import unittest

from renderers.frontier_fabric import HardwareProfile, plan_strict_video_fabric
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

    def test_clean_frontier_models_pass(self):
        for model_id in (
            "kandinsky-5-video-pro",
            "kandinsky-5-video-lite",
            "step-video-t2v",
            "wan2.2-ti2v-5b",
        ):
            self.assertTrue(require_strict_open_source(model_id).is_strict_open_source)

    def test_community_or_dependency_review_models_are_blocked(self):
        for model_id in (
            "ltx-2",
            "ltx-2.5",
            "minimax-h3",
            "skyreels-v3",
            "hunyuan-video-1.5",
            "magi-2-preview",
            "mmaudio",
        ):
            with self.assertRaises(ValueError):
                require_strict_open_source(model_id)


class FrontierFabricTests(unittest.TestCase):
    def test_known_8gb_class_machine_gets_offloaded_local_plan(self):
        plan = plan_strict_video_fabric(HardwareProfile(vram_gb=8, ram_gb=64))
        self.assertEqual(plan.tier, "local_8gb")
        self.assertEqual(plan.primary_world_model, "wan2.2-ti2v-5b")
        self.assertIn("LightX2V", plan.inference_engine)

    def test_large_gpu_promotes_kandinsky_pro(self):
        plan = plan_strict_video_fabric(HardwareProfile(vram_gb=64, ram_gb=128))
        self.assertEqual(plan.tier, "large_gpu")
        self.assertEqual(plan.primary_world_model, "kandinsky-5-video-pro")

    def test_tiny_host_ram_is_rejected_for_low_vram_offload(self):
        with self.assertRaises(ValueError):
            plan_strict_video_fabric(HardwareProfile(vram_gb=8, ram_gb=16))


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
