import unittest

from renderers.longform import LongFormProductionProfile, plan_long_form
from renderers.open_source_policy import (
    require_strict_open_source,
    validate_strict_open_source_profile,
)


class OpenSourcePolicyTests(unittest.TestCase):
    def test_default_longform_stack_is_strict_open_source(self):
        profile = LongFormProductionProfile()
        records = validate_strict_open_source_profile(profile.model_ids())
        self.assertEqual(len(records), len(profile.model_ids()))
        self.assertTrue(all(record.is_strict_open_source for record in records))

    def test_ltx2_is_blocked_in_strict_mode(self):
        with self.assertRaises(ValueError):
            require_strict_open_source("ltx-2")

    def test_noncommercial_checkpoint_is_blocked(self):
        with self.assertRaises(ValueError):
            require_strict_open_source("mmaudio")


class LongFormPlannerTests(unittest.TestCase):
    def test_six_minute_plan_has_exact_duration_and_many_real_shots(self):
        profile = LongFormProductionProfile(duration_seconds=360.0, shot_target_seconds=5.0)
        plan = plan_long_form(profile)
        self.assertEqual(len(plan.shots), 72)
        self.assertAlmostEqual(plan.shots[0].start_seconds, 0.0)
        self.assertAlmostEqual(plan.shots[-1].end_seconds, 360.0)
        self.assertTrue(all(3.0 <= shot.duration_seconds <= 8.0 for shot in plan.shots))
        self.assertGreater(len({shot.lane for shot in plan.shots}), 2)

    def test_music_is_partitioned_into_stable_sections(self):
        plan = plan_long_form(LongFormProductionProfile(duration_seconds=360.0))
        self.assertEqual(len(plan.music_sections), 2)
        self.assertEqual(plan.music_sections[0].mode, "generate")
        self.assertEqual(plan.music_sections[1].mode, "complete")
        self.assertAlmostEqual(plan.music_sections[-1].end_seconds, 360.0)


if __name__ == "__main__":
    unittest.main()
