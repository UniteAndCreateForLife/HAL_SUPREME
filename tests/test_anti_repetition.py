import unittest

from hal_studio.anti_repetition import PriorShotSimilarity, evaluate_repetition


class AntiRepetitionTests(unittest.TestCase):
    def test_first_shot_passes(self):
        self.assertTrue(evaluate_repetition([]).accepted)

    def test_near_duplicate_is_rejected(self):
        d = evaluate_repetition([
            PriorShotSimilarity("shot-011", 0.98, 0.96, 0.95)
        ])
        self.assertFalse(d.accepted)
        self.assertEqual(d.nearest_shot_id, "shot-011")
        self.assertTrue(d.failures[0].startswith("near_duplicate:shot-011"))

    def test_same_character_new_composition_and_motion_passes(self):
        d = evaluate_repetition([
            PriorShotSimilarity("shot-011", 0.97, 0.60, 0.55)
        ])
        self.assertTrue(d.accepted)

    def test_intentional_callback_bypasses_repetition_rejection(self):
        d = evaluate_repetition([
            PriorShotSimilarity("shot-004", 1.0, 1.0, 1.0)
        ], intentional_repeat=True)
        self.assertTrue(d.accepted)

    def test_invalid_similarity_fails_loudly(self):
        with self.assertRaises(ValueError):
            evaluate_repetition([
                PriorShotSimilarity("bad", 1.2, 0.5, 0.5)
            ])


if __name__ == "__main__":
    unittest.main()
