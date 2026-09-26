"""Build the SIGNAL SPLIT music-video EDL: shots cut on bar lines, assigned by song section.

Usage: python tools/build_signal_split_edl.py <song.wav> <lyrics.txt> <out_edl.json> [performance_spans.json]

The song's beat grid comes from hal_remix_v1.beat_grid (a least-squares line through every beat). A grid faster than
130 BPM is read as double time, so a bar is eight tracked beats. Section boundaries come from hal_lyric_timeline_v1
(Whisper word times aligned to the lyrics) and snap to the nearest bar line; the downbeat is the beat that puts the
section starts closest to bar lines. Every cut lands on a bar line, no cut is longer than a shot, a shot never follows
itself, and the last cut is always the closing shot, aligned so its collapse to black ends with the song.
The slow analysis (stem split and transcription) is cached next to the EDL as <name>.analysis.json."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# hal_remix_v1 (beat grid) ships in the public studio folder; the stem split and lyric alignment are HAL modules named by
# HAL_SCRIPTS and only needed when no cached analysis sits next to the EDL.
for _extra in (os.environ.get("HAL_SCRIPTS"), str(Path(__file__).resolve().parents[3] / "studio")):
    if _extra and Path(_extra).is_dir():
        sys.path.insert(0, _extra)

SHOTS_DIR = Path(__file__).resolve().parents[1] / "shots"
CLIP_S = 7.04  # every Kling shot is 7.04 s long
MAX_CUT_S = 6.9  # headroom inside a shot
MIN_CUT_S = 1.2  # shorter pieces merge into a neighbour
CLOSER = "V12"  # the CRT collapsing to black; always the last cut
CLOSER_MIN_S = 3.0  # long enough for the collapse to read
# (section, occurrence) -> shots in order, one per lyric couplet (verse) or line (chorus)
SHOTS = {
    ("intro", 0): ["V01", "V10", "V08"],
    ("verse", 0): ["V02", "V03", "V04", "V06"],  # mirror lagging / sink / cracked vinyl / split-self
    ("chorus", 0): ["V05", "V06", "V11", "V07", "V04"],  # street / shatter-frame / static / signal answers
    ("verse", 1): ["V08", "V09", "V10", "V07"],  # binary rain / ghost in the haze / older voice / a dozen you and me
    ("chorus", 1): ["V05", "V11", "V07", "V06", "V02"],  # the 4th line lands on the cracked mirror, not the TV wall again
    ("outro", 0): ["V11", "V01"],
}
BARS_PER_CUT = {"chorus": 1}  # everything else cuts every two bars


def shots_for(label: str, occurrence: int) -> list[str]:
    if (label, occurrence) in SHOTS:
        return SHOTS[(label, occurrence)]
    known = sorted(n for (name, n) in SHOTS if name == label)
    return SHOTS[(label, known[-1])] if known else SHOTS[("verse", 1)]


def beats_per_bar(grid: dict) -> int:
    return 8 if 60.0 / grid["period_s"] > 130 else 4


def bar_lines(grid: dict, duration: float, anchors: list[float]) -> list[float]:
    """Bar lines across the song; the downbeat is the beat that puts the anchors closest to a bar line."""
    period, beats = grid["period_s"], beats_per_bar(grid)
    bar = beats * period

    def lines(offset: int) -> list[float]:
        first = (grid["phase_s"] + offset * period) % bar
        return [first + k * bar for k in range(int(duration / bar) + 2) if first + k * bar < duration]

    def cost(offset: int) -> float:
        marks = lines(offset)
        return sum(min(abs(anchor - mark) for mark in marks) for anchor in anchors) if anchors and marks else 0.0

    return lines(min(range(beats), key=cost))


def merge_sections(spans: list) -> list[tuple[str, float, float]]:
    merged: list[tuple[str, float, float]] = []
    for label, start, end in spans:
        label = label.lower().split()[0]
        if merged and merged[-1][0] == label:
            merged[-1] = (label, merged[-1][1], float(end))
        else:
            merged.append((label, float(start), float(end)))
    return merged


def snap_sections(spans: list[tuple[str, float, float]], bars: list[float], duration: float) -> list[tuple[str, float, float]]:
    """Section starts moved to the nearest bar line within half a bar; the first starts at 0, the last ends with the song."""
    bar = bars[1] - bars[0] if len(bars) > 1 else duration
    starts = [0.0]
    for _, start, _ in spans[1:]:
        nearest = min(bars, key=lambda mark: abs(mark - start)) if bars else start
        starts.append(nearest if abs(nearest - start) <= bar / 2 else start)
    ends = starts[1:] + [duration]
    return [(label, a, b) for (label, _, _), a, b in zip(spans, starts, ends) if b - a > 1e-3]


def pieces(start: float, end: float, bars: list[float], per_cut: int) -> list[tuple[float, float]]:
    """[start, end) cut every per_cut bar lines; short pieces merge into a neighbour, long ones split at a bar line."""
    inner = [mark for mark in bars if start + 1e-3 < mark < end - 1e-3]
    points = [start] + inner + [end]
    marks = points[::per_cut]
    if marks[-1] != end:
        marks.append(end)
    out = [[a, b] for a, b in zip(marks, marks[1:])]
    index = 0
    while index < len(out):  # merge short pieces
        a, b = out[index]
        if b - a < MIN_CUT_S and len(out) > 1:
            if index > 0 and out[index][1] - out[index - 1][0] <= MAX_CUT_S:
                out[index - 1][1] = b
                del out[index]
                continue
            if index + 1 < len(out):
                out[index + 1][0] = a
                del out[index]
                continue
        index += 1
    result: list[tuple[float, float]] = []
    for a, b in out:  # split long pieces at the bar line nearest their middle
        stack = [(a, b)]
        while stack:
            a, b = stack.pop()
            if b - a <= MAX_CUT_S:
                result.append((a, b))
                continue
            candidates = [mark for mark in bars if a + MIN_CUT_S < mark < b - MIN_CUT_S]
            middle = min(candidates, key=lambda mark: abs(mark - (a + b) / 2)) if candidates else (a + b) / 2
            stack += [(middle, b), (a, middle)]
    return result


def plan(duration: float, grid: dict, spans: list) -> list[dict]:
    """The cut list for one song: contiguous cuts from 0 to the song's end."""
    sections = merge_sections(spans)
    bars = bar_lines(grid, duration, [start for _, start, _ in sections[1:]])
    timeline, seen = [], {}
    for label, start, end in snap_sections(sections, bars, duration):
        occurrence = seen.get(label, 0)
        seen[label] = occurrence + 1
        for a, b in pieces(start, end, bars, BARS_PER_CUT.get(label, 2)):
            timeline.append((label, occurrence, a, b))
    if len(timeline) > 1 and timeline[-1][3] - timeline[-1][2] < CLOSER_MIN_S:  # give the closing shot room
        (label, occurrence, a, _), (_, _, _, end) = timeline[-2], timeline[-1]
        room = [mark for mark in bars if a + MIN_CUT_S <= mark and CLOSER_MIN_S <= end - mark <= MAX_CUT_S]
        if room:
            timeline[-2:] = [(label, occurrence, a, max(room)), (timeline[-1][0], timeline[-1][1], max(room), end)]
        elif end - a <= MAX_CUT_S:
            timeline[-2:] = [(timeline[-1][0], timeline[-1][1], a, end)]
    cuts, offsets, turn = [], {}, {}
    previous = None
    for index, (label, occurrence, a, b) in enumerate(timeline):
        length = b - a
        if index == len(timeline) - 1:
            shot, in_s = CLOSER, max(0.0, CLIP_S - 0.05 - length)  # the collapse lands on the song's end
        else:
            options = [shot for shot in shots_for(label, occurrence) if shot != CLOSER]
            step = turn.get((label, occurrence), 0)
            shot = options[step % len(options)]
            if shot == previous and len(options) > 1:
                step += 1
                shot = options[step % len(options)]
            turn[(label, occurrence)] = step + 1
            in_s = offsets.get(shot, 0.0)
            if in_s + length > MAX_CUT_S:  # reuse: take the tail of the shot rather than repeat its opening
                in_s = max(0.0, CLIP_S - 0.05 - length)
            offsets[shot] = in_s + length
        previous = shot
        cuts.append({"id": f"{index + 1:02d}_{label}", "section": label, "occurrence": occurrence,
                     "start_s": round(a, 3), "end_s": round(b, 3), "source": f"../shots/{shot}.mp4", "in_s": round(in_s, 3)})
    for before, after in zip(cuts, cuts[1:]):  # rounding must not open gaps
        before["end_s"] = after["start_s"]
    cuts[-1]["end_s"] = round(duration, 3)
    return cuts


def analyze(song: Path, lyrics: str, cache: Path) -> dict:
    if cache.exists():
        cached = json.loads(cache.read_text(encoding="utf-8"))
        if cached.get("song_bytes") == song.stat().st_size:
            return cached
        try:  # a re-encoded copy of the same take: keep the committed analysis unless HAL's analysers are here
            import hal_lyric_timeline_v1  # noqa: F401
        except ImportError:
            print(f"note: {song.name} differs in size from the analysed take; using the committed analysis", file=sys.stderr)
            return cached
    from hal_lyric_timeline_v1 import lyric_timeline, transcribe_words
    from hal_remix_v1 import beat_grid
    from hal_voice_clone_pipeline import separate

    import soundfile

    info = soundfile.info(str(song))
    duration = round(info.frames / info.samplerate, 3)
    timeline = lyric_timeline(lyrics, transcribe_words(Path(separate(song))))
    runs: list[tuple[str, float]] = []
    for line in timeline:
        if line.get("start") is None:
            continue
        label = line["section"].lower().split()[0]
        if not runs or runs[-1][0] != label:
            runs.append((label, float(line["start"])))
    spans = [(label, start, runs[i + 1][1] if i + 1 < len(runs) else duration) for i, (label, start) in enumerate(runs)]
    result = {"song_bytes": song.stat().st_size, "duration_s": duration, "beat_grid": beat_grid(song), "sections": spans}
    cache.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def perform(cuts: list[dict], spans: list[dict], tolerance: float = 0.02) -> list[dict]:
    """Swap B-roll cuts for lip-synced performance where a performance clip covers them.

    A span's clip was rendered from the vocal stem starting at file_offset_s of song time, so a cut at song time T plays
    the clip from T - file_offset_s and the mouth stays on the words. `replace` picks which of the cuts inside the span
    become performance: first, last, odd (1st, 3rd, ...), even (2nd, 4th, ...), all, or a list of positions. Cut boundaries never move."""
    out = [dict(cut) for cut in cuts]
    for span in spans:
        inside = [i for i, cut in enumerate(out) if cut["start_s"] >= span["start_s"] - tolerance
                  and cut["end_s"] <= span["end_s"] + tolerance]
        rule = span["replace"]
        if isinstance(rule, list):  # explicit positions among the cuts inside the span, e.g. [1] for a second camera angle
            pick = [inside[k] for k in rule if 0 <= k < len(inside)]
        else:
            pick = {"first": inside[:1], "last": inside[-1:], "odd": inside[::2], "even": inside[1::2], "all": inside}[rule]
        for i in pick:
            out[i]["source"] = span["source"]
            out[i]["in_s"] = round(out[i]["start_s"] - span["file_offset_s"], 3)
            out[i]["performance"] = span["name"]
    return out


def build(song: Path, lyrics: str, out: Path, spans: list[dict] | None = None) -> dict:
    out.parent.mkdir(parents=True, exist_ok=True)
    analysis = analyze(song, lyrics, out.with_suffix(".analysis.json"))
    cuts = plan(analysis["duration_s"], analysis["beat_grid"], analysis["sections"])
    if spans:
        cuts = perform(cuts, spans)
    edl = {"song": Path(os.path.relpath(song.resolve(), out.parent.resolve())).as_posix(), "duration_s": analysis["duration_s"], "fps": 24,
           "width": 1920, "height": 1080, "cuts": cuts, "overlays": [], "beat_grid": analysis["beat_grid"],
           "sections": analysis["sections"]}
    out.write_text(json.dumps(edl, indent=2) + "\n", encoding="utf-8")
    return edl


if __name__ == "__main__":
    song, lyrics_path, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    lyrics = "\n".join(line for line in lyrics_path.read_text(encoding="utf-8").splitlines()
                       if line.strip() and not line.startswith(("SIGNAL SPLIT", "Lyrics:", "a few lines")))
    performance = json.loads(Path(sys.argv[4]).read_text(encoding="utf-8"))["spans"] if len(sys.argv) > 4 else None
    edl = build(song, lyrics, out, performance)
    print(json.dumps({"cuts": len(edl["cuts"]), "bpm": edl["beat_grid"]["bpm"], "sections": edl["sections"],
                      "performance_cuts": sum(1 for cut in edl["cuts"] if cut.get("performance"))}))
