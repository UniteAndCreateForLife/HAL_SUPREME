"""Remix v1: tempo and key matching, phrase alignment, the beat prompt guard, and the mix graph."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "studio"))
import hal_remix_v1 as rx  # noqa: E402


class MatchTests(unittest.TestCase):
    def test_period_ratio_folds_half_and_double_time(self):
        self.assertAlmostEqual(rx.normalized_period_ratio(0.5, 0.5), 1.0)
        self.assertAlmostEqual(rx.normalized_period_ratio(0.5, 60 / 143.584), 0.5 / (60 / 143.584))
        self.assertAlmostEqual(rx.normalized_period_ratio(1.0, 0.5), 1.0)  # half time already fits
        self.assertAlmostEqual(rx.normalized_period_ratio(0.25, 0.5), 1.0)  # double time already fits
        self.assertAlmostEqual(rx.tempo_drift_ms(0.5 * 1.001, 0.5, 200.0), 200.0, places=3)  # 0.1% walks 200 ms in 200 s

    def test_semitone_shift(self):
        self.assertEqual(rx.semitone_shift("C minor", "D minor"), 2)
        self.assertEqual(rx.semitone_shift("D minor", "C minor"), -2)
        self.assertEqual(rx.semitone_shift("F# minor", "C minor"), -6)
        self.assertEqual(rx.semitone_shift("C major", "A minor"), 0)  # relative keys share their notes
        self.assertEqual(rx.semitone_shift("A minor", "C major"), 0)
        self.assertEqual(rx.semitone_shift("G major", "A minor"), 5)  # G major up to C major, A minor's relative

    def test_period_from_beats_is_precise_and_robust(self):
        period = 60 / 119.8
        beats = np.arange(200) * period + 0.37
        beats = np.delete(beats, [40, 41, 120])  # skipped beats
        beats = np.sort(np.append(beats, [beats[60] + period / 2]))  # one doubled beat
        estimate = rx.period_from_beats(beats + np.random.default_rng(1).normal(0, 0.004, len(beats)))
        self.assertAlmostEqual(60 / estimate, 119.8, delta=0.1)
        self.assertIsNone(rx.period_from_beats(np.array([0.0, 0.5, 1.0])))

    def test_grid_phase_and_steadiness(self):
        period = 60 / 143.584
        steady = np.arange(300) * period + 0.21
        p, phase, rms = rx.grid_from_beats(steady)
        self.assertAlmostEqual(p, period, places=6)
        self.assertAlmostEqual(phase, 0.21, places=6)
        self.assertLess(rms, 1e-6)
        wandering = steady + 0.03 * np.sin(np.arange(300) / 12)  # a generated beat that speeds up and slows down
        self.assertGreater(rx.grid_from_beats(wandering)[2] * 1000, 15)

    def test_timing_gate_ignores_breakdowns_but_catches_drift(self):
        period = 60 / 143.584
        beats = np.arange(430) * period + 0.2
        rng = np.random.default_rng(4)
        strengths = np.ones(len(beats)) * 5.0
        breakdown = (beats > 80) & (beats < 100)
        strengths[breakdown] = 0.5  # no drums: the tracker wanders here
        jittered = beats + rng.normal(0, 0.004, len(beats))
        jittered[breakdown] += rng.normal(0, 0.08, breakdown.sum())
        steady = rx.window_offsets(jittered, strengths, period, 0.2)
        self.assertTrue(rx.timing_ok(steady), steady)
        drifting = np.arange(430) * period * 1.002 + 0.2  # 0.2% fast: about 360 ms late by the end
        report = rx.window_offsets(drifting, np.ones(430), period, 0.2)
        self.assertFalse(rx.timing_ok(report), report)
        self.assertFalse(rx.timing_ok(rx.window_offsets(beats[:10], np.ones(10), period, 0.2)))  # too little to judge
        late = rx.window_offsets(beats + 0.06, np.ones(430), period, 0.2)  # steady but 60 ms behind the vocal
        self.assertEqual(late["spread_ms"], 0.0)
        self.assertFalse(rx.timing_ok(late))
        sloppy = rx.window_offsets(beats + rng.normal(0, 0.05, 430), np.ones(430), period, 0.2)  # on average right, never tight
        self.assertFalse(rx.timing_ok(sloppy), sloppy)
        long_break = np.ones(430) * 5.0
        long_break[(beats > 60) & (beats < 95)] = 0.5
        wander = beats + rng.normal(0, 0.003, 430)
        wander[(beats > 60) & (beats < 95)] += rng.normal(0, 0.09, ((beats > 60) & (beats < 95)).sum())
        self.assertTrue(rx.timing_ok(rx.window_offsets(wander, long_break, period, 0.2)))  # a drumless stretch is left out

    def test_offset_candidates_step_by_beats_around_the_nearest_phase(self):
        candidates = rx.bar_offset_candidates(reference_phase=0.10, candidate_phase=0.35, period=0.5, bars=1)
        self.assertIn(-0.25, candidates)
        self.assertEqual(len(candidates), 5)
        self.assertEqual(sorted(candidates), candidates)
        self.assertTrue(all(abs(round((c + 0.25) / 0.5) * 0.5 - (c + 0.25)) < 1e-9 for c in candidates))

    def test_correlation_prefers_the_true_delay(self):
        rng = np.random.default_rng(9)
        reference = rng.random(1000)
        candidate = reference[25:]  # runs 25 frames early: delaying it by 25 lines it up
        self.assertGreater(rx.correlation_at(reference, candidate, 25), rx.correlation_at(reference, candidate, 0))

    def test_best_offset_finds_the_delay(self):
        rng = np.random.default_rng(3)
        reference = rng.random(400)
        delayed = np.concatenate([np.zeros(12), reference[:-12]])  # candidate runs 12 frames late
        self.assertEqual(rx.best_offset(reference, delayed, max_lag=40), -12)
        early = reference[7:]
        self.assertEqual(rx.best_offset(reference, early, max_lag=40), 7)


class PromptAndMixTests(unittest.TestCase):
    def test_beat_prompt_carries_tempo_key_and_no_vocals(self):
        prompt = rx.beat_prompt({"tempo_bpm": 139.7, "key": {"key": "F minor"}}, ["dark bass music", "eerie"],
                                "half-time drums")
        self.assertIn("instrumental only, no vocals", prompt)
        self.assertIn("140 BPM", prompt)
        self.assertIn("F minor", prompt)

    def test_balance_puts_the_beat_under_the_vocal(self):
        self.assertEqual(rx.balance_beat_db(-20.0, -12.0), -12.0)  # beat 8 LU hot: pull it 12 dB down to sit 4 LU under
        self.assertEqual(rx.balance_beat_db(-20.0, -30.0), 6.0)  # clamped boost
        self.assertEqual(rx.balance_beat_db(None, -12.0), -3.0)
        self.assertEqual(rx.balance_beat_db(-20.0, float("-inf")), -3.0)

    def test_mute_spans_silences_only_the_listed_words(self):
        graph = rx.mute_spans([(109.2, 109.5), (39.7, 40.0)])
        self.assertEqual(graph.count("volume=0"), 2)
        self.assertLess(graph.index("39.640"), graph.index("109.140"))  # sorted, padded 60 ms each side
        self.assertIn("between(t,39.640,40.060)", graph)
        self.assertEqual(rx.mute_spans([]), "anull")

    def test_mix_graph_ducks_the_beat_under_the_vocal(self):
        graph = rx.mix_filter(0.0, -3.0)
        self.assertIn("sidechaincompress", graph)
        self.assertIn("[beat][key]sidechaincompress", graph)
        self.assertIn("amix=inputs=2:duration=first", graph)
        self.assertTrue(graph.endswith("[out]"))


if __name__ == "__main__":
    unittest.main()
