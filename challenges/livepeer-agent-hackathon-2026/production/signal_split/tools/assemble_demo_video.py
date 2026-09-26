"""Assemble the HAL Studio hackathon demo: narrated slides and evidence, then the full music video, then a close card.

Usage: python tools/assemble_demo_video.py <slides_dir> <voiceover.mp3> <music_video.mp4> <evidence_dir> <bed.wav> <out.mp4>

The narration has seven paragraphs. Slide changes sit in the middle of the six longest pauses, so every slide arrives
with its paragraph. Paragraph four (Livepeer Agent renders every step) shows the create slide, one real call, the
keyframes and the shot strips; paragraph five shows the review slide and the edit map. The narration is levelled to
-16 LUFS over a quiet bed (an instrumental of the song, about 18 LU under the voice). The music video follows with its
own mastered audio."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

FF = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
W, H, FPS = 1920, 1080, 24


def duration(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def paragraph_marks(voiceover: Path, paragraphs: int = 7) -> list[float]:
    """Midpoints of the longest pauses, one fewer than the paragraphs, in time order."""
    text = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(voiceover), "-af",
                           "silencedetect=noise=-40dB:d=0.35", "-f", "null", "-"], capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", text)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", text)]
    pauses = sorted(zip(starts, ends), key=lambda pause: pause[1] - pause[0], reverse=True)[:paragraphs - 1]
    if len(pauses) < paragraphs - 1:
        raise ValueError(f"found {len(pauses)} paragraph pauses, need {paragraphs - 1}")
    return sorted((a + b) / 2 for a, b in pauses)


def paragraph_marks_from_text(voiceover: Path, script: Path) -> list[float]:
    """Slide changes on the first spoken word of each paragraph (Whisper word times, CPU, cached model)."""
    import re as _re
    if os.environ.get("HAL_SCRIPTS"):  # HAL's Whisper wrapper; without it the slides follow the longest pauses
        sys.path.insert(0, os.environ["HAL_SCRIPTS"])
    from hal_lyric_timeline_v1 import transcribe_words

    words = transcribe_words(voiceover)
    norm = lambda w: _re.sub(r"[^a-z0-9]", "", w.lower())  # noqa: E731
    heard = [norm(w) for w, _, _ in words]
    paragraphs = [p for p in script.read_text(encoding="utf-8").split("\n\n") if p.strip()]
    marks, cursor = [], 0
    for paragraph in paragraphs[1:]:
        first = [norm(w) for w in paragraph.split()[:3]]
        for index in range(cursor, len(heard) - 2):  # two of the first three words is enough: Whisper hears HAL as "hall"
            if sum(a == b for a, b in zip(heard[index:index + 3], first)) >= 2:
                marks.append((words[index - 1][2] + words[index][1]) / 2 if index else words[index][1])
                cursor = index + 1
                break
        else:
            raise ValueError(f"paragraph not heard: {' '.join(first)}")
    return marks


def still(image: Path, seconds: float, out: Path, push: bool) -> Path:
    frames = max(1, round(seconds * FPS))
    if push:  # a slow push-in keeps a slide alive without distracting from it
        move = (f"scale={round(W * 1.1)}:-2,zoompan=z='1+0.035*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                f":d={frames}:s={W}x{H}:fps={FPS}")
    else:
        move = f"scale={W}:{H},fps={FPS}"
    subprocess.run([*FF, "-loop", "1", "-i", str(image), "-vf", f"{move},format=yuv420p", "-frames:v", str(frames),
                    "-c:v", "libx264", "-crf", "18", "-r", str(FPS), str(out)], check=True)
    return out


def main(slides: Path, voiceover: Path, video: Path, evidence: Path, bed: Path, out: Path) -> dict:
    out = out.resolve()
    work = out.parent / (out.stem + "_work")
    work.mkdir(parents=True, exist_ok=True)
    vo = duration(voiceover)
    script = Path(__file__).resolve().parents[1] / "demo" / os.environ.get("DEMO_SCRIPT", "VOICEOVER_V3.txt")
    try:
        marks = paragraph_marks_from_text(voiceover, script)
    except Exception as error:  # noqa: BLE001 (no Whisper here: fall back to the longest pauses)
        print(f"word alignment unavailable ({error}); using pauses", file=sys.stderr)
        marks = paragraph_marks(voiceover)
    bounds = [0.0, *marks, vo + 0.8]
    spans = [b - a for a, b in zip(bounds, bounds[1:])]
    plan = [
        [("01_title", 1.0)], [("02_problem", 1.0)], [("03_loop", 1.0)],
        [("04_create", 0.32), ("ev:call", 0.14), ("ev:keyframes", 0.11), ("ev:shots_a", 0.10), ("ev:shots_b", 0.10),
         ("ev:lipsync", 0.23)],
        [("05_review", 0.55), ("ev:edit", 0.45)],
        [("06_taste", 1.0)], [("07_result", 1.0)],
    ]
    pieces, timeline, clock = [], [], 0.0
    for span, items in zip(spans, plan):
        for name, share in items:
            seconds = span * share
            source = evidence / f"{name[3:]}.jpg" if name.startswith("ev:") else slides / f"{name}.png"
            pieces.append(still(source, seconds, work / f"{len(pieces):02d}_{name.replace(':', '_')}.mp4", not name.startswith("ev:")))
            timeline.append({"item": name, "start_s": round(clock, 2), "seconds": round(seconds, 2)})
            clock += seconds
    listing = work / "narrated.txt"
    listing.write_text("".join(f"file '{p.as_posix()}'\n" for p in pieces), encoding="utf-8")
    picture = work / "narrated_picture.mp4"
    subprocess.run([*FF, "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(picture)], check=True)
    length = duration(picture)
    narrated = work / "narrated.mp4"
    mix = (f"[1:a]loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000,apad[v];"
           f"[2:a]aresample=48000,volume=-14.4dB,afade=t=in:d=1.5,afade=t=out:st={length - 2.5:.2f}:d=2.5[b];"
           f"[v][b]amix=inputs=2:duration=first:normalize=0,atrim=0:{length:.3f}[a]")
    subprocess.run([*FF, "-i", str(picture), "-i", str(voiceover), "-i", str(bed), "-filter_complex", mix,
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", str(narrated)], check=True)
    mv = work / "music_video.mp4"
    subprocess.run([*FF, "-i", str(video), "-vf", f"scale={W}:{H},fps={FPS},format=yuv420p", "-c:v", "libx264", "-crf", "18",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", str(mv)], check=True)
    close = still(slides / "08_close.png", 6.0, work / "08_close.mp4", True)
    close_a = work / "08_close_a.mp4"
    subprocess.run([*FF, "-i", str(close), "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-shortest", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", str(close_a)], check=True)
    final_list = work / "final.txt"
    final_list.write_text("".join(f"file '{p.as_posix()}'\n" for p in (narrated, mv, close_a)), encoding="utf-8")
    subprocess.run([*FF, "-f", "concat", "-safe", "0", "-i", str(final_list), "-c:v", "libx264", "-crf", "20",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)], check=True)
    receipt = {"out": str(out), "seconds": round(duration(out), 2), "voiceover_s": round(vo, 2),
               "paragraph_marks_s": [round(m, 2) for m in marks], "narrated_timeline": timeline,
               "music_video": str(video), "music_video_s": round(duration(video), 2), "bed": str(bed)}
    out.with_suffix(".receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


if __name__ == "__main__":
    print(json.dumps(main(*(Path(a) for a in sys.argv[1:7])), indent=2))
