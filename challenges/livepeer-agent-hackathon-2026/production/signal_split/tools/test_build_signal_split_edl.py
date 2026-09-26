"""Cut-list rules for the SIGNAL SPLIT music video. Run: python -m pytest tools/test_build_signal_split_edl.py -q"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_signal_split_edl as edl  # noqa: E402

SPANS = [("intro", 0.0, 1.4), ("intro", 1.4, 18.7), ("verse", 18.7, 44.1), ("chorus", 44.1, 57.6),
         ("verse", 57.6, 79.3), ("chorus", 79.3, 92.9), ("outro", 92.9, 103.3)]


def grid(bpm: float, phase: float = 0.21) -> dict:
    return {"bpm": bpm, "period_s": 60.0 / bpm, "phase_s": phase}


def check(cuts: list[dict], duration: float) -> None:
    assert cuts[0]["start_s"] == 0.0 and cuts[-1]["end_s"] == round(duration, 3)
    for before, after in zip(cuts, cuts[1:]):
        assert before["end_s"] == after["start_s"]
        assert before["source"] != after["source"], (before["id"], after["id"])
    for cut in cuts:
        length = cut["end_s"] - cut["start_s"]
        assert edl.MIN_CUT_S - 1e-6 <= length <= edl.MAX_CUT_S + 1e-6 or cut is cuts[0], cut
        assert cut["in_s"] + length <= edl.CLIP_S + 1e-6, cut
    assert cuts[-1]["source"].endswith(f"{edl.CLOSER}.mp4")


def test_slow_song_never_asks_a_shot_for_more_than_it_has():
    cuts = edl.plan(86.46, grid(85.37), [("intro", 0.0, 11.8), ("verse", 11.8, 34.3), ("chorus", 34.3, 46.3),
                                         ("verse", 46.3, 68.1), ("chorus", 68.1, 80.6), ("outro", 80.6, 86.46)])
    check(cuts, 86.46)


def test_double_time_grid_cuts_on_half_time_bars():
    fast = grid(171.81)
    cuts = edl.plan(103.329, fast, SPANS)
    check(cuts, 103.329)
    bar = 8 * fast["period_s"]
    lines = edl.bar_lines(fast, 103.329, [s for _, s, _ in edl.merge_sections(SPANS)[1:]])
    assert abs((lines[1] - lines[0]) - bar) < 1e-9
    for cut in cuts[1:]:
        assert min(abs(cut["start_s"] - mark) for mark in lines) < 0.002, cut


def test_repeated_section_labels_merge_into_one_intro():
    merged = edl.merge_sections(SPANS)
    assert [label for label, _, _ in merged] == ["intro", "verse", "chorus", "verse", "chorus", "outro"]
    assert merged[0][1] == 0.0 and merged[0][2] == 18.7


def test_closing_shot_ends_with_the_song():
    cuts = edl.plan(90.349, grid(87.1), [("intro", 0.0, 13.1), ("verse", 13.1, 33.78), ("chorus", 33.78, 45.5),
                                         ("verse", 45.5, 67.16), ("chorus", 67.16, 78.6), ("outro", 78.6, 90.349)])
    last = cuts[-1]
    assert abs(last["in_s"] + (last["end_s"] - last["start_s"]) - (edl.CLIP_S - 0.05)) < 0.01


def test_slow_tempo_two_bar_pieces_are_split_to_fit_a_shot():
    slow = grid(64.0)  # a bar is 3.75 s, so two bars would ask a 7.04 s shot for 7.5 s
    cuts = edl.plan(80.0, slow, [("intro", 0.0, 15.0), ("verse", 15.0, 45.0), ("chorus", 45.0, 60.0),
                                 ("outro", 60.0, 80.0)])
    check(cuts, 80.0)


def test_a_shot_never_follows_itself_across_a_section_boundary(monkeypatch):
    monkeypatch.setitem(edl.SHOTS, ("verse", 0), ["V02", "V03"])
    monkeypatch.setitem(edl.SHOTS, ("chorus", 0), ["V03", "V05"])
    cuts = edl.plan(40.0, grid(90.0, 0.0), [("verse", 0.0, 10.67), ("chorus", 10.67, 32.0), ("outro", 32.0, 40.0)])
    check(cuts, 40.0)


def test_closing_shot_gets_room_to_collapse():
    # take A: the outro's last bar line leaves the closer only 1.26 s unless the boundary moves back a bar
    cuts = edl.plan(86.46, grid(85.37), [("intro", 0.0, 11.8), ("verse", 11.8, 34.3), ("chorus", 34.3, 46.3),
                                         ("verse", 46.3, 68.1), ("chorus", 68.1, 80.6), ("outro", 80.6, 86.46)])
    check(cuts, 86.46)
    assert cuts[-1]["end_s"] - cuts[-1]["start_s"] >= edl.CLOSER_MIN_S


def test_performance_cuts_play_the_clip_at_the_song_time_they_cover():
    cuts = edl.plan(103.329, grid(171.81), SPANS)
    spans = [{"name": "P", "source": "../performance/P.mp4", "start_s": 43.69, "end_s": 57.66, "file_offset_s": 43.44,
              "replace": "odd"}]
    out = edl.perform(cuts, spans)
    inside = [c for c in out if c["start_s"] >= 43.67 and c["end_s"] <= 57.68]
    assert inside and [bool(c.get("performance")) for c in inside] == [i % 2 == 0 for i in range(len(inside))]
    for cut in inside[::2]:
        assert cut["source"].endswith("P.mp4") and abs(cut["in_s"] - (cut["start_s"] - 43.44)) < 1e-6
    assert [(c["start_s"], c["end_s"]) for c in out] == [(c["start_s"], c["end_s"]) for c in cuts]  # boundaries never move
    assert all(not c.get("performance") for c in out if c["end_s"] <= 43.67 or c["start_s"] >= 57.68)
