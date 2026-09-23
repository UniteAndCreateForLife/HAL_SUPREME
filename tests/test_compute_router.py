import os
import unittest
from unittest.mock import patch

from services.compute_router.app import build_providers, choose_route


class ComputeRouterProviderTests(unittest.TestCase):
    def test_new_remote_providers_default_disabled(self):
        with patch.dict(os.environ, {}, clear=True):
            providers = build_providers()
        self.assertFalse(providers["cloudflare_workers_ai"]["enabled"])
        self.assertFalse(providers["modal"]["enabled"])

    def test_cloudflare_routes_only_explicit_capabilities(self):
        with patch.dict(
            os.environ,
            {
                "HAL_PROVIDER_CLOUDFLARE_ENABLED": "true",
                "HAL_PROVIDER_HUGGINGFACE_ENABLED": "false",
                "HAL_PROVIDER_MODAL_ENABLED": "false",
                "HAL_PROVIDER_LOCAL_ENABLED": "false",
            },
            clear=True,
        ):
            providers = build_providers()
            inference = choose_route("inference", providers)
            video = choose_route("video", providers)
        self.assertIsNotNone(inference)
        self.assertEqual(inference["provider"], "cloudflare_workers_ai")
        self.assertIsNone(video)

    def test_modal_routes_gpu_workloads_without_claiming_video_support(self):
        with patch.dict(
            os.environ,
            {
                "HAL_PROVIDER_CLOUDFLARE_ENABLED": "false",
                "HAL_PROVIDER_HUGGINGFACE_ENABLED": "false",
                "HAL_PROVIDER_MODAL_ENABLED": "true",
                "HAL_PROVIDER_LOCAL_ENABLED": "false",
            },
            clear=True,
        ):
            providers = build_providers()
            science = choose_route("scientific_compute", providers)
            video = choose_route("video", providers)
        self.assertIsNotNone(science)
        self.assertEqual(science["provider"], "modal")
        self.assertIsNone(video)

    def test_fail_closed_when_provider_is_disabled(self):
        providers = {
            "cloudflare_workers_ai": {
                "enabled": False,
                "capabilities": ["inference"],
            }
        }
        self.assertIsNone(choose_route("inference", providers))

    def test_provider_inventory_does_not_expose_secret_environment_values(self):
        with patch.dict(
            os.environ,
            {
                "HAL_PROVIDER_CLOUDFLARE_ENABLED": "true",
                "HAL_CLOUDFLARE_WORKER_TOKEN": "must-not-leak",
                "MODAL_TOKEN_SECRET": "must-not-leak",
            },
            clear=True,
        ):
            providers = build_providers()
        rendered = repr(providers)
        self.assertNotIn("must-not-leak", rendered)
        self.assertNotIn("token", rendered.lower())


if __name__ == "__main__":
    unittest.main()
