from __future__ import annotations

import json
import re
import subprocess
from fractions import Fraction
from pathlib import Path
from typing import Any


class VideoQualityError(RuntimeError):
    pass


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def _fraction(value: str | None) -> float:
    if not value or value in {"0/0", "N/A"}:
        return 0.0
    try:
        return float(Fraction(value))
    except (ValueError, ZeroDivisionError):
        return 0.0


def probe_video(video: Path) -> dict[str, Any]:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries",
        "format=duration:stream=index,codec_type,codec_name,width,height,avg_frame_rate,r_frame_rate,channels,sample_rate",
        "-of", "json", str(video),
    ]
    proc = _run(cmd)
    if proc.returncode != 0:
        raise VideoQualityError(proc.stderr.strip() or "ffprobe failed")
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise VideoQualityError("ffprobe returned invalid JSON") from exc

    streams = payload.get("streams") or []
    video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    if not video_stream:
        raise VideoQualityError("artifact has no video stream")
    audio_streams = [s for s in streams if s.get("codec_type") == "audio"]

    try:
        duration_s = float((payload.get("format") or {}).get("duration") or 0.0)
    except (TypeError, ValueError):
        duration_s = 0.0

    fps = _fraction(video_stream.get("avg_frame_rate")) or _fraction(video_stream.get("r_frame_rate"))
    return {
        "duration_s": duration_s,
        "width": int(video_stream.get("width") or 0),
        "height": int(video_stream.get("height") or 0),
        "fps": fps,
        "video_codec": video_stream.get("codec_name"),
        "audio_streams": len(audio_streams),
        "audio_codecs": [s.get("codec_name") for s in audio_streams],
    }


def _extract_durations(stderr: str, key: str) -> list[float]:
    pattern = re.compile(rf"{re.escape(key)}\s*[:=]\s*([0-9]+(?:\.[0-9]+)?)")
    return [float(m.group(1)) for m in pattern.finditer(stderr)]


def detect_freezes(video: Path, *, minimum_s: float = 1.5, noise_db: float = -55.0) -> dict[str, Any]:
    proc = _run([
        "ffmpeg", "-hide_banner", "-nostats", "-v", "info", "-i", str(video),
        "-vf", f"freezedetect=n={noise_db}dB:d={minimum_s}", "-an", "-f", "null", "-",
    ])
    if proc.returncode != 0:
        raise VideoQualityError(proc.stderr.strip() or "ffmpeg freezedetect failed")
    durations = _extract_durations(proc.stderr, "freeze_duration")
    return {
        "threshold_s": minimum_s,
        "events": len(durations),
        "durations_s": durations,
        "max_duration_s": max(durations, default=0.0),
    }


def detect_black(video: Path, *, minimum_s: float = 0.5, pixel_threshold: float = 0.10) -> dict[str, Any]:
    proc = _run([
        "ffmpeg", "-hide_banner", "-nostats", "-v", "info", "-i", str(video),
        "-vf", f"blackdetect=d={minimum_s}:pix_th={pixel_threshold}", "-an", "-f", "null", "-",
    ])
    if proc.returncode != 0:
        raise VideoQualityError(proc.stderr.strip() or "ffmpeg blackdetect failed")
    durations = _extract_durations(proc.stderr, "black_duration")
    return {
        "threshold_s": minimum_s,
        "events": len(durations),
        "durations_s": durations,
        "max_duration_s": max(durations, default=0.0),
    }


def evaluate_video_evidence(
    probe: dict[str, Any],
    *,
    expected_duration_s: float | None = None,
    duration_tolerance_s: float = 0.75,
    minimum_width: int | None = None,
    minimum_height: int | None = None,
    minimum_fps: float | None = None,
    require_audio: bool = False,
    freeze: dict[str, Any] | None = None,
    max_freeze_s: float | None = None,
    black: dict[str, Any] | None = None,
    max_black_s: float | None = None,
) -> dict[str, Any]:
    failures: list[str] = []
    duration_s = float(probe.get("duration_s") or 0.0)
    if duration_s <= 0:
        failures.append("non_positive_duration")
    if expected_duration_s is not None and abs(duration_s - expected_duration_s) > duration_tolerance_s:
        failures.append(f"duration_out_of_tolerance:{duration_s:.3f}s")
    if minimum_width is not None and int(probe.get("width") or 0) < minimum_width:
        failures.append(f"width_below_minimum:{probe.get('width')}")
    if minimum_height is not None and int(probe.get("height") or 0) < minimum_height:
        failures.append(f"height_below_minimum:{probe.get('height')}")
    if minimum_fps is not None and float(probe.get("fps") or 0.0) < minimum_fps:
        failures.append(f"fps_below_minimum:{float(probe.get('fps') or 0.0):.3f}")
    if require_audio and int(probe.get("audio_streams") or 0) < 1:
        failures.append("audio_stream_required")
    if max_freeze_s is not None and freeze is not None and float(freeze.get("max_duration_s") or 0.0) > max_freeze_s:
        failures.append(f"freeze_too_long:{float(freeze.get('max_duration_s') or 0.0):.3f}s")
    if max_black_s is not None and black is not None and float(black.get("max_duration_s") or 0.0) > max_black_s:
        failures.append(f"black_segment_too_long:{float(black.get('max_duration_s') or 0.0):.3f}s")
    return {"passed": not failures, "failures": failures}


def audit_video(
    video: Path,
    *,
    expected_duration_s: float | None = None,
    duration_tolerance_s: float = 0.75,
    minimum_width: int | None = None,
    minimum_height: int | None = None,
    minimum_fps: float | None = None,
    require_audio: bool = False,
    deep_scan: bool = False,
    freeze_threshold_s: float = 1.5,
    max_freeze_s: float | None = None,
    black_threshold_s: float = 0.5,
    max_black_s: float | None = None,
) -> dict[str, Any]:
    probe = probe_video(video)
    freeze = detect_freezes(video, minimum_s=freeze_threshold_s) if deep_scan else None
    black = detect_black(video, minimum_s=black_threshold_s) if deep_scan else None
    verdict = evaluate_video_evidence(
        probe,
        expected_duration_s=expected_duration_s,
        duration_tolerance_s=duration_tolerance_s,
        minimum_width=minimum_width,
        minimum_height=minimum_height,
        minimum_fps=minimum_fps,
        require_audio=require_audio,
        freeze=freeze,
        max_freeze_s=max_freeze_s,
        black=black,
        max_black_s=max_black_s,
    )
    return {"probe": probe, "freeze": freeze, "black": black, **verdict}


def require_video_quality(video: Path, **policy: Any) -> dict[str, Any]:
    evidence = audit_video(video, **policy)
    if not evidence["passed"]:
        raise VideoQualityError(f"video quality gate failed: {evidence['failures']}")
    return evidence
