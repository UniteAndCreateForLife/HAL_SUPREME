"""Beat-synced camera and glitch effects for the SIGNAL SPLIT music video, driven by the song's own drum hits.

Usage: python tools/beat_fx.py <in.mp4> <edl.json> <drums.wav> <out.mp4>

Kick and snare hits are picked from the drum stem (onset strength in 35-110 Hz and 1.5-6 kHz), not from a guessed grid.
  - choruses: a zoom punch on every kick (7%, decaying over 0.22 s) with a small exposure lift; a shake and a pink/cyan
    split on every snare
  - verses: a lighter zoom punch (3%) on the kicks that fall on bar lines
  - every section change: a 6-frame glitch transition (sliced rows, a wide colour split, a flash)
  - B-roll cuts get a slow push-in across the cut; performance cuts get a gentle handheld drift
  - every cut's exposure is pulled halfway toward the median of all cuts first (shot matching)
The typography is overlaid after this pass, so the text never shakes."""
from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

W, H, FPS = 1920, 1080, 24


def hits(drums: Path, lo: float, hi: float, threshold: float) -> np.ndarray:
    import librosa

    y, sr = librosa.load(str(drums), sr=22050, mono=True)
    spec = np.abs(librosa.stft(y, n_fft=2048, hop_length=256))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    env = np.maximum(0, np.diff(spec[(freqs > lo) & (freqs < hi)], axis=1)).sum(axis=0)
    env = env / (np.percentile(env, 99.5) or 1.0)
    peaks = librosa.util.peak_pick(env, pre_max=6, post_max=6, pre_avg=20, post_avg=20, delta=threshold, wait=12)
    return peaks * 256 / sr


def section_at(sections: list, t: float) -> str:
    for label, start, end in sections:
        if start <= t < end:
            return label
    return sections[-1][0]


def plan(edl: dict, drums: Path) -> dict:
    from build_signal_split_edl import bar_lines, merge_sections, snap_sections

    duration = edl["duration_s"]
    merged = merge_sections(edl["sections"])
    bars = bar_lines(edl["beat_grid"], duration, [start for _, start, _ in merged[1:]])
    sections = snap_sections(merged, bars, duration)
    kicks, snares = hits(drums, 35, 110, 0.15), hits(drums, 1500, 6000, 0.15)
    punches, shakes = [], []
    for t in kicks:
        label = section_at(sections, t)
        if label == "chorus":
            punches.append((float(t), 0.07))
        elif label == "verse" and min(abs(t - b) for b in bars) < 0.06:
            punches.append((float(t), 0.03))
    for t in snares:
        if section_at(sections, t) == "chorus":
            shakes.append(float(t))
    changes = [start for _, start, _ in sections[1:]]
    return {"punches": punches, "shakes": shakes, "changes": changes, "cuts": edl["cuts"]}


def exposure_gains(video: Path, cuts: list[dict], pull: float = 0.5) -> dict[str, float]:
    """Pull each cut's mean brightness halfway toward the median of all cuts, so the video does not jump from a near
    black shot to a bright one; the gain is clamped (0.8-1.6) so dark moods stay dark."""
    means = {}
    for cut in cuts:
        values = []
        for share in (0.25, 0.5, 0.75):
            t = cut["start_s"] + (cut["end_s"] - cut["start_s"]) * share
            raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(video), "-frames:v", "1",
                                  "-vf", "scale=192:108,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
            values.append(np.frombuffer(raw, np.uint8).astype(float).mean())
        means[cut["id"]] = float(np.mean(values))
    median = float(np.median(list(means.values())))
    return {key: float(np.clip((median + (mean - median) * pull) / max(mean, 1.0), 0.8, 1.6)) for key, mean in means.items()}


def envelope(t: float, events: list[float], decay: float) -> float:
    value = 0.0
    for e in events:
        if 0 <= t - e < decay * 4:
            value = max(value, math.exp(-(t - e) / decay))
    return value


def render(video: Path, fx: dict, out: Path) -> dict:
    import cv2

    rng = np.random.default_rng(26)
    if "gains" not in fx:
        fx["gains"] = exposure_gains(video, fx["cuts"])
    decoder = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(video), "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                               stdout=subprocess.PIPE)
    encoder = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                                "-r", str(FPS), "-i", "-", "-i", str(video), "-map", "0:v", "-map", "1:a", "-c:v", "libx264",
                                "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "copy", str(out)],
                               stdin=subprocess.PIPE)
    punch_times = [p for p, _ in fx["punches"]]
    punch_size = dict(fx["punches"])
    frame_bytes = W * H * 3
    count, stats = 0, {"punch_frames": 0, "shake_frames": 0, "glitch_frames": 0}
    while True:
        raw = decoder.stdout.read(frame_bytes)
        if len(raw) < frame_bytes:
            break
        frame = np.frombuffer(raw, np.uint8).reshape(H, W, 3)
        t = count / FPS
        cut = next((c for c in fx["cuts"] if c["start_s"] <= t < c["end_s"]), fx["cuts"][-1])
        gain = fx.get("gains", {}).get(cut["id"], 1.0)
        if abs(gain - 1.0) > 0.02:
            frame = cv2.convertScaleAbs(frame, alpha=gain)
        progress = (t - cut["start_s"]) / max(0.01, cut["end_s"] - cut["start_s"])
        zoom, dx, dy, angle = 1.0, 0.0, 0.0, 0.0
        if cut.get("performance"):  # handheld drift
            dx, dy = 5 * math.sin(t * 1.3 + 0.7), 4 * math.sin(t * 1.7)
            angle = 0.25 * math.sin(t * 0.9)
            zoom = 1.02
        else:  # slow push-in across the cut
            zoom = 1.0 + 0.045 * progress
        recent = [p for p in punch_times if 0 <= t - p < 0.9]
        if recent:
            last = max(recent)
            amount = punch_size[last] * math.exp(-(t - last) / 0.22)
            zoom += amount
            if amount > 0.005:
                stats["punch_frames"] += 1
        shake = envelope(t, fx["shakes"], 0.10)
        if shake > 0.05:
            dx += rng.uniform(-14, 14) * shake
            dy += rng.uniform(-10, 10) * shake
            stats["shake_frames"] += 1
        matrix = cv2.getRotationMatrix2D((W / 2, H / 2), angle, zoom)
        matrix[:, 2] += (dx, dy)
        frame = cv2.warpAffine(frame, matrix, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        flash = 0.10 * envelope(t, punch_times, 0.08) if section_at_cut(cut) == "chorus" else 0.0
        split = int(round(9 * shake))
        glitch = max((1 - abs(t - c) / 0.13 for c in fx["changes"] if abs(t - c) < 0.13), default=0.0)
        if glitch > 0:
            split = max(split, int(28 * glitch))
            flash = max(flash, 0.35 * glitch)
            stats["glitch_frames"] += 1
        if split:
            b, g, r = frame[..., 0], frame[..., 1], frame[..., 2]
            frame = np.dstack([np.roll(b, split, axis=1), g, np.roll(r, -split, axis=1)])
        if glitch > 0.3:
            frame = frame.copy()
            for _ in range(int(14 * glitch)):
                top, height = int(rng.integers(0, H - 40)), int(rng.integers(8, 60))
                frame[top:top + height] = np.roll(frame[top:top + height], int(rng.integers(-160, 160)), axis=1)
        if flash > 0.01:
            frame = cv2.convertScaleAbs(frame, alpha=1.0 + flash, beta=255 * flash * 0.25)
        encoder.stdin.write(np.ascontiguousarray(frame).tobytes())
        count += 1
    encoder.stdin.close()
    encoder.wait()
    decoder.wait()
    return {"frames": count, **stats, "punches": len(fx["punches"]), "shakes": len(fx["shakes"]),
            "section_changes": len(fx["changes"]), "exposure_gains": {k: round(v, 2) for k, v in fx["gains"].items()}}


def section_at_cut(cut: dict) -> str:
    return cut.get("section", "")


if __name__ == "__main__":
    video, edl_path, drums, out = (Path(a) for a in sys.argv[1:5])
    edl = json.loads(edl_path.read_text(encoding="utf-8"))
    fx = plan(edl, drums)
    report = render(video, fx, out)
    out.with_suffix(".fx.json").write_text(json.dumps({**report, "punch_times": fx["punches"], "shake_times": fx["shakes"],
                                                       "section_changes": fx["changes"]}, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=1))
