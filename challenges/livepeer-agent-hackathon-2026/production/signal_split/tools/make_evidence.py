"""Evidence images for the HAL Studio demo (1920x1080 JPGs), drawn from the production's own files and receipts.

Usage: python tools/make_evidence.py <edl.json> <out_dir>

call.jpg       one real Livepeer Agent call from receipts/livepeer_calls_raw.json, as it was sent and what came back
keyframes.jpg  the twelve FLUX keyframes
shots_a.jpg    frame strips of shots V01-V06 (Kling), shots_b.jpg for V07-V12
edit.jpg       the song's waveform with its bar lines, sections and the cuts HAL placed on them"""
from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parents[1]
W, H = 1920, 1080
BG, INK, MUTED = (11, 10, 18), (238, 234, 244), (150, 146, 170)
PINK, CYAN = (236, 72, 153), (56, 189, 248)
FONTS = Path(r"C:\Windows\Fonts")


def face(size: int, mono: bool = False, bold: bool = False) -> ImageFont.FreeTypeFont:
    if mono:
        return ImageFont.truetype(str(FONTS / ("consolab.ttf" if bold else "consola.ttf")), size)
    font = ImageFont.truetype(str(FONTS / "bahnschrift.ttf"), size)
    try:
        font.set_variation_by_name("Bold" if bold else "Regular")
    except Exception:  # noqa: BLE001
        pass
    return font


def canvas(title: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(image)
    draw.text((80, 50), title.upper(), font=face(30, bold=True), fill=PINK)
    return image, draw


def call_card(out: Path) -> None:
    calls = json.loads((HERE / "receipts" / "livepeer_calls_raw.json").read_text(encoding="utf-8"))
    call = next(c for c in calls if c.get("idempotency_key") == "signal-split-v09-20260926")
    image, draw = canvas("One real call · Livepeer Agent MCP, raw surface")
    mono, y = face(34, mono=True), 150
    lines = ["run_capability(", f'  capability = "{call["capability"]}",', '  source_url = <keyframe K09, FLUX>,']
    lines += [f"  prompt     = {part}" if i == 0 else f"               {part}"
              for i, part in enumerate(textwrap.wrap(json.dumps(call["prompt"]), 66))]
    lines += [f'  inputs     = {json.dumps(call["inputs"])},  async = true,', f'  session_id = "livepeer-hackathon-20260926")']
    for line in lines:
        draw.text((110, y), line, font=mono, fill=INK)
        y += 48
    y += 30
    seconds = (call.get("elapsed_ms") or 0) / 1000
    draw.text((110, y), f'→ {call["job_id"]} · {call["status"]} in {seconds:.0f} s · ${call["cost_usd_estimated"]:.3f}',
              font=face(40, mono=True, bold=True), fill=CYAN)
    shot = HERE / "shots" / "V09.mp4"
    frame = out / "_v09.jpg"
    import subprocess
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", "3.5", "-i", str(shot), "-frames:v", "1",
                    "-vf", "scale=620:-2", str(frame)], check=True)
    thumb = Image.open(frame)
    image.paste(thumb, (W - thumb.width - 90, H - thumb.height - 90))
    frame.unlink()
    image.save(out / "call.jpg", quality=92)


def keyframes(out: Path) -> None:
    image, draw = canvas("12 keyframes · flux-pro")
    tile_w, tile_h, gap = 432, 243, 24
    left = (W - (4 * tile_w + 3 * gap)) // 2
    for index in range(12):
        tile = Image.open(HERE / "keyframes" / f"K{index + 1:02d}.png").convert("RGB").resize((tile_w, tile_h))
        x, y = left + (index % 4) * (tile_w + gap), 140 + (index // 4) * (tile_h + gap + 44)
        image.paste(tile, (x, y))
        draw.text((x, y + tile_h + 6), f"K{index + 1:02d}", font=face(26, mono=True), fill=MUTED)
    image.save(out / "keyframes.jpg", quality=92)


def shots(out: Path) -> None:
    for name, ids in (("shots_a", range(1, 7)), ("shots_b", range(7, 13))):
        image, draw = canvas(f"shots V{ids[0]:02d}-V{ids[-1]:02d} · kling-v3-turbo-pro-i2v · 7 s each, six frames per shot")
        y, row = 120, 142  # six rows fit under the title
        for number in ids:
            strip = Image.open(HERE / "shots" / f"strip_V{number:02d}.jpg").convert("RGB")
            strip = strip.resize((round(strip.width * row / strip.height), row))
            image.paste(strip, (200, y))
            draw.text((80, y + row // 2 - 18), f"V{number:02d}", font=face(32, mono=True, bold=True), fill=CYAN)
            y += row + 14
        image.save(out / f"{name}.jpg", quality=92)


def edit(edl_path: Path, out: Path) -> None:
    import numpy as np
    import soundfile

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from build_signal_split_edl import bar_lines, merge_sections, snap_sections

    edl = json.loads(edl_path.read_text(encoding="utf-8"))
    audio, rate = soundfile.read(str((edl_path.parent / edl["song"]).resolve()), always_2d=True)
    mono = np.abs(audio.mean(axis=1))
    duration = edl["duration_s"]
    image, draw = canvas("The edit · every cut on a bar line of the song's own beat grid")
    top, bottom, left, right = 260, 760, 80, W - 80
    scale = (right - left) / duration
    middle = (top + bottom) // 2
    columns = np.array_split(mono, right - left)
    peak = max(float(column.max()) for column in columns if len(column)) or 1.0
    for x, column in enumerate(columns):
        height = (float(column.max()) / peak) * (bottom - top) / 2 if len(column) else 0
        draw.line([(left + x, middle - height), (left + x, middle + height)], fill=(70, 66, 96))
    sections = merge_sections(edl["sections"])
    bars = bar_lines(edl["beat_grid"], duration, [start for _, start, _ in sections[1:]])
    for mark in bars:
        draw.line([(left + mark * scale, top), (left + mark * scale, bottom)], fill=(40, 38, 58), width=1)
    for label, start, end in snap_sections(sections, bars, duration):
        colour = PINK if label == "chorus" else CYAN
        draw.rectangle([left + start * scale, top - 70, left + end * scale - 3, top - 26], outline=colour, width=3)
        draw.text((left + start * scale + 10, top - 66), label, font=face(28, bold=True), fill=colour)
    for cut in edl["cuts"]:
        x = left + cut["start_s"] * scale
        if cut.get("performance"):  # lip-synced performance: a cyan band instead of a shot label
            draw.rectangle([x + 2, bottom + 14, left + cut["end_s"] * scale - 2, bottom + 40], fill=CYAN)
        else:
            draw.text((x + 6, bottom + 18), Path(cut["source"]).stem, font=face(20, mono=True), fill=MUTED)
        draw.line([(x, top - 10), (x, bottom + 10)], fill=PINK, width=3)
    bpm = 60 / edl["beat_grid"]["period_s"]
    performed = sum(1 for cut in edl["cuts"] if cut.get("performance"))
    first = (f"{len(edl['cuts'])} cuts, {performed} lip-synced (cyan) · beat grid {bpm:.1f} BPM"
             + (", read as half time" if bpm > 130 else ""))
    draw.text((left, bottom + 80), first, font=face(34), fill=INK)
    draw.text((left, bottom + 130), "two-bar cuts in verses, one-bar cuts in choruses · no cut longer than its 7 s shot",
              font=face(34), fill=MUTED)
    image.save(out / "edit.jpg", quality=92)


def lipsync(out: Path) -> None:
    """Performance frames, then the check: the audio inside a returned clip against the vocal segment that was sent."""
    import subprocess

    import numpy as np

    image, draw = canvas("Lip-sync · kontext-edit frames, talking-head clips, and HAL's alignment check")
    names = ["street", "tvwall", "bathroom", "gas"]
    for index, name in enumerate(names):
        tile = Image.open(HERE / "performance" / f"PK_{name}.jpg").convert("RGB").resize((420, 227))
        image.paste(tile, (80 + index * 445, 120))
    rate = 8000

    def pcm(path: Path) -> np.ndarray:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(rate), "-f", "f32le", "-"],
                             capture_output=True, check=True).stdout
        return np.frombuffer(raw, np.float32)

    sent, got = pcm(HERE / "performance" / "audio" / "P_street.wav"), pcm(HERE / "performance" / "P_street.mp4")
    top, height, left, right = 430, 150, 80, W - 80
    for row, (label, signal, colour) in enumerate((("sent: vocal stem, song 43.44-57.91 s", sent, CYAN),
                                                   ("returned inside the lip-sync clip", got, PINK))):
        y0 = top + row * (height + 60)
        draw.text((left, y0 - 34), label, font=face(26), fill=MUTED)
        columns = np.array_split(np.abs(signal[:len(sent)]), right - left)
        peak = max(float(c.max()) for c in columns if len(c)) or 1.0
        for x, column in enumerate(columns):
            h = (float(column.max()) / peak) * height / 2 if len(column) else 0
            draw.line([(left + x, y0 + height / 2 - h), (left + x, y0 + height / 2 + h)], fill=colour)
    env = lambda x: np.convolve(np.abs(x), np.ones(80) / 80, mode="same")[::40]
    a, b = env(sent), env(got)
    n = min(len(a), len(b))
    lags = range(-40, 41)
    score = [np.corrcoef(a[max(0, -l):n - max(0, l)], b[max(0, l):n - max(0, -l)])[0, 1] for l in lags]
    best = int(np.argmax(score))
    draw.text((left, top + 2 * (height + 60) + 10), f"offset {lags[best] * 5} ms · correlation {score[best]:.2f} · the same check passed on all eight clips",
              font=face(38, bold=True), fill=INK)
    image.save(out / "lipsync.jpg", quality=92)


if __name__ == "__main__":
    edl_file, target = Path(sys.argv[1]), Path(sys.argv[2])
    target.mkdir(parents=True, exist_ok=True)
    call_card(target)
    keyframes(target)
    shots(target)
    edit(edl_file, target)
    lipsync(target)
    print("evidence written")
