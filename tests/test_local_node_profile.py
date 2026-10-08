import os
import unittest
from unittest.mock import patch

from services.compute_router.local_node import build_local_node_profile


class LocalNodeProfileTests(unittest.TestCase):
    def test_default_profile_is_disabled_owned_and_public_safe(self):
        with patch.dict(os.environ, {}, clear=True):
            profile = build_local_node_profile()

        self.assertFalse(profile["enabled"])
        self.assertTrue(profile["owner_controlled"])
        self.assertFalse(profile["remote_dependency"])
        self.assertEqual(profile["budget_policy"], "owned_compute_only")
        self.assertEqual(
            profile["capabilities"],
            ["audio", "comfyui", "media", "video"],
        )
        self.assertEqual(
            profile["capacity"],
            {
                "cpu_cores": None,
                "ram_gib": None,
                "gpu_model": None,
                "gpu_vram_gib": None,
            },
        )
        self.assertTrue(all(value is False for value in profile["disclosure"].values()))

    def test_operator_declared_capacity_and_capabilities_are_normalized(self):
        with patch.dict(
            os.environ,
            {
                "HAL_PROVIDER_LOCAL_ENABLED": "true",
                "HAL_LOCAL_NODE_CAPABILITIES": "Inference, coding, inference,  ",
                "HAL_LOCAL_NODE_CPU_CORES": "16",
                "HAL_LOCAL_NODE_RAM_GIB": "119.0",
                "HAL_LOCAL_NODE_GPU_MODEL": "RTX 2080",
                "HAL_LOCAL_NODE_GPU_VRAM_GIB": "8",
            },
            clear=True,
        ):
            profile = build_local_node_profile()

        self.assertTrue(profile["enabled"])
        self.assertEqual(profile["capabilities"], ["coding", "inference"])
        self.assertEqual(profile["capacity"]["cpu_cores"], 16)
        self.assertEqual(profile["capacity"]["ram_gib"], 119.0)
        self.assertEqual(profile["capacity"]["gpu_model"], "RTX 2080")
        self.assertEqual(profile["capacity"]["gpu_vram_gib"], 8.0)

    def test_invalid_or_negative_capacity_values_fail_closed_to_unknown(self):
        with patch.dict(
            os.environ,
            {
                "HAL_LOCAL_NODE_CPU_CORES": "-4",
                "HAL_LOCAL_NODE_RAM_GIB": "not-a-number",
                "HAL_LOCAL_NODE_GPU_VRAM_GIB": "-1",
            },
            clear=True,
        ):
            profile = build_local_node_profile()

        self.assertIsNone(profile["capacity"]["cpu_cores"])
        self.assertIsNone(profile["capacity"]["ram_gib"])
        self.assertIsNone(profile["capacity"]["gpu_vram_gib"])

    def test_profile_does_not_auto_disclose_host_identity(self):
        with patch.dict(
            os.environ,
            {
                "COMPUTERNAME": "PRIVATE-WORKSTATION",
                "USERNAME": "private-user",
                "HOME": "/private/home",
            },
            clear=True,
        ):
            rendered = repr(build_local_node_profile())

        self.assertNotIn("PRIVATE-WORKSTATION", rendered)
        self.assertNotIn("private-user", rendered)
        self.assertNotIn("/private/home", rendered)


if __name__ == "__main__":
    unittest.main()
