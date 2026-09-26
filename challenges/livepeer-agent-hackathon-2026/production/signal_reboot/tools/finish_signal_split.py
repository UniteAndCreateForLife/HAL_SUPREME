"""Master the song, cut the SIGNAL REBOOT music video from its EDL, grade it, set the typography, and check the result.

Usage: python tools/finish_signal_split.py <edl.json> <out.mp4> [typography_dir] [drums.wav]

1. Master: master_song_v2.py (corrective EQ, three-band compression with the bass in mono, glue compression, tape-style
   saturation, a 4x oversampled limiter) to -9.5 LUFS.
2. Cut: assemble_music_video_v1 (hard cuts on the EDL, B-roll and lip-synced performance, the master as the only audio).
3. Grade: one two-tone pass for the whole video (teal shadows, pink highlights, deeper blacks, a one-pixel chroma split,
   light sharpening, fine grain, a vignette) and a fade to black on the closing shot.
3b. Beat effects (beat_fx.py): zoom punches and shakes on the bar grid, glitch transitions and light leaks at section
   changes, a grade per section, push-ins on B-roll, handheld drift on performance, a 2.2:1 letterbox.
4. Typography: every event in <typography_dir>/events.json (title, word hits, typed line) overlaid at its start time;
   the end card (the last line typed on black, then credits) is appended after the song as its own silent clip.
5. QC: duration against the song, loudness and true peak of the final audio, a contact sheet.
The output frame rate is the EDL's `fps` (25 for SIGNAL REBOOT, the rate of the lip-sync clips)."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # assemble_music_video_v1 sits next to this file

from assemble_music_video_v1 import assemble, probe_duration, sha256  # noqa: E402

FF = ["ffmpeg", "-hide_banner", "-y"]
FPS = 24
GRADE = ("eq=contrast=1.10:saturation=1.16:gamma=1.0,"
         "colorbalance=rs=-0.05:gs=-0.01:bs=0.09:rh=0.07:gh=-0.02:bh=-0.03,"
         "curves=all='0/0 0.05/0.025 0.5/0.5 1/1',rgbashift=rh=-2:bh=2,unsharp=5:5:0.35,noise=alls=4:allf=t,"
         "vignette=angle=PI/4.5")


def master(song: Path, out: Path) -> dict:
    probe = subprocess.run([*FF, "-i", str(song), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                           capture_output=True, text=True, check=True).stderr
    measured = json.loads(probe[probe.rindex("{"):probe.rindex("}") + 1])
    second = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={measured['input_i']}:measured_TP={measured['input_tp']}:"
              f"measured_LRA={measured['input_lra']}:measured_thresh={measured['input_thresh']}:"
              f"offset={measured['target_offset']}:linear=true")
    subprocess.run([*FF, "-loglevel", "error", "-i", str(song), "-af", second, "-ar", "48000", "-c:a", "pcm_s24le", str(out)],
                   check=True)
    return measured


def loudness(path: Path) -> dict:
    text = subprocess.run([*FF, "-nostats", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"],
                          capture_output=True, text=True).stderr
    integrated = re.findall(r"I:\s+(-?[\d.]+) LUFS", text)
    peak = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", text)
    return {"integrated_lufs": float(integrated[-1]), "true_peak_dbtp": float(peak[-1])}


def overlay_typography(video: Path, events: list[dict], typography: Path, out: Path) -> None:
    inputs, graph, last = ["-i", str(video)], [], "0:v"
    for index, event in enumerate(events, start=1):
        inputs += ["-framerate", str(FPS), "-i", str(typography / event["dir"] / "%04d.png")]
        graph.append(f"[{index}:v]format=rgba,setpts=PTS-STARTPTS+{event['start_s']:.3f}/TB[t{index}]")
        graph.append(f"[{last}][t{index}]overlay=eof_action=pass:format=auto[v{index}]")
        last = f"v{index}"
    subprocess.run([*FF, "-loglevel", "error", *inputs, "-filter_complex", ";".join(graph), "-map", f"[{last}]", "-map", "0:a",
                    "-c:v", "libx264", "-crf", "17", "-preset", "slow", "-pix_fmt", "yuv420p", "-c:a", "copy", str(out)],
                   check=True)


def end_clip(typography: Path, event: dict, out: Path, fps: int = FPS) -> None:
    subprocess.run([*FF, "-loglevel", "error", "-framerate", str(FPS), "-i", str(typography / event["dir"] / "%04d.png"),
                    "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-shortest", "-vf", f"fps={fps},format=yuv420p",
                    "-c:v", "libx264", "-crf", "17", "-c:a", "aac", "-b:a", "320k", str(out)], check=True)


def main(edl_path: Path, out: Path, typography: Path | None = None, drums: Path | None = None) -> dict:
    edl_path, out = edl_path.resolve(), out.resolve()  # ffmpeg's concat list resolves relative paths against itself
    edl = json.loads(edl_path.read_text(encoding="utf-8"))
    base = edl_path.parent
    song = (base / edl["song"]).resolve()
    mastered = song.with_name(song.stem + "_master_v2.wav")
    from master_song_v2 import master as master_release
    mastering = master_release(song, mastered, -9.5)
    measured = {"input_i": mastering["input"]["integrated_lufs"], "input_tp": mastering["input"]["true_peak_dbtp"],
                "input_lra": mastering["input"]["lra_lu"]}
    duration = edl["duration_s"]
    edl["song"], edl["overlays"] = str(mastered), []
    cut_edl = edl_path.with_name(edl_path.stem + "_final.json")
    cut_edl.write_text(json.dumps(edl, indent=2) + "\n", encoding="utf-8")
    work = out.parent / (out.stem + "_work")
    raw = out.with_name(out.stem + "_ungraded.mp4")
    assemble(cut_edl, raw, work)
    graded = work / "graded.mp4"
    grade = f"{GRADE},fade=t=out:st={duration - 1.2:.3f}:d=1.2"  # the closing shot ends on a dot; finish it to black
    subprocess.run([*FF, "-loglevel", "error", "-i", str(raw), "-vf", grade, "-c:v", "libx264", "-crf", "16", "-preset", "medium",
                    "-pix_fmt", "yuv420p", "-c:a", "copy", str(graded)], check=True)
    if drums:  # kick and snare hits from the drum stem drive zoom punches, shakes and section glitches
        from beat_fx import plan as fx_plan, render as fx_render
        with_fx = work / "fx.mp4"
        fx_report = fx_render(graded, fx_plan(edl, drums), with_fx)
        graded = with_fx
    else:
        fx_report = None
    events = json.loads((typography / "events.json").read_text(encoding="utf-8")) if typography else []
    overlays = [event for event in events if event["name"] != "endcard"]
    titled = work / "titled.mp4"
    if overlays:
        overlay_typography(graded, overlays, typography, titled)
    else:
        titled = graded
    parts = [titled]
    for event in events:
        if event["name"] == "endcard":
            clip = work / "endcard.mp4"
            end_clip(typography, event, clip, edl.get("fps", FPS))
            parts.append(clip)
    listing = work / "final.txt"
    listing.write_text("".join(f"file '{part.as_posix()}'\n" for part in parts), encoding="utf-8")
    subprocess.run([*FF, "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listing), "-r", str(edl.get("fps", FPS)),
                    "-c:v", "libx264", "-crf", "17",
                    "-preset", "slow", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "320k", "-ar", "48000",
                    "-movflags", "+faststart", str(out)], check=True)
    sheet = out.with_name(out.stem + "_sheet.jpg")
    middles = "+".join(f"eq(n\\,{round((c['start_s'] + c['end_s']) / 2 * edl.get('fps', FPS))})" for c in edl["cuts"])
    subprocess.run([*FF, "-loglevel", "error", "-i", str(out), "-vf",
                    f"select='{middles}',scale=384:-2,tile=5x{-(-len(edl['cuts']) // 5)}", "-frames:v", "1", "-update", "1",
                    str(sheet)], check=True)
    receipt = {"schema": "hal.signal-split.finish.v3", "edl": str(cut_edl), "song": str(song), "master": str(mastered),
               "master_measured_input": {k: measured[k] for k in ("input_i", "input_tp", "input_lra")},
               "output": str(out), "output_sha256": sha256(out), "duration_s": round(probe_duration(out), 3),
               "song_duration_s": duration, "final_audio": loudness(out), "cuts": len(edl["cuts"]),
               "performance_cuts": sum(1 for c in edl["cuts"] if c.get("performance")), "grade": GRADE,
               "typography_events": [e["name"] for e in events], "beat_fx": fx_report, "contact_sheet": str(sheet)}
    out.with_suffix(".receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


if __name__ == "__main__":
    print(json.dumps(main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]) if len(sys.argv) > 3 else None,
                          Path(sys.argv[4]) if len(sys.argv) > 4 else None), indent=2))
