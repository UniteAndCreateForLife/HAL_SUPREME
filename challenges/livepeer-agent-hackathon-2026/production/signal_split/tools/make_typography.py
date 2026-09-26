"""Typography for the SIGNAL SPLIT music video: a glitch-in chrome title, chorus word hits, and end credits on black.

Usage: python tools/make_typography.py <words.json> <song_duration_s> <out_dir>

Every event is a transparent PNG sequence (1920x1080, 24 fps) plus its start time, listed in <out_dir>/events.json for
the finishing pass to overlay. Word hits start on the sung word (Whisper word times on the separated vocal), so the
text lands with the voice. Styles: the chrome blackletter logo (ideogram-v4, background removed) for the title and the
end card; Bahnschrift Bold Condensed with a pink and cyan split for the word hits; letter-spaced Bahnschrift for credits."""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parents[1]
W, H, FPS = 1920, 1080, 24
PINK, CYAN, WHITE = (236, 72, 153), (56, 189, 248), (245, 245, 245)
FONT = r"C:\Windows\Fonts\bahnschrift.ttf"
# (word as Whisper hears it, text on screen): one hit per chorus line
HOOKS = [("glitch", "GLITCH"), ("replay", "REPLAY"), ("static", "STATIC"), ("signal", "SIGNAL")]


def font(size: int, variation: str) -> ImageFont.FreeTypeFont:
    face = ImageFont.truetype(FONT, size)
    face.set_variation_by_name(variation)
    return face


def spaced(draw: ImageDraw.ImageDraw, text: str, face, tracking: float) -> tuple[int, int]:
    width = sum(draw.textlength(ch, font=face) for ch in text) + tracking * (len(text) - 1)
    box = draw.textbbox((0, 0), text, font=face)
    return round(width), box[3] - box[1]


def draw_spaced(draw, xy, text, face, tracking, fill) -> None:
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=face, fill=fill)
        x += draw.textlength(ch, font=face) + tracking


def shift(array: np.ndarray, dx: int) -> np.ndarray:
    out = np.zeros_like(array)
    if dx > 0:
        out[:, dx:] = array[:, :-dx]
    elif dx < 0:
        out[:, :dx] = array[:, -dx:]
    else:
        out[:] = array
    return out


def split(layer: np.ndarray, dx: int, rng: random.Random, slices: int, slice_px: int) -> np.ndarray:
    """RGBA layer with a pink copy shifted left and a cyan copy shifted right under it, then horizontal slices offset."""
    alpha = layer[..., 3:4].astype(np.float32) / 255
    out = np.zeros_like(layer, dtype=np.float32)
    for colour, offset in ((CYAN, dx), (PINK, -dx)):
        a = shift(alpha, offset) * 0.85
        out[..., :3] = out[..., :3] * (1 - a) + np.array(colour, np.float32) * a
        out[..., 3:4] = np.maximum(out[..., 3:4], a * 255)
    a = alpha
    out[..., :3] = out[..., :3] * (1 - a) + layer[..., :3].astype(np.float32) * a
    out[..., 3:4] = np.maximum(out[..., 3:4], a * 255)
    out = out.astype(np.uint8)
    for _ in range(slices):
        top = rng.randrange(0, H - 8)
        height = rng.randrange(6, 40)
        out[top:top + height] = shift(out[top:top + height], rng.randint(-slice_px, slice_px))
    return out


def place(image: Image.Image, width: int, center: tuple[int, int]) -> np.ndarray:
    scaled = image.resize((width, round(image.height * width / image.width)), Image.LANCZOS)
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    canvas.paste(scaled, (center[0] - scaled.width // 2, center[1] - scaled.height // 2), scaled)
    return np.array(canvas)


def fade(array: np.ndarray, opacity: float) -> np.ndarray:
    out = array.copy()
    out[..., 3] = (out[..., 3].astype(np.float32) * max(0.0, min(1.0, opacity))).astype(np.uint8)
    return out


def logo_image() -> Image.Image:
    """The cut-out logo cropped to its lettering; the matte leaves thin specks near the edges, which rows and columns
    with little alpha in them drop."""
    logo = Image.open(HERE / "titles" / "title_gothic_alpha.png").convert("RGBA")
    solid = np.array(logo.getchannel("A")) > 100

    def main_run(counts: np.ndarray, gap: int = 12) -> tuple[int, int]:
        """The longest stretch of busy rows (or columns), bridging gaps between letters up to `gap` pixels."""
        busy = np.where(counts > 25)[0]
        runs, start = [], busy[0]
        for before, after in zip(busy, busy[1:]):
            if after - before > gap:
                runs.append((start, before))
                start = after
        runs.append((start, busy[-1]))
        return max(runs, key=lambda run: run[1] - run[0])

    top, bottom = main_run(solid.sum(axis=1))
    left, right = main_run(solid[top:bottom + 1].sum(axis=0), gap=40)
    cropped = logo.crop((int(left), int(top), int(right) + 1, int(bottom) + 1))
    return cropped


def write(frames: list[np.ndarray], folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    for index, frame in enumerate(frames):
        Image.fromarray(frame, "RGBA").save(folder / f"{index:04d}.png", compress_level=1)


def title(out: Path, start: float, seconds: float, rng: random.Random) -> dict:
    logo = place(logo_image(), 780, (W // 2, H // 2 + 10))
    top = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(top)
    face = font(34, "SemiLight")
    width, _ = spaced(draw, "HAL SUPREME", face, 18)
    draw_spaced(draw, ((W - width) // 2, H // 2 - 250), "HAL SUPREME", face, 18, WHITE + (235,))
    top = np.array(top)
    frames, total = [], round(seconds * FPS)
    for i in range(total):
        t = i / FPS
        entering, leaving = t < 0.4, t > seconds - 0.4
        strength = (0.4 - t) / 0.4 if entering else (t - (seconds - 0.4)) / 0.4 if leaving else 0.08
        flicker = 1.0 if not (entering or leaving) else (0.35 + 0.65 * rng.random())
        layer = split(logo, max(1, round(2 + 26 * strength)), rng, round(10 * strength), round(120 * strength))
        layer = fade(layer, flicker * (1 - max(0.0, t - (seconds - 0.4)) / 0.4 if leaving else flicker))
        words = fade(top, min(1.0, max(0.0, (t - 0.5) / 0.6)) * (1 - max(0.0, t - (seconds - 0.5)) / 0.5))
        frame = Image.alpha_composite(Image.fromarray(layer, "RGBA"), Image.fromarray(words, "RGBA"))
        frames.append(np.array(frame))
    write(frames, out / "title")
    return {"name": "title", "dir": "title", "start_s": start, "frames": total}


def hook(out: Path, name: str, text: str, start: float, seconds: float, rng: random.Random) -> dict:
    face = font(300, "Bold Condensed")
    probe = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    box = probe.textbbox((0, 0), text, font=face)
    art = Image.new("RGBA", (box[2] - box[0] + 40, box[3] - box[1] + 40), (0, 0, 0, 0))
    ImageDraw.Draw(art).text((20 - box[0], 20 - box[1]), text, font=face, fill=WHITE + (255,))
    frames, total = [], max(8, round(seconds * FPS))
    for i in range(total):
        progress = i / (total - 1)
        width = round(art.width * (1.10 - 0.10 * min(1.0, progress * 3)))  # a punch that settles
        layer = place(art, width, (W // 2, H // 2))
        hit = 1.0 if i < 3 else 0.25
        layer = split(layer, round(6 + 14 * hit), rng, 6 if i < 3 else 1, 60 if i < 3 else 12)
        opacity = 1.0 if i < total - 3 else (total - i) / 4
        frames.append(fade(layer, 0.95 * opacity))
    write(frames, out / name)
    return {"name": name, "dir": name, "start_s": round(start, 3), "frames": total}


def credits(out: Path, start: float, seconds: float) -> dict:
    card = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    logo = logo_image()
    logo = logo.resize((380, round(logo.height * 380 / logo.width)), Image.LANCZOS)
    card.paste(logo, ((W - logo.width) // 2, 200), logo)
    draw = ImageDraw.Draw(card)
    lines = [("HAL SUPREME  —  SIGNAL SPLIT", 40, "SemiBold", WHITE), ("", 20, "Regular", WHITE),
             ("LYRICS   HAL", 28, "Regular", (200, 200, 210)), ("SONG   MINIMAX MUSIC 3", 28, "Regular", (200, 200, 210)),
             ("PICTURE   FLUX  ·  KLING  ·  OMNIHUMAN", 28, "Regular", (200, 200, 210)),
             ("DIRECTED AND CUT BY   HAL STUDIO", 28, "Regular", (200, 200, 210)), ("", 20, "Regular", WHITE),
             ("RENDERED ON LIVEPEER AGENT", 30, "SemiBold", PINK)]
    y = 200 + logo.height + 60
    for text, size, variation, colour in lines:
        if text:
            face = font(size, variation)
            width, _ = spaced(draw, text, face, size * 0.28)
            draw_spaced(draw, ((W - width) // 2, y), text, face, size * 0.28, colour + (255,))
        y += round(size * 1.9)
    base = np.array(card)
    frames, total = [], round(seconds * FPS)
    for i in range(total):
        t = i / FPS
        frames.append(fade(base, min(1.0, t / 0.6)) if t < 0.6 else base)
    write(frames, out / "credits")
    return {"name": "credits", "dir": "credits", "start_s": round(start, 3), "frames": total, "opaque_after_s": 0.6}


def hook_times(words: list, lines: list) -> list[tuple[str, str, float, float]]:
    """The first hearing of each hook word inside each chorus line window."""
    hits = []
    for line in lines:
        if not line["section"].lower().startswith("chorus") or line["start"] is None:
            continue
        for heard, text in HOOKS:
            if heard not in line["text"].lower().replace("-", " ").split() and heard not in line["text"].lower():
                continue
            for token, a, b in words:
                if token.startswith(heard) and line["start"] - 0.3 <= a <= line["end"] + 0.3:
                    hits.append((f"{text.lower()}_{round(a)}", text, a, b))
                    break
            break
    return hits


def typed_frames(text: str, seconds: float, size: int, y: int, background: bool) -> list[np.ndarray]:
    """A line typed out letter by letter with a blinking cursor, then held; fades out over the last 0.3 s."""
    face = font(size, "SemiLight")
    frames, total = [], round(seconds * FPS)
    typing = min(seconds * 0.55, 0.07 * len(text))
    probe = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    full = probe.textlength(text, font=face)
    for i in range(total):
        t = i / FPS
        shown = text[:min(len(text), int(len(text) * t / typing) + 1)] if typing else text
        card = Image.new("RGBA", (W, H), (0, 0, 0, 255 if background else 0))
        draw = ImageDraw.Draw(card)
        x = round((W - full) / 2)
        draw.text((x, y), shown, font=face, fill=WHITE + (255,))
        if (t < typing or int(t * 2.5) % 2 == 0):
            cursor_x = x + probe.textlength(shown, font=face) + 6
            draw.rectangle([cursor_x, y + size * 0.12, cursor_x + max(3, size // 14), y + size * 1.05], fill=WHITE + (255,))
        array = np.array(card)
        if t > seconds - 0.3 and not background:
            array = fade(array, (seconds - t) / 0.3)
        frames.append(array)
    return frames


def typed(out: Path, name: str, text: str, start: float, seconds: float) -> dict:
    frames = typed_frames(text, seconds, 54, round(H * 0.78), background=False)
    write(frames, out / name)
    return {"name": name, "dir": name, "start_s": round(start, 3), "frames": len(frames)}


def end_card(out: Path, line: str, typed_s: float, credits_s: float) -> dict:
    """Black: the last line typed out, then the credits card. Played after the song as its own clip."""
    frames = typed_frames(line, typed_s, 62, H // 2 - 40, background=True)
    credits(out, 0.0, credits_s)
    folder = out / "endcard"
    write(frames, folder)
    for index, source in enumerate(sorted((out / "credits").glob("*.png"))):
        source.replace(folder / f"{len(frames) + index:04d}.png")
    (out / "credits").rmdir()
    return {"name": "endcard", "dir": "endcard", "frames": len(frames) + round(credits_s * FPS), "seconds": typed_s + credits_s}


def main(words_path: Path, duration: float, out: Path) -> list[dict]:
    rng = random.Random(26)
    data = json.loads(words_path.read_text(encoding="utf-8"))
    events = [title(out, 0.5, 3.9, rng)]
    for name, text, a, b in hook_times(data["words"], data["lines"]):
        events.append(hook(out, name, text, a - 0.04, min(0.9, max(0.5, b - a + 0.35)), rng))
    for line in data["lines"]:  # the whispered question, typed like a thought
        if line["text"].startswith("older voice whispers") and line["start"] is not None:
            events.append(typed(out, "typed_question", "are you still the same?", line["start"] - 0.1, 3.0))
    events.append(end_card(out, "signal split. still me.", 3.0, 4.5))
    (out / "events.json").write_text(json.dumps(events, indent=2) + "\n", encoding="utf-8")
    return events


if __name__ == "__main__":
    print(json.dumps(main(Path(sys.argv[1]), float(sys.argv[2]), Path(sys.argv[3])), indent=1))
