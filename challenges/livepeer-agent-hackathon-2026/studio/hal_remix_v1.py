#!/usr/bin/env python3
"""HAL Remix v1: keep the owner's performed vocal, give it a new HAL-made beat, and document who did what.

The owner freestyled the vocal on DARK SIGNAL over a beat whose engine nobody recorded. A remix makes the process
fully known: the owner's own voice, a new instrumental from a named model with published training-data claims, and
a receipt that lists every tool.

Stages:
  split   song -> the vocal stem and the original instrumental (Demucs, via hal_voice_clone_pipeline.separate), each
          analysed for tempo and key
  brief   the analysis -> beat prompts in original words (no artist names) for a text-to-music model
  fit     a generated beat -> matched to the vocal: tempo ratio (half/double-time aware) and key shift with ffmpeg's
          rubberband filter, then aligned to the vocal's phrasing by cross-correlating onset envelopes against the
          original instrumental
  mix     vocal + fitted beat -> vocal clean-up (high-pass, de-ess, gentle compression), the beat ducked under the
          vocal with a sidechain compressor, two-pass loudness master (-14 LUFS, -1 dBTP), and a 44.1 kHz / 16-bit
          WAV plus a 320 kbps MP3 for upload
Every stage writes into data/remix/<id>/ and appends to receipt.json. Generation itself happens upstream (Sonilo v1.1
through Livepeer credits); nothing here spends, uploads or publishes.

Usage:
  python scripts/hal_remix_v1.py split --id dark_signal --song <file>
  python scripts/hal_remix_v1.py brief --id dark_signal
  python scripts/hal_remix_v1.py fit --id dark_signal --beat <take.wav> --name take1
  python scripts/hal_remix_v1.py mix --id dark_signal --name take1
"""

from __future__ import annotations

import argparse
import os
import hashlib
import json
import math
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(os.environ.get("HAL_ROOT", Path(__file__).resolve().parents[1]))  # the private tree sets HAL_ROOT
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from hal_our_version_v1 import NOTES, analyze_audio, banned_names, refuse_names  # noqa: E402

STATE = ROOT / "data" / "remix"
SR = 22050
HOP = 512


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def run(args: list[str]) -> None:
    proc = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    if proc.returncode != 0:
        raise RuntimeError(f"{args[0]} failed: {proc.stderr[-800:]}")


# ---------------------------------------------------------------- pure functions

def grid_from_beats(beat_times: np.ndarray) -> tuple[float, float, float] | None:
    """(period, phase, residual RMS) of a least-squares line through every beat: far finer than a tempo histogram bin.

    Beats are numbered by rounding their distance from the first beat in median periods, so a skipped or doubled
    beat does not bend the line. The residual says how steady the tempo is: a generated beat can wander."""
    times = np.asarray(beat_times, dtype=float)
    if len(times) < 8:
        return None
    median = float(np.median(np.diff(times)))
    if median <= 0:
        return None
    index = np.round((times - times[0]) / median)
    keep = np.abs((times - times[0]) - index * median) < 0.25 * median
    if keep.sum() < 8:
        return None
    slope, intercept = np.polyfit(index[keep], times[keep], 1)
    residual = times[keep] - (slope * index[keep] + intercept)
    return float(slope), float(intercept), float(np.sqrt(np.mean(np.square(residual))))


def period_from_beats(beat_times: np.ndarray) -> float | None:
    grid = grid_from_beats(beat_times)
    return grid[0] if grid else None


def track_beats(path: Path, hop: int = 128, tightness: tuple[int, ...] = (100, 400, 1600)) -> dict[str, Any] | None:
    """Beats of a track with the tracker setting that best explains them.

    librosa's default tracker can misread a steady song's tempo by a fraction of a percent, enough to walk a beat
    180 ms off a vocal over four minutes. Each setting's beats get a straight grid; the setting whose beats sit closest
    to their own grid (strong-beat window spread plus jitter) wins."""
    import librosa  # noqa: PLC0415

    y, sr = librosa.load(str(path), sr=SR, mono=True)
    envelope = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    coarse = float(np.atleast_1d(librosa.feature.tempo(onset_envelope=envelope, sr=sr, hop_length=hop))[0])
    best = None
    for tight in tightness:
        _, frames = librosa.beat.beat_track(onset_envelope=envelope, sr=sr, hop_length=hop, start_bpm=coarse, tightness=tight)
        frames = np.asarray(frames, dtype=int)
        times = librosa.frames_to_time(frames, sr=sr, hop_length=hop)
        grid = grid_from_beats(times)
        if not grid:
            continue
        strengths = envelope[np.clip(frames, 0, len(envelope) - 1)]
        own = window_offsets(times, strengths, grid[0], grid[1])
        score = (own["spread_ms"] + own["jitter_ms"]) if own["spread_ms"] is not None else float("inf")
        if best is None or score < best["score"]:
            best = {"times": times, "strengths": strengths, "grid": grid, "tightness": tight, "score": score,
                    "own": own, "duration_s": len(y) / sr}
    return best


def beat_grid(path: Path, hop: int = 128) -> dict[str, float] | None:
    tracked = track_beats(path, hop)
    if not tracked:
        return None
    period, phase, residual = tracked["grid"]
    return {"bpm": round(60.0 / period, 4), "period_s": period, "phase_s": phase, "steadiness_ms": round(residual * 1000, 1),
            "beats": int(len(tracked["times"])), "duration_s": round(tracked["duration_s"], 3),
            "tightness": tracked["tightness"], "self_spread_ms": tracked["own"]["spread_ms"],
            "self_jitter_ms": tracked["own"]["jitter_ms"]}


def window_offsets(beats: np.ndarray, strengths: np.ndarray, ref_period: float, ref_phase: float,
                   window_s: float = 30.0, min_beats: int = 16, strength_quantile: float = 0.4) -> dict[str, Any]:
    """How far the beat sits from the vocal's grid, window by window, using only beats where drums are playing.

    Each strong beat is measured against the nearest half-beat of the reference grid (a tracker may lock onto
    off-beats). A window's offset is the median of its beats; jitter is the worst window's median absolute deviation.
    Breakdowns without drums are left out instead of failing a steady beat."""
    beats, strengths = np.asarray(beats, dtype=float), np.asarray(strengths, dtype=float)
    if len(beats) < min_beats:
        return {"offsets_ms": [], "spread_ms": None, "worst_ms": None, "jitter_ms": None}
    keep = strengths >= np.quantile(strengths, strength_quantile)
    times = beats[keep]
    half = ref_period / 2
    position = (times - ref_phase) / half
    offset = (position - np.round(position)) * half
    offsets, jitters = [], []
    for start in np.arange(0.0, float(times.max()) + 1e-9, window_s):
        inside = (times >= start) & (times < start + window_s)
        if inside.sum() >= min_beats:
            median = float(np.median(offset[inside]))
            offsets.append(median)
            jitters.append(float(np.median(np.abs(offset[inside] - median))))
    if not offsets:
        return {"offsets_ms": [], "spread_ms": None, "worst_ms": None, "jitter_ms": None}
    return {"offsets_ms": [round(o * 1000, 1) for o in offsets],
            "spread_ms": round((max(offsets) - min(offsets)) * 1000, 1),
            "worst_ms": round(max(abs(o) for o in offsets) * 1000, 1),
            "jitter_ms": round(max(jitters) * 1000, 1)}  # the sloppiest window: a sloppy section is audible on its own


def timing_ok(report: dict[str, Any], limit_ms: float = 40.0, jitter_limit_ms: float = 20.0) -> bool:
    return (len(report.get("offsets_ms") or []) >= 2 and report["spread_ms"] <= limit_ms
            and report["worst_ms"] <= limit_ms and report["jitter_ms"] <= jitter_limit_ms)


def beats_with_strength(path: Path, hop: int = 128) -> tuple[np.ndarray, np.ndarray]:
    tracked = track_beats(path, hop)
    if not tracked:
        return np.array([]), np.array([])
    return tracked["times"], tracked["strengths"]


def normalized_period_ratio(period: float, reference: float) -> float:
    """period / reference folded to the nearest of half, same or double time."""
    return min((period / reference * m for m in (0.5, 1.0, 2.0)), key=lambda r: abs(math.log(r)))


def tempo_drift_ms(period: float, reference: float, duration_s: float) -> float:
    """How far a steady beat at `period` walks away from the `reference` grid over the song."""
    return abs(normalized_period_ratio(period, reference) - 1.0) * duration_s * 1000.0


def bar_offset_candidates(reference_phase: float, candidate_phase: float, period: float, bars: int = 2) -> list[float]:
    """Delays that put the candidate's beats on the reference's, one per whole-beat shift (a bar is four beats)."""
    base = (reference_phase - candidate_phase) % period
    if base > period / 2:
        base -= period
    return [round(base + k * period, 6) for k in range(-4 * bars // 2, 4 * bars // 2 + 1)]


def parse_key(key: str) -> tuple[int, str]:
    tonic, mode = key.split()
    return NOTES.index(tonic), mode


def semitone_shift(beat_key: str, vocal_key: str) -> int:
    """Smallest shift (-6..+5) that puts the beat in the vocal's key; a major/minor mismatch aims at the relative key."""
    beat_tonic, beat_mode = parse_key(beat_key)
    vocal_tonic, vocal_mode = parse_key(vocal_key)
    if beat_mode != vocal_mode:  # A minor and C major share their notes: aim at the vocal key's relative
        vocal_tonic = (vocal_tonic + 3) % 12 if vocal_mode == "minor" else (vocal_tonic - 3) % 12
    shift = (vocal_tonic - beat_tonic) % 12
    return shift - 12 if shift > 5 else shift


def best_offset(reference: np.ndarray, candidate: np.ndarray, max_lag: int) -> int:
    """Lag in frames (candidate delayed by +lag) that best lines the candidate's onsets up with the reference's."""
    ref = (reference - reference.mean()) / (reference.std() or 1.0)
    cand = (candidate - candidate.mean()) / (candidate.std() or 1.0)
    best, best_score = 0, -np.inf
    for lag in range(-max_lag, max_lag + 1):
        if lag >= 0:
            a, b = ref[lag:], cand[: len(cand) - lag] if lag else cand
        else:
            a, b = ref[: len(ref) + lag], cand[-lag:]
        n = min(len(a), len(b))
        if n < 16:
            continue
        score = float(np.dot(a[:n], b[:n]) / n)
        if score > best_score:
            best, best_score = lag, score
    return best


def beat_prompt(analysis: dict[str, Any], style_words: list[str], variant: str) -> str:
    """A beat description in original words: the vocal's tempo and key, the owner's style, one variation."""
    words = ", ".join(style_words)
    return (f"instrumental only, no vocals, {words}, {variant}, "
            f"{round(float(analysis['tempo_bpm']))} BPM, {analysis['key']['key']}, "
            "leaves space in the mid-range for a lead vocal, mixed for headphones")


def balance_beat_db(vocal_lufs: float | None, beat_lufs: float | None, vocal_lead_lu: float = 4.0) -> float:
    """Beat gain that sits the beat `vocal_lead_lu` below the vocal (vocal-forward, as rap and pop mixes are)."""
    if vocal_lufs is None or beat_lufs is None or not math.isfinite(vocal_lufs) or not math.isfinite(beat_lufs):
        return -3.0
    return round(min(6.0, max(-18.0, (vocal_lufs - vocal_lead_lu) - beat_lufs)), 2)


def measure_lufs(path: Path) -> float | None:
    try:
        import pyloudnorm  # noqa: PLC0415
        import soundfile  # noqa: PLC0415

        data, rate = soundfile.read(str(path))
        value = float(pyloudnorm.Meter(rate).integrated_loudness(data))
        return value if math.isfinite(value) else None
    except Exception:  # noqa: BLE001 - an unmeasurable file falls back to a fixed balance
        return None


def mix_filter(vocal_gain_db: float = 0.0, beat_gain_db: float = -3.0) -> str:
    """Vocal clean-up and a beat that ducks a few dB under it; inputs: [0] vocal, [1] beat."""
    return (f"[0:a]highpass=f=90,deesser=i=0.4,acompressor=threshold=-18dB:ratio=3:attack=8:release=120,"
            f"volume={vocal_gain_db}dB,asplit=2[vox][key];"
            f"[1:a]volume={beat_gain_db}dB[beat];"
            "[beat][key]sidechaincompress=threshold=0.08:ratio=3:attack=15:release=250[ducked];"
            "[vox][ducked]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[out]")


# ---------------------------------------------------------------- receipt

def receipt_path(song_id: str) -> Path:
    return STATE / song_id / "receipt.json"


def update_receipt(song_id: str, key: str, value: Any) -> None:
    path = receipt_path(song_id)
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {
        "schema": "hal.remix.receipt.v1", "song_id": song_id, "created_at_utc": utc_now()}
    data[key] = value
    data["updated_at_utc"] = utc_now()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- stages

def cmd_split(args: argparse.Namespace) -> int:
    from hal_voice_clone_pipeline import separate  # noqa: PLC0415

    folder = STATE / args.id
    folder.mkdir(parents=True, exist_ok=True)
    source = folder / f"source_original{Path(args.song).suffix.lower()}"  # kept as received; source.wav is the working copy
    if Path(args.song).resolve() != source.resolve():
        shutil.copyfile(args.song, source)
    wav = folder / "source.wav"
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(source), "-vn", "-ac", "2", "-ar", "44100", str(wav)])
    vocals = Path(separate(wav))
    shutil.copyfile(vocals, folder / "vocals.wav")
    no_vocals = vocals.with_name("no_vocals.wav")
    shutil.copyfile(no_vocals, folder / "original_instrumental.wav")
    analysis = {"source": analyze_audio(wav), "instrumental": analyze_audio(folder / "original_instrumental.wav")}
    (folder / "analysis.json").write_text(json.dumps(analysis, indent=2) + "\n", encoding="utf-8")
    update_receipt(args.id, "split", {"source": str(args.song), "source_sha256": sha256(source),
                                      "separation": "Demucs htdemucs, two stems (https://github.com/facebookresearch/demucs)",
                                      "vocals_sha256": sha256(folder / "vocals.wav"),
                                      "tempo_bpm": analysis["instrumental"]["tempo_bpm"],
                                      "key": analysis["instrumental"]["key"]["key"],
                                      "duration_s": analysis["source"]["duration_s"]})
    print(json.dumps({k: analysis["instrumental"][k] for k in ("tempo_bpm", "key", "duration_s")}))
    return 0


def cmd_brief(args: argparse.Namespace) -> int:
    analysis = json.loads((STATE / args.id / "analysis.json").read_text(encoding="utf-8"))["instrumental"]
    style = [word.strip() for word in args.style.split(",") if word.strip()]
    variants = ["heavy half-time drums and a sub bass that breathes", "glitchy broken percussion and detuned pads",
                "slow build into a heavy drop, eerie bell motif", "dark trance lift with wide supersaws"]
    prompts = []
    for variant in variants[: args.takes]:
        prompt = beat_prompt(analysis, style, variant)
        refuse_names(prompt, banned_names())
        prompts.append(prompt)
    duration = int(math.ceil(float(analysis["duration_s"]) + 4))
    update_receipt(args.id, "brief", {"prompts": prompts, "duration_s": duration, "style_words": style})
    print(json.dumps({"duration_s": duration, "prompts": prompts}, indent=2))
    return 0


def onset_envelope(path: Path, hop: int = HOP) -> np.ndarray:
    import librosa  # noqa: PLC0415

    y, _ = librosa.load(str(path), sr=SR, mono=True)
    return librosa.onset.onset_strength(y=y, sr=SR, hop_length=hop)


def low_band_envelope(path: Path, hop: int = HOP) -> np.ndarray:
    """Onsets below 150 Hz: kick and bass, the parts that mark where a bar starts."""
    import librosa  # noqa: PLC0415
    from scipy.signal import butter, sosfilt  # noqa: PLC0415

    y, _ = librosa.load(str(path), sr=SR, mono=True)
    low = sosfilt(butter(4, 150, btype="lowpass", fs=SR, output="sos"), y)
    return librosa.onset.onset_strength(y=low, sr=SR, hop_length=hop)


def correlation_at(reference: np.ndarray, candidate: np.ndarray, lag: int) -> float:
    """Normalized correlation with the candidate delayed by `lag` frames."""
    ref = (reference - reference.mean()) / (reference.std() or 1.0)
    cand = (candidate - candidate.mean()) / (candidate.std() or 1.0)
    a, b = (ref[lag:], cand) if lag >= 0 else (ref, cand[-lag:])
    n = min(len(a), len(b))
    return float(np.dot(a[:n], b[:n]) / n) if n > 16 else float("-inf")


def vocal_key(path: Path, min_pitched_share: float = 0.2) -> dict[str, Any] | None:
    """The key the performed vocal actually sits in, from pYIN pitch classes of its pitched frames.

    None when too little of the vocal is pitched (pure rap or speech): then the key comes from the instrumental."""
    import librosa  # noqa: PLC0415

    from hal_our_version_v1 import estimate_key  # noqa: PLC0415

    y, sr = librosa.load(str(path), sr=16000, mono=True)
    f0, voiced, prob = librosa.pyin(y, fmin=70, fmax=700, sr=sr, frame_length=1024, hop_length=256)
    rms = librosa.feature.rms(y=y, frame_length=1024, hop_length=256)[0]
    n = min(len(rms), len(voiced))
    active = rms[:n] > np.percentile(rms[:n], 40)
    pitched = voiced[:n] & active & (prob[:n] > 0.5)
    share = float(pitched.sum() / max(1, active.sum()))
    if share < min_pitched_share:
        return None
    classes = np.zeros(12)
    for midi in librosa.hz_to_midi(f0[:n][pitched]):
        classes[int(round(midi)) % 12] += 1
    key = estimate_key(classes / classes.sum())
    return {**key, "pitched_share": round(share, 3)}


def stretch(source: Path, destination: Path, tempo: float, semitones: int = 0) -> None:
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(source), "-af",
         f"rubberband=tempo={tempo:.6f}:pitch={2 ** (semitones / 12):.6f}:pitchq=quality", "-ar", "44100", "-ac", "2",
         str(destination)])


def cmd_fit(args: argparse.Namespace) -> int:
    folder = STATE / args.id
    analysis = json.loads((folder / "analysis.json").read_text(encoding="utf-8"))["instrumental"]
    duration = float(analysis["duration_s"])
    reference = beat_grid(folder / "original_instrumental.wav")  # the grid the vocal was performed on
    raw = beat_grid(Path(args.beat))
    if not reference or not raw:
        raise RuntimeError("no steady beat found in the reference or the take")
    beat_key = analyze_audio(Path(args.beat))["key"]["key"]
    all_analysis = json.loads((folder / "analysis.json").read_text(encoding="utf-8"))
    if "vocal_key" not in all_analysis:  # measured once: the key the performance sits in
        all_analysis["vocal_key"] = vocal_key(folder / "vocals.wav")
        (folder / "analysis.json").write_text(json.dumps(all_analysis, indent=2) + "\n", encoding="utf-8")
    target_key = (all_analysis["vocal_key"] or {}).get("key") or analysis["key"]["key"]
    shift = semitone_shift(beat_key, target_key)
    ratio = normalized_period_ratio(raw["period_s"], reference["period_s"])
    stretched = folder / f"{args.name}_stretched.wav"
    stretch(Path(args.beat), stretched, ratio, shift)
    measured = beat_grid(stretched)
    corrections = 0
    if measured and tempo_drift_ms(measured["period_s"], reference["period_s"], duration) > 20.0:
        corrected = folder / f"{args.name}_stretched2.wav"  # one corrective pass on the residual tempo error
        stretch(stretched, corrected, normalized_period_ratio(measured["period_s"], reference["period_s"]))
        corrected.replace(stretched)
        measured, corrections = beat_grid(stretched), 1
    if not measured:
        raise RuntimeError("the stretched take has no steady beat")
    hop_s = HOP / SR
    ref_low, cand_low = low_band_envelope(folder / "original_instrumental.wav"), low_band_envelope(stretched)
    half = reference["period_s"] / 2
    candidates = [c for c in bar_offset_candidates(reference["phase_s"], measured["phase_s"], half, bars=2)]
    scored = sorted(((correlation_at(ref_low, cand_low, int(round(d / hop_s))), d) for d in candidates), reverse=True)
    best_corr, offset_s = scored[0]
    fitted = folder / f"{args.name}_fitted.wav"
    if offset_s >= 0:
        shape = f"adelay={int(round(offset_s * 1000))}|{int(round(offset_s * 1000))},apad,atrim=0:{duration:.3f}"
    else:
        shape = f"atrim=start={-offset_s:.3f},asetpts=PTS-STARTPTS,apad,atrim=0:{duration:.3f}"
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(stretched), "-af",
         shape + ",afade=t=out:st=" + f"{max(0.0, duration - 3):.3f}:d=3", str(fitted)])
    final = beat_grid(fitted) or measured
    drift = round(tempo_drift_ms(final["period_s"], reference["period_s"], duration), 1)
    phase_gap = (final["phase_s"] - reference["phase_s"]) % half
    phase_error = round(min(phase_gap, half - phase_gap) * 1000, 1)
    fit = {"beat": str(args.beat), "beat_sha256": sha256(Path(args.beat)), "beat_bpm": raw["bpm"],
           "vocal_grid_bpm": reference["bpm"], "fitted_bpm": final["bpm"], "beat_key": beat_key, "target_key": target_key,
           "tempo_ratio": round(ratio, 6), "corrective_passes": corrections, "semitone_shift": shift,
           "offset_s": round(offset_s, 3), "low_band_correlation": round(best_corr, 3), "drift_ms": drift,
           "phase_error_ms": phase_error, "steadiness_ms": final["steadiness_ms"],
           "fitted": fitted.name, "tool": "ffmpeg rubberband filter (Rubber Band Library)"}
    fit.update(timing_check(fitted, reference))
    receipt = json.loads(receipt_path(args.id).read_text(encoding="utf-8"))
    fits = receipt.get("fits", {})
    fits[args.name] = fit
    update_receipt(args.id, "fits", fits)
    print(json.dumps(fit, indent=2))
    return 0


def timing_check(fitted: Path, reference: dict[str, Any]) -> dict[str, Any]:
    """The in-time gate: strong beats of the fitted beat stay within 40 ms of the vocal's grid in every window."""
    beats, strengths = beats_with_strength(fitted)
    timing = window_offsets(beats, strengths, reference["period_s"], reference["phase_s"])
    return {"timing": timing, "in_time": timing_ok(timing), "timing_method": "strong-beat window offsets v2"}


def cmd_qc(args: argparse.Namespace) -> int:
    """Re-run the timing gate on an existing fitted beat, without re-rendering anything."""
    folder = STATE / args.id
    reference = beat_grid(folder / "original_instrumental.wav")
    receipt = json.loads(receipt_path(args.id).read_text(encoding="utf-8"))
    fits = receipt.get("fits", {})
    fit = fits.get(args.name, {})
    fit.update(timing_check(folder / f"{args.name}_fitted.wav", reference))
    fits[args.name] = fit
    update_receipt(args.id, "fits", fits)
    print(json.dumps(fit, indent=2))
    return 0


def mute_spans(times: list[tuple[float, float]], pad: float = 0.06) -> str:
    """ffmpeg volume filter that silences each span (with a little padding) and nothing else."""
    parts = [f"volume=enable='between(t,{max(0.0, a - pad):.3f},{b + pad:.3f})':volume=0" for a, b in sorted(times)]
    return ",".join(parts) if parts else "anull"


def cmd_clean(args: argparse.Namespace) -> int:
    """A radio edit of the vocal: the listed words are found by Whisper word timestamps and muted."""
    from hal_lyric_timeline_v1 import transcribe_words  # noqa: PLC0415

    folder = STATE / args.id
    targets = {word.strip().lower() for word in args.words.split(",") if word.strip()}
    words = transcribe_words(folder / "vocals.wav")
    spans = [(start, end) for word, start, end in words if word in targets]
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(folder / "vocals.wav"), "-af",
         mute_spans(spans), str(folder / "vocals_clean.wav")])
    update_receipt(args.id, "clean_edit", {"muted_words": sorted(targets), "spans_s": [[round(a, 2), round(b, 2)] for a, b in spans],
                                           "method": "Whisper base.en word timestamps on the vocal stem; ffmpeg volume mute, 60 ms padding"})
    print(json.dumps({"muted": [[round(a, 2), round(b, 2)] for a, b in spans]}))
    return 0


def cmd_mix(args: argparse.Namespace) -> int:
    from hal_music_quality_gate import master_audio  # noqa: PLC0415

    folder = STATE / args.id
    vocals = folder / ("vocals_clean.wav" if args.clean else "vocals.wav")
    vocal_lufs, beat_lufs = measure_lufs(vocals), measure_lufs(folder / f"{args.name}_fitted.wav")
    if args.beat_db is None:
        args.beat_db = balance_beat_db(vocal_lufs, beat_lufs, args.vocal_lead)
    out = args.name + ("_clean" if args.clean else "")  # a radio edit never overwrites the original mix
    premaster = folder / f"{out}_premaster.wav"
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(vocals),
         "-i", str(folder / f"{args.name}_fitted.wav"), "-filter_complex",
         mix_filter(args.vocal_db, args.beat_db), "-map", "[out]", "-ar", "44100", str(premaster)])
    mastered48 = folder / f"{out}_master48k.wav"
    mastering = master_audio(premaster, mastered48)
    final_wav = folder / f"{out}_final_44k16.wav"
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(mastered48), "-ar", "44100",
         "-sample_fmt", "s16", str(final_wav)])
    final_mp3 = folder / f"{out}_final_320k.mp3"
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(final_wav), "-codec:a", "libmp3lame",
         "-b:a", "320k", "-ar", "44100", str(final_mp3)])
    receipt = json.loads(receipt_path(args.id).read_text(encoding="utf-8"))
    mixes = receipt.get("mixes", {})
    mixes[out] = {"vocals": vocals.name, "vocal_lufs": vocal_lufs, "beat_lufs": beat_lufs, "vocal_lead_lu": args.vocal_lead,
                        "vocal_db": args.vocal_db, "beat_db": args.beat_db, "mix_filter": mix_filter(args.vocal_db, args.beat_db),
                        "mastering": mastering, "final_wav": final_wav.name, "final_wav_sha256": sha256(final_wav),
                        "final_mp3": final_mp3.name, "final_mp3_bytes": final_mp3.stat().st_size}
    update_receipt(args.id, "mixes", mixes)
    print(json.dumps({"final_mp3": str(final_mp3), "bytes": final_mp3.stat().st_size,
                      "output_lufs": mastering["measurement"].get("output_i")}, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("split")
    p.add_argument("--id", required=True)
    p.add_argument("--song", required=True)
    p = sub.add_parser("brief")
    p.add_argument("--id", required=True)
    p.add_argument("--style", default="dark bass music, dubstep weight, darkwave synths, eerie and hypnotic")
    p.add_argument("--takes", type=int, default=4)
    p = sub.add_parser("fit")
    p.add_argument("--id", required=True)
    p.add_argument("--beat", required=True)
    p.add_argument("--name", required=True)
    p = sub.add_parser("mix")
    p.add_argument("--id", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--vocal-db", type=float, default=0.0)
    p.add_argument("--beat-db", type=float, default=None, help="default: measured, the beat sits --vocal-lead LU under the vocal")
    p.add_argument("--vocal-lead", type=float, default=4.0)
    p.add_argument("--clean", action="store_true", help="use the radio-edit vocal from the clean stage")
    p = sub.add_parser("qc")
    p.add_argument("--id", required=True)
    p.add_argument("--name", required=True)
    p = sub.add_parser("clean")
    p.add_argument("--id", required=True)
    p.add_argument("--words", required=True, help="comma-separated words to mute")
    args = parser.parse_args(argv)
    return {"split": cmd_split, "brief": cmd_brief, "fit": cmd_fit, "mix": cmd_mix, "clean": cmd_clean, "qc": cmd_qc}[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
