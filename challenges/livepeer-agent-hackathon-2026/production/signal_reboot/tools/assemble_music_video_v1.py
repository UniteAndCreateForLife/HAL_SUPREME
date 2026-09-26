"""Assemble a music video from an edit decision list: hard cuts over the song master.

EDL JSON (paths relative to the EDL file):
  {"song": "<master.wav>", "duration_s": 163.1, "fps": 25, "width": 1920, "height": 1080,
   "cuts": [{"id": "C01", "start_s": 0.0, "end_s": 6.1, "source": "<clip.mp4>", "in_s": 0.0}, ...],
   "overlays": [{"png": "<title.png>", "start_s": 155.0, "end_s": 163.1, "fade_s": 1.0}]}

Each cut is taken from its source at in_s for exactly its timeline length (frame counts come from
rounded cut boundaries, so the picture never drifts against the song), conformed to the frame size
and rate, and joined with hard cuts. The song master is the only audio. The EDL is refused before
any rendering if it has gaps, overlaps, sources too short for their cut, or a timeline that does
not end with the song.

Usage:
  python tools/assemble_music_video_v1.py --edl <edl.json> --out <video.mp4> --work <dir>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

FFMPEG = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]


def probe_duration(path: Path) -> float:
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1",
                             str(path)], capture_output=True, text=True, check=True)
    return float(result.stdout.strip())


def validate(edl: dict[str, Any], source_seconds: dict[str, float]) -> list[str]:
    """Every problem that would make the cut wrong; empty when the EDL is sound."""
    cuts, problems = edl["cuts"], []
    if not cuts:
        return ["no cuts"]
    if abs(cuts[0]["start_s"]) > 1e-6:
        problems.append("timeline must start at 0")
    for before, after in zip(cuts, cuts[1:]):
        if abs(before["end_s"] - after["start_s"]) > 1e-6:
            problems.append(f"gap or overlap between {before['id']} and {after['id']}")
    if abs(cuts[-1]["end_s"] - edl["duration_s"]) > 0.05:
        problems.append(f"timeline ends at {cuts[-1]['end_s']} but the song lasts {edl['duration_s']}")
    for cut in cuts:
        length = cut["end_s"] - cut["start_s"]
        available = source_seconds[cut["source"]] - cut.get("in_s", 0.0)
        if length <= 0:
            problems.append(f"{cut['id']} has no length")
        elif available + 1e-3 < length:
            problems.append(f"{cut['id']} needs {length:.2f} s but its source has {available:.2f} s after the in-point")
    return problems


def frame_counts(cuts: list[dict[str, Any]], fps: int) -> list[int]:
    """Frames per cut from rounded cut boundaries, so the cut lengths always add up to the timeline."""
    bounds = [round(cut["start_s"] * fps) for cut in cuts] + [round(cuts[-1]["end_s"] * fps)]
    return [end - start for start, end in zip(bounds, bounds[1:])]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def assemble(edl_path: Path, out: Path, work: Path) -> dict[str, Any]:
    edl = json.loads(edl_path.read_text(encoding="utf-8"))
    base = edl_path.parent
    fps, width, height = edl.get("fps", 25), edl.get("width", 1920), edl.get("height", 1080)
    source_seconds = {cut["source"]: probe_duration(base / cut["source"]) for cut in edl["cuts"]}
    problems = validate(edl, source_seconds)
    if problems:
        raise ValueError("; ".join(problems))
    work.mkdir(parents=True, exist_ok=True)
    conform = (f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},"
               f"fps={fps},setsar=1,format=yuv420p")
    parts = []
    for cut, frames in zip(edl["cuts"], frame_counts(edl["cuts"], fps)):
        part = work / f"{cut['id']}.mp4"
        subprocess.run([*FFMPEG, "-ss", f"{cut.get('in_s', 0.0):.3f}", "-i", str(base / cut["source"]), "-an", "-vf", conform,
                        "-frames:v", str(frames), "-c:v", "libx264", "-crf", "16", "-preset", "medium", str(part)], check=True)
        parts.append(part)
    listing = work / "concat.txt"
    listing.write_text("".join(f"file '{part.as_posix()}'\n" for part in parts), encoding="utf-8")
    picture = work / "picture.mp4"
    subprocess.run([*FFMPEG, "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(picture)], check=True)

    inputs, graph, last = ["-i", str(picture)], [], "0:v"
    for index, overlay in enumerate(edl.get("overlays", []), start=1):
        fade = overlay.get("fade_s", 1.0)
        inputs += ["-loop", "1", "-t", f"{edl['duration_s']:.3f}", "-i", str(base / overlay["png"])]
        graph.append(f"[{index}:v]format=rgba,fade=t=in:st={overlay['start_s']}:d={fade}:alpha=1,"
                     f"fade=t=out:st={overlay['end_s'] - fade}:d={fade}:alpha=1[o{index}]")
        graph.append(f"[{last}][o{index}]overlay=0:0:enable='between(t,{overlay['start_s']},{overlay['end_s']})'[v{index}]")
        last = f"v{index}"
    song_index = 1 + len(edl.get("overlays", []))  # after the picture and one input per overlay
    inputs += ["-i", str(base / edl["song"])]
    command = [*FFMPEG, *inputs]
    if graph:
        command += ["-filter_complex", ";".join(graph), "-map", f"[{last}]"]
    else:
        command += ["-map", "0:v"]
    command += ["-map", f"{song_index}:a", "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "320k", "-t", f"{edl['duration_s']:.3f}", "-movflags", "+faststart", str(out)]
    subprocess.run(command, check=True)
    receipt = {"schema": "hal.music-video-assembly.v1",
               "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
               "edl": str(edl_path), "output": str(out), "output_sha256": sha256(out),
               "duration_s": round(probe_duration(out), 3), "cuts": len(edl["cuts"]), "overlays": len(edl.get("overlays", []))}
    out.with_suffix(".receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--edl", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(assemble(args.edl, args.out, args.work), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
