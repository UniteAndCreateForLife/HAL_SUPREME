from __future__ import annotations

import subprocess
from pathlib import Path


class MotionEvidenceError(RuntimeError):
    pass


def probe_frame_hashes(video: Path, sample_fps: float = 2.0) -> list[str]:
    """Return framemd5 hashes sampled from a video using ffmpeg."""
    cmd = [
        "ffmpeg", "-v", "error", "-i", str(video),
        "-vf", f"fps={sample_fps}",
        "-f", "framemd5", "-"
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise MotionEvidenceError(proc.stderr.strip() or "ffmpeg motion probe failed")
    hashes = []
    for line in proc.stdout.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        fields = [part.strip() for part in line.split(",")]
        if fields:
            hashes.append(fields[-1])
    return hashes


def require_temporal_motion(video: Path, minimum_unique_frames: int = 3) -> dict:
    hashes = probe_frame_hashes(video)
    unique = len(set(hashes))
    passed = len(hashes) >= minimum_unique_frames and unique >= minimum_unique_frames
    evidence = {
        "sampled_frames": len(hashes),
        "unique_frame_hashes": unique,
        "minimum_unique_frames": minimum_unique_frames,
        "passed": passed,
    }
    if not passed:
        raise MotionEvidenceError(f"zero-still gate failed: {evidence}")
    return evidence
