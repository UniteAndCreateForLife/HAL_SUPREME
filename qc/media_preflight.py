from __future__ import annotations

import json
import math
import subprocess
from dataclasses import asdict, dataclass
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
    return parsed if math.isfinite(parsed) and parsed > 0 else default


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
    ratio = num / den if den else 0.0
    return ratio if math.isfinite(ratio) and ratio > 0 else 0.0


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

    try:
        width = int(video.get("width") or 0)
    except (TypeError, ValueError, OverflowError):
        width = 0
    try:
        height = int(video.get("height") or 0)
    except (TypeError, ValueError, OverflowError):
        height = 0
    if width < 0:
        width = 0
    if height < 0:
        height = 0
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


@dataclass(frozen=True)
class MediaAuditPolicy:
    min_integrated_lufs: float = -18.0
    max_integrated_lufs: float = -14.0
    max_true_peak_dbtp: float = -1.0
    min_dialogue_margin_db: float = 6.0
    max_picture_failures: int = 0
    min_text_height_px: float = 24.0


def _finite_number(section: Mapping[str, Any], key: str) -> float | None:
    value = section.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    parsed = float(value)
    if parsed != parsed or parsed in (float("inf"), float("-inf")):
        return None
    return parsed


def evaluate_audit_evidence(
    report: Mapping[str, Any],
    policy: MediaAuditPolicy | None = None,
) -> dict[str, Any]:
    """Evaluate shift-left production audits without rendering or provider calls."""
    policy = policy or MediaAuditPolicy()
    checks: dict[str, dict[str, Any]] = {}

    picture = report.get("picture")
    if isinstance(picture, Mapping):
        failed = _finite_number(picture, "failed_shots")
        text_px = _finite_number(picture, "minimum_text_height_px")
        picture_ok = (
            failed is not None
            and failed >= 0
            and text_px is not None
            and failed <= policy.max_picture_failures
            and text_px >= policy.min_text_height_px
        )
        picture_reason = (
            ""
            if picture_ok
            else "picture failures/text size exceed policy or evidence is invalid"
        )
        picture_evidence = dict(picture)
    else:
        picture_ok = False
        picture_reason = "missing picture audit"
        picture_evidence = {}
    checks["picture"] = {
        "passed": picture_ok,
        "reason": picture_reason,
        "evidence": picture_evidence,
    }

    audio = report.get("audio")
    if isinstance(audio, Mapping):
        lufs = _finite_number(audio, "integrated_lufs")
        peak = _finite_number(audio, "true_peak_dbtp")
        margin = _finite_number(audio, "minimum_dialogue_margin_db")
        audio_ok = (
            lufs is not None
            and peak is not None
            and margin is not None
            and policy.min_integrated_lufs <= lufs <= policy.max_integrated_lufs
            and peak <= policy.max_true_peak_dbtp
            and margin >= policy.min_dialogue_margin_db
        )
        audio_reason = (
            ""
            if audio_ok
            else "loudness/peak/dialogue margin exceed policy or evidence is invalid"
        )
        audio_evidence = dict(audio)
    else:
        audio_ok = False
        audio_reason = "missing audio audit"
        audio_evidence = {}
    checks["audio"] = {
        "passed": audio_ok,
        "reason": audio_reason,
        "evidence": audio_evidence,
    }

    story = report.get("story")
    story_ok = isinstance(story, Mapping) and story.get("blind_viewer_pass") is True
    checks["story"] = {
        "passed": story_ok,
        "reason": "" if story_ok else "blind-viewer story check did not pass",
        "evidence": dict(story) if isinstance(story, Mapping) else {},
    }

    provenance = report.get("provenance")
    provenance_ok = (
        isinstance(provenance, Mapping) and provenance.get("complete") is True
    )
    checks["provenance"] = {
        "passed": provenance_ok,
        "reason": "" if provenance_ok else "provenance evidence is incomplete",
        "evidence": dict(provenance) if isinstance(provenance, Mapping) else {},
    }

    failures = [name for name, check in checks.items() if not check["passed"]]
    return {
        "schema": "hal.media_audit_preflight.v1",
        "authority": "DERIVED_ACCEPTANCE_EVIDENCE",
        "passed": not failures,
        "failures": failures,
        "policy": asdict(policy),
        "checks": checks,
    }


def require_audit_preflight(
    report: Mapping[str, Any],
    policy: MediaAuditPolicy | None = None,
) -> dict[str, Any]:
    evidence = evaluate_audit_evidence(report, policy)
    if not evidence["passed"]:
        raise MediaPreflightError(
            "production audit preflight failed: " + ",".join(evidence["failures"])
        )
    return evidence


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


def require_production_preflight(
    media: Path,
    audit_report: Mapping[str, Any],
    *,
    audit_policy: MediaAuditPolicy | None = None,
    min_duration_s: float = 0.25,
    min_width: int = 320,
    min_height: int = 180,
    min_fps: float = 12.0,
    require_audio: bool = True,
    probe_runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    motion_checker: Callable[[Path], dict[str, Any]] = require_temporal_motion,
) -> dict[str, Any]:
    """Require both media integrity/motion and production audit evidence."""
    media_evidence = require_media_preflight(
        media,
        min_duration_s=min_duration_s,
        min_width=min_width,
        min_height=min_height,
        min_fps=min_fps,
        require_audio=require_audio,
        probe_runner=probe_runner,
        motion_checker=motion_checker,
    )
    audit_evidence = require_audit_preflight(audit_report, audit_policy)
    return {
        "schema": "hal.production_preflight.v1",
        "authority": "DERIVED_ACCEPTANCE_EVIDENCE",
        "media": str(Path(media)),
        "passed": True,
        "media_evidence": media_evidence,
        "audit_evidence": audit_evidence,
    }
