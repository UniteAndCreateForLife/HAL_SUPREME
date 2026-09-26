"""Slides for the HAL Studio hackathon demo video (1920x1080 PNGs), in the music video's palette.

Usage: python tools/make_demo_slides.py <facts.json> <out_dir>
facts.json supplies the measured numbers so every figure on a slide comes from a receipt."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
BG, INK, MUTED = (11, 10, 18), (238, 234, 244), (150, 146, 170)
PINK, CYAN = (236, 72, 153), (56, 189, 248)
FONTS = Path(r"C:\Windows\Fonts")


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    face = ImageFont.truetype(str(FONTS / "bahnschrift.ttf"), size)
    try:
        face.set_variation_by_name("Bold" if bold else "Regular")
    except Exception:  # noqa: BLE001
        pass
    return face


def canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(image)
    for y in range(0, H, 4):  # faint scanlines, like the video
        draw.line([(0, y), (W, y)], fill=(15, 14, 24))
    return image, draw


def wrap(draw: ImageDraw.ImageDraw, text: str, face: ImageFont.FreeTypeFont, width: int) -> list[str]:
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if draw.textlength(trial, font=face) > width and line:
            lines.append(line)
            line = word
        else:
            line = trial
    return lines + ([line] if line else [])


def text_block(draw, x, y, text, face, fill=INK, width=1500, gap=14):
    for line in wrap(draw, text, face, width):
        draw.text((x, y), line, font=face, fill=fill)
        y += face.size + gap
    return y


def eyebrow(draw, label: str, colour=PINK):
    draw.text((140, 120), label.upper(), font=font(30, True), fill=colour)
    draw.line([(140, 168), (260, 168)], fill=colour, width=4)


def save(image: Image.Image, out: Path, name: str) -> None:
    image.save(out / f"{name}.png")


def slides(facts: dict, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    # 01 title
    image, draw = canvas()
    draw.text((140, 330), "HAL Studio", font=font(150, True), fill=INK)
    text_block(draw, 146, 520, "A self-checking AI music and video director on Livepeer Agent", font(52), MUTED, 1600)
    draw.text((146, 820), "Livepeer Agent Hackathon 2026 · Builder track", font=font(34), fill=CYAN)
    draw.text((146, 870), "Unite And Create For Life × HAL SUPREME", font=font(34), fill=PINK)
    save(image, out, "01_title")
    # 02 problem
    image, draw = canvas()
    eyebrow(draw, "The problem")
    y = text_block(draw, 140, 260, "Generating media is easy now.", font(84, True))
    y = text_block(draw, 140, y + 10, "Knowing whether it is good is the hard part.", font(84, True), PINK)
    text_block(draw, 140, y + 60, facts["problem"], font(40), MUTED, 1600)
    save(image, out, "02_problem")
    # 03 loop
    image, draw = canvas()
    eyebrow(draw, "The loop", CYAN)
    steps = [("DIRECT", "owner picks the vibe"), ("CREATE", "Livepeer Agent renders"), ("REVIEW", "HAL measures every take"),
             ("REFINE", "reject or re-brief"), ("DECIDE", "the owner listens"), ("LEARN", "choices that win get picked more")]
    x = 140
    for index, (title, note) in enumerate(steps):
        colour = PINK if index % 2 == 0 else CYAN
        draw.rounded_rectangle([x, 420, x + 250, 600], radius=18, outline=colour, width=4)
        draw.text((x + 22, 450), title, font=font(46, True), fill=colour)
        text_block(draw, x + 22, 515, note, font(26), MUTED, 210, 6)
        if index < len(steps) - 1:
            draw.text((x + 258, 480), "→", font=font(56, True), fill=MUTED)
        x += 290
    text_block(draw, 140, 700, facts["loop_note"], font(38), INK, 1640)
    save(image, out, "03_loop")
    # 04 create
    image, draw = canvas()
    eyebrow(draw, "Create · every generative step runs on Livepeer Agent", CYAN)
    y, step = 240, min(110, 640 // max(1, len(facts["capabilities"])))  # the table fits above the note however long it is
    size = 44 if step >= 100 else 36
    for row in facts["capabilities"]:
        draw.text((140, y), row["capability"], font=font(size, True), fill=PINK)
        draw.text((860, y + 4), row["use"], font=font(size - 6), fill=INK)
        draw.text((1600, y + 4), row["cost"], font=font(size - 6), fill=CYAN)
        y += step
    text_block(draw, 140, y + 30, facts["create_note"], font(34), MUTED, 1640)
    save(image, out, "04_create")
    # 05 review
    image, draw = canvas()
    eyebrow(draw, "Review · HAL checks its own work")
    y = 250
    for line in facts["review_lines"]:
        draw.ellipse([140, y + 18, 158, y + 36], fill=PINK)
        y = text_block(draw, 190, y, line, font(40), INK, 1580) + 26
    save(image, out, "05_review")
    # 06 taste
    image, draw = canvas()
    eyebrow(draw, "The honest part", CYAN)
    y = text_block(draw, 140, 250, "Scores are not taste.", font(84, True), PINK)
    y = text_block(draw, 140, y + 40, facts["taste"], font(40), INK, 1640)
    text_block(draw, 140, y + 40, facts["taste_fix"], font(40), CYAN, 1640)
    save(image, out, "06_taste")
    # 07 result title card
    image, draw = canvas()
    eyebrow(draw, "The result")
    logo_file = Path(__file__).resolve().parents[1] / "titles" / "title_gothic_alpha.png"
    if logo_file.exists():  # the video's own chrome title
        from make_typography import logo_image
        logo = logo_image()
        logo = logo.resize((560, round(logo.height * 560 / logo.width)))
        image.paste(logo, (130, 215), logo)
    else:
        draw.text((140, 380), "SIGNAL SPLIT", font=font(140, True), fill=INK)
    text_block(draw, 146, 660, facts["result_line"], font(44), MUTED, 1600)
    save(image, out, "07_result")
    # 08 close
    image, draw = canvas()
    eyebrow(draw, "Open source", CYAN)
    draw.text((140, 300), "github.com/UniteAndCreateForLife/HAL_SUPREME", font=font(56, True), fill=INK)
    text_block(draw, 146, 400, "challenges/livepeer-agent-hackathon-2026", font(40), PINK)
    y = text_block(draw, 146, 520, facts["close"], font(40), MUTED, 1600)
    save(image, out, "08_close")


if __name__ == "__main__":
    slides(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")), Path(sys.argv[2]))
    print("slides written")
