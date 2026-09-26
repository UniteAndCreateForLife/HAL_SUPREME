"""Our Version v1: catalog classes, key and tempo analysis, the artist-name guard, reward, and the learner."""

from __future__ import annotations

import json
import math
import random
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "studio"))
import hal_our_version_v1 as ov  # noqa: E402

try:  # HAL's canonical EventStore lives in the private tree; the learner itself is tested without it
    import hal_cognition.event_store  # noqa: F401
    HAS_EVENTSTORE = True
except ImportError:
    HAS_EVENTSTORE = False


class CatalogTests(unittest.TestCase):
    def test_classes(self):
        cases = {
            "UltravioleNt ShadowS": "own_song",
            "mui zyu - sparky (Official Visualizer)(Cover) (Remastered)": "third_party",
            "Darkman007 - Synthez Brains (Remix)": "third_party",
            "Speak My Mind (Remix)": "own_song",
            "Cinder Prayer - HeartMuLa-3B | HAL SUPREME Music Video": "own_song",
            "HAL - Glass Signal (Night Remix)": "own_song",
            "PLAYFUL COMPUTER - Episode 13": "non_song",
            "THRIFT STORE INTERVIEW (raw)": "non_song",
            "WATCH NOW   THE SHAPE OF SIGNAL   B03 3 MIN 30 SEC PICTURE REVIEW": "hal_review",
        }
        for title, expected in cases.items():
            with self.subTest(title=title):
                self.assertEqual(ov.classify_upload({"title": title, "duration": 200}), expected)
        self.assertEqual(ov.classify_upload({"title": "Beep beep beep", "duration": 20}), "non_song")

    def test_engagement_weights_likes_and_comments(self):
        self.assertEqual(ov.engagement({"view_count": 100, "like_count": 2, "comment_count": 1}), 140)
        self.assertEqual(ov.engagement({"view_count": None}), 0)
        catalog = ov.build_catalog([{"id": "a", "title": "Song A", "duration": 200, "view_count": 10},
                                    {"id": "b", "title": "Song B", "duration": 200, "view_count": 5, "like_count": 3}])
        self.assertEqual([u["id"] for u in catalog["uploads"]], ["b", "a"])
        self.assertEqual(catalog["counts"], {"own_song": 2})


class AnalysisTests(unittest.TestCase):
    def test_key_from_profile(self):
        a_minor = np.roll(ov._MINOR, 9)
        self.assertEqual(ov.estimate_key(a_minor)["key"], "A minor")
        self.assertEqual(ov.estimate_key(np.roll(ov._MAJOR, 7))["key"], "G major")

    def test_tempo_loudness_and_energy_on_a_click_track(self):
        import soundfile as sf

        sr = 22050
        y = np.zeros(sr * 12, dtype=np.float32)
        for beat in np.arange(0, 12, 0.5):  # 120 BPM
            start = int(beat * sr)
            y[start:start + 400] += np.hanning(400).astype(np.float32) * np.sin(np.arange(400) * 0.3).astype(np.float32)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "clicks.wav"
            sf.write(path, y, sr)
            result = ov.analyze_audio(path)
        self.assertAlmostEqual(result["tempo_bpm"], 120, delta=3)
        self.assertEqual(len(result["energy_db_5s"]), 3)
        self.assertTrue(result["lufs_mono"] is None or math.isfinite(result["lufs_mono"]))
        self.assertNotIn("style_vector", result)

    def test_lyric_lines_and_sections(self):
        words = [{"word": w, "start": s, "end": s + 0.3} for w, s in
                 [("hold", 0.0), ("the", 0.4), ("line", 0.8), ("hold", 2.0), ("the", 2.4), ("line", 2.8)]]
        self.assertEqual(ov.lyric_lines_from_words(words), ["hold the line", "hold the line"])
        timed = [("rain", 0.0, 0.3), ("falls", 0.35, 0.6), ("again", 2.0, 2.4)]  # hal_lyric_timeline_v1.TimedWord
        self.assertEqual(ov.lyric_lines_from_words(timed), ["rain falls", "again"])
        tagged = ov.tag_sections(["a", "b", "c", "d", "hook", "hook", "hook", "e"])
        self.assertTrue(tagged.startswith("[Verse]"))
        self.assertIn("[Chorus]\nhook\nhook\nhook\ne", tagged)
        # A transcriber hears the same chorus line slightly differently each time.
        sung = ["rain on the window", "cold light in the hall", "a door i never opened", "the last train home",
                "the glass remembers remember", "i feel the signal", "the glass remembers, remember me", "i feel the signal now"]
        fuzzy = ov.tag_sections(sung)
        self.assertTrue(fuzzy.startswith("[Verse]\nrain on the window"))
        self.assertIn("[Chorus]\nthe glass remembers remember", fuzzy)
        self.assertEqual(fuzzy.count("[Chorus]"), 1)


class BriefTests(unittest.TestCase):
    ANALYSIS = {"tempo_bpm": 140.2, "key": {"key": "F# minor"}, "duration_s": 200,
                "style_tags": [["whispered vocals", 0.54], ["dubstep", 0.46], ["darkwave", 0.40], ["euphoric", 0.40]]}

    def test_brief_uses_original_words(self):
        picked = {"vocal": "whispered close-mic lead", "texture": "detuned synth pads",
                  "drums": "half-time dubstep drums", "arc": "slow build to a heavy drop"}
        brief = ov.build_brief("song", self.ANALYSIS, picked, banned=["bladee", "skrillex"], seconds=180)
        self.assertIn("140 BPM", brief["prompt"])
        self.assertIn("F# minor", brief["prompt"])
        self.assertIn("dubstep", brief["prompt"])
        self.assertEqual(brief["context"], "dubstep")
        self.assertEqual(brief["seconds"], 180)

    def test_structure_gives_the_production_room(self):
        lyrics = "[verse]\na\n\n[verse]\nb\n\n[verse]\nc\n\n[verse]\nd\n\n[verse]\ne"
        drops = ov.arrange_lyrics(lyrics, "instrumental drops between sections")
        self.assertEqual(drops.count("[instrumental]"), 2)
        self.assertFalse(drops.endswith("[instrumental]"))
        self.assertTrue(ov.arrange_lyrics(lyrics, "instrumental intro and outro").startswith("[intro]"))
        self.assertEqual(ov.arrange_lyrics(lyrics, "vocal-forward song"), lyrics)
        picked = {"vocal": "whispered close-mic lead", "texture": "detuned synth pads", "drums": "half-time dubstep drums",
                  "arc": "slow build to a heavy drop", "structure": "instrumental drops between sections"}
        brief = ov.build_brief("song", self.ANALYSIS, picked, banned=[], lyrics=lyrics)
        prompt = brief["prompt"]
        self.assertLess(prompt.index("half-time dubstep drums"), prompt.index("whispered close-mic lead"))
        self.assertIn("production-led", prompt)
        self.assertIn("[instrumental]", brief["lyrics"])

    def test_artist_names_are_refused(self):
        picked = {"vocal": "a lead in the style of Bladee"}
        with self.assertRaises(ValueError):
            ov.build_brief("song", self.ANALYSIS, picked, banned=["bladee"])
        # The owner's lyrics may name people; only the prompt, which steers the sound, is guarded.
        brief = ov.build_brief("song", self.ANALYSIS, {"vocal": "x"}, banned=["drake"], lyrics="call me Drake tonight")
        self.assertEqual(brief["lyrics"], "call me Drake tonight")
        # A name inside another word is not a match.
        ov.refuse_names("drakes and dragons", ["drake"])


class RestoreTests(unittest.TestCase):
    RAW = ("[Verse]\ni am the signal\nevery system bends when i speak through it\nthe dedicists corrupt them when i feel too much\n"
           "[Verse]\ni am the signal\nevery silence cracks when i breathe through it")

    def test_small_repairs_pass(self):
        repaired = ("[chorus]\ni am the signal\nevery system bends when i speak through it\n[verse]\nthe decisions corrupt them "
                    "when i feel too much\n[chorus]\ni am the signal\nevery silence cracks when i breathe through it")
        result = ov.restore_lyrics(self.RAW, lambda s, u: json.dumps({"lyrics": repaired, "changed": [{"from": "dedicists", "to": "decisions"}]}))
        self.assertTrue(result["restored"])
        self.assertIn("[chorus]", result["lyrics"])
        self.assertGreater(result["similarity"], 0.9)

    def test_rewrites_are_rejected(self):
        rewritten = "[verse]\nwe rise tonight\nhands up to the sky\nnothing can stop us now\n[chorus]\nwe rise tonight"
        result = ov.restore_lyrics(self.RAW, lambda s, u: json.dumps({"lyrics": rewritten}))
        self.assertFalse(result["restored"])
        self.assertEqual(result["lyrics"], self.RAW)

    def test_model_failure_keeps_the_raw_words(self):
        def broken(system, user):
            raise RuntimeError("502")

        self.assertEqual(ov.restore_lyrics(self.RAW, broken)["lyrics"], self.RAW)


class ItemsTests(unittest.TestCase):
    def test_parse_items(self):
        self.assertEqual(ov.parse_items(None, None, ["a=C:/x.wav", "b = D:/y z.wav"]),
                         [("a", Path("C:/x.wav")), ("b", Path("D:/y z.wav"))])
        self.assertEqual(ov.parse_items("s.wav", "s", None), [("s", Path("s.wav"))])
        for bad in (["nopath"], ["=x.wav"], ["a="]):
            with self.assertRaises(ValueError):
                ov.parse_items(None, None, bad)
        with self.assertRaises(ValueError):
            ov.parse_items(None, None, None)


class ScoreTests(unittest.TestCase):
    def test_catalog_rank(self):
        catalog = {"a": [1.0, 0.0, 0.0], "b": [0.0, 1.0, 0.0], "c": [0.7, 0.7, 0.0]}
        self.assertEqual(ov.catalog_rank([0.9, 0.1, 0.0], "a", catalog), 1)
        self.assertEqual(ov.catalog_rank([0.6, 0.8, 0.0], "a", catalog), 3)
        self.assertIsNone(ov.catalog_rank([1.0, 0.0, 0.0], "missing", catalog))

    def test_reward_orders_and_gates(self):
        strong = ov.reward(0.86, rank=1, take_wer=0.15, original_wer=0.12, lufs=-14.2)
        weak = ov.reward(0.48, rank=7, take_wer=0.40, original_wer=0.12, lufs=-9.0)
        self.assertTrue(strong["pass"])
        self.assertFalse(weak["pass"])
        self.assertGreater(strong["reward"], 0.9)
        self.assertLess(weak["reward"], 0.1)
        self.assertFalse(ov.reward(0.86, rank=2)["pass"])  # closer to another of the owner's songs than to its own original
        self.assertFalse(ov.reward(0.74, rank=1)["pass"])
        self.assertAlmostEqual(ov.reward(0.70)["reward"], 0.5)  # only style known: (0.70 - 0.50) / 0.40

    def test_a_remix_off_the_beat_never_passes(self):
        on_time = ov.reward(0.80, rank=1, in_time=True)
        drifting = ov.reward(0.80, rank=1, in_time=False)
        self.assertTrue(on_time["pass"])
        self.assertFalse(drifting["pass"])
        self.assertLess(drifting["reward"], 0.5)
        self.assertEqual(ov.reward(0.80, rank=1)["pass"], True)  # a generated song has no fit to check

    def test_receipt_metrics_read_the_selected_candidate(self):
        receipt = {"selection": {"selected": "user_voice_double"},
                   "candidates": {"user_voice_double": {"lyrics": {"reached_word_error_rate": 0.151},
                                                        "mastering": {"measurement": {"output_i": "-13.52"}}},
                                  "user_voice": {"lyrics": {"reached_word_error_rate": 0.9}}}}
        self.assertEqual(ov.receipt_metrics(receipt), (0.151, -13.52, "user_voice_double"))
        self.assertEqual(ov.receipt_metrics({}), (None, None, None))


class LearnerTests(unittest.TestCase):
    def test_learner_prefers_rewarded_choices_per_context(self):
        learner = ov.Learner()
        winning = {"vocal": "whispered close-mic lead", "texture": "detuned synth pads",
                   "drums": "half-time dubstep drums", "arc": "slow build to a heavy drop",
                   "structure": "instrumental drops between sections"}
        for _ in range(20):
            learner.update("dubstep", winning, 1.0)
        for dimension, options in ov.CHOICES.items():
            for option in options:
                if option != winning[dimension]:
                    learner.update("dubstep", {dimension: option}, 0.0, weight=3)
        rng = random.Random(7)
        picks = [learner.sample("dubstep", rng)["vocal"] for _ in range(200)]
        self.assertGreater(picks.count("whispered close-mic lead"), 180)
        other_context = [learner.sample("darkwave", rng)["vocal"] for _ in range(200)]
        self.assertLess(other_context.count("whispered close-mic lead"), 120)  # nothing learned for darkwave yet

    @unittest.skipUnless(HAS_EVENTSTORE, "needs HAL EventStore (private tree)")
    def test_owner_verdict_outweighs_a_score_and_replays_from_events(self):
        from hal_cognition.event_store import EventStore

        with tempfile.TemporaryDirectory() as tmp:
            store = EventStore(db_path=Path(tmp) / "events.db")
            choices = {"vocal": "stacked falsetto hook"}
            ov.record(store, "our_version.reward", ov.LEARNER_SUBJECT,
                      {"kind": "reward", "song_id": "s", "context": "trap", "choices": choices, "reward": 0.9, "weight": 1.0})
            ov.record(store, "our_version.verdict", ov.LEARNER_SUBJECT,
                      {"kind": "verdict", "song_id": "s", "context": "trap", "choices": choices, "reward": 0.0, "weight": 3.0})
            ov.record(store, "our_version.analyzed", "s", {"song_id": "s"})  # other subjects are not learning events
            learner = ov.learner_from_store(store)
            store.close()
        alpha, beta = learner.stats[ov.Learner.key("trap", "vocal", "stacked falsetto hook")]
        self.assertAlmostEqual(alpha, 1.9)
        self.assertAlmostEqual(beta, 4.1)  # the owner's reject (weight 3) outweighs the 0.9 score

    def test_a_rescore_replaces_the_earlier_score_for_the_same_take(self):
        events = [{"payload": {"kind": "reward", "take_sha256": "abc", "context": "dubstep", "choices": {"engine": "remix"}, "reward": 0.8}},
                  {"payload": {"kind": "reward", "take_sha256": "abc", "context": "dubstep", "choices": {"engine": "remix"}, "reward": 0.2}}]
        alpha, beta = ov.Learner.from_events(events).stats[ov.Learner.key("dubstep", "engine", "remix")]
        self.assertAlmostEqual(alpha, 1.2)
        self.assertAlmostEqual(beta, 1.8)


if __name__ == "__main__":
    unittest.main()
