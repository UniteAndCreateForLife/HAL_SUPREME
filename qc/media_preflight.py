from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Callable, Mapping

from qc.motion import MotionEvidenceError, require_temporal_motion


class MediaPreflightError(RuntimeError):
    pass


def _positive_float(value: Any, default: float = 0.0) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _ratio(value: Any) -> float:
    if not value:
        return 0.0
    text = str(value).strip()
    if "/" not in text:
        return _positive_float(text)
    numerator, denominator = text.split("/", 1)
    try:
        num = float(numerator)
        den = float(denominator)
    except ValueError:
        return 0.0
    return num / den if den else 0.0


def probe_media(
    media: Path,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    """Return machine-readable stream/container evidence from ffprobe."""
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_streams",
        "-show_format",
        "-of",
        "json",
        str(media),
    ]
    proc = runner(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise MediaPreflightError(proc.stderr.strip() or "ffprobe failed")
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise MediaPreflightError("ffprobe returned invalid JSON") from exc
    if not isinstance(payload, dict):
        raise MediaPreflightError("ffprobe payload must be an object")
    return payload


def evaluate_probe(
    payload: Mapping[str, Any],
    *,
    min_duration_s: float = 0.25,
    min_width: int = 320,
    min_height: int = 180,
    min_fps: float = 12.0,
    require_audio: bool = True,
) -> dict[str, Any]:
    """Evaluate structural media evidence without invoking external tools."""
    streams = payload.get("streams", [])
    if not isinstance(streams, list):
        streams = []
    video_streams = [
        stream
        for stream in streams
        if isinstance(stream, dict) and stream.get("codec_type") == "video"
    ]
    audio_streams = [
        stream
        for stream in streams
        if isinstance(stream, dict) and stream.get("codec_type") == "audio"
    ]
    video = video_streams[0] if video_streams else {}

    format_info = payload.get("format", {})
    if not isinstance(format_info, dict):
        format_info = {}
    duration_s = _positive_float(format_info.get("duration"))
    if not duration_s:
        duration_s = _positive_float(video.get("duration"))

    width = int(video.get("width") or 0)
    height = int(video.get("height") or 0)
    fps = _ratio(video.get("avg_frame_rate") or video.get("r_frame_rate"))

    checks = {
        "has_video": bool(video_streams),
        "duration": duration_s >= min_duration_s,
        "resolution": width >= min_width and height >= min_height,
        "frame_rate": fps >= min_fps,
        "audio": (not require_audio) or bool(audio_streams),
    }
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "observed": {
            "duration_s": round(duration_s, 3),
            "width": width,
            "height": height,
            "fps": round(fps, 3),
            "video_streams": len(video_streams),
            "audio_streams": len(audio_streams),
        },
        "policy": {
            "min_duration_s": min_duration_s,
            "min_width": min_width,
            "min_height": min_height,
            "min_fps": min_fps,
            "require_audio": require_audio,
        },
    }


def require_media_preflight(
    media: Path,
    *,
    min_duration_s: float = 0.25,
    min_width: int = 320,
    min_height: int = 180,
    min_fps: float = 12.0,
    require_audio: bool = True,
    probe_runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    motion_checker: Callable[[Path], dict[str, Any]] = require_temporal_motion,
) -> dict[str, Any]:
    """Require structural evidence and HAL's existing temporal-motion gate."""
    media = Path(media)
    if not media.is_file():
        raise MediaPreflightError(f"media file does not exist: {media}")

    structural = evaluate_probe(
        probe_media(media, runner=probe_runner),
        min_duration_s=min_duration_s,
        min_width=min_width,
        min_height=min_height,
        min_fps=min_fps,
        require_audio=require_audio,
    )
    if not structural["passed"]:
        failed = [name for name, ok in structural["checks"].items() if not ok]
        raise MediaPreflightError(
            f"structural media preflight failed: {','.join(failed)}; "
            f"observed={structural['observed']}"
        )

    try:
        motion = motion_checker(media)
    except MotionEvidenceError as exc:
        raise MediaPreflightError(f"motion preflight failed: {exc}") from exc
    if not isinstance(motion, dict) or motion.get("passed") is not True:
        raise MediaPreflightError(
            f"motion preflight returned no passing evidence: {motion!r}"
        )

    return {
        "schema": "hal.media_preflight.v1",
        "media": str(media),
        "passed": True,
        "structural": structural,
        "motion": motion,
    }
