import os
import unittest
from unittest.mock import patch

from services.compute_router.app import build_providers, choose_route


class ComputeRouterProviderTests(unittest.TestCase):
    def test_new_remote_providers_default_disabled_and_not_zero_spend_ready(self):
        with patch.dict(os.environ, {}, clear=True):
            providers = build_providers()
        for name in ("cloudflare_workers_ai", "modal"):
            self.assertFalse(providers[name]["enabled"])
            self.assertTrue(providers[name]["requires_zero_spend_ready"])
            self.assertFalse(providers[name]["zero_spend_ready"])

    def test_enabled_remote_provider_still_fails_closed_without_zero_spend_readiness(self):
        with patch.dict(
            os.environ,
            {
                "HAL_PROVIDER_CLOUDFLARE_ENABLED": "true",
                "HAL_PROVIDER_MODAL_ENABLED": "true",
                "HAL_PROVIDER_HUGGINGFACE_ENABLED": "false",
                "HAL_PROVIDER_LOCAL_ENABLED": "false",
            },
            clear=True,
        ):
            providers = build_providers()
            cloudflare = choose_route("embeddings", providers)
            modal = choose_route("scientific_compute", providers)
        self.assertIsNone(cloudflare)
        self.assertIsNone(modal)

    def test_cloudflare_routes_only_when_enabled_ready_and_capable(self):
        with patch.dict(
            os.environ,
            {
                "HAL_PROVIDER_CLOUDFLARE_ENABLED": "true",
                "HAL_PROVIDER_CLOUDFLARE_ZERO_SPEND_READY": "true",
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

    def test_modal_routes_gpu_workloads_only_when_zero_spend_ready(self):
        with patch.dict(
            os.environ,
            {
                "HAL_PROVIDER_CLOUDFLARE_ENABLED": "false",
                "HAL_PROVIDER_HUGGINGFACE_ENABLED": "false",
                "HAL_PROVIDER_MODAL_ENABLED": "true",
                "HAL_PROVIDER_MODAL_ZERO_SPEND_READY": "true",
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

    def test_unready_provider_is_not_returned_as_fallback(self):
        with patch.dict(
            os.environ,
            {
                "HAL_PROVIDER_CLOUDFLARE_ENABLED": "true",
                "HAL_PROVIDER_CLOUDFLARE_ZERO_SPEND_READY": "true",
                "HAL_PROVIDER_MODAL_ENABLED": "true",
                "HAL_PROVIDER_MODAL_ZERO_SPEND_READY": "false",
                "HAL_PROVIDER_HUGGINGFACE_ENABLED": "false",
                "HAL_PROVIDER_LOCAL_ENABLED": "false",
            },
            clear=True,
        ):
            route = choose_route("inference", build_providers())
        self.assertIsNotNone(route)
        self.assertEqual(route["provider"], "cloudflare_workers_ai")
        self.assertEqual(route["fallbacks"], [])

    def test_local_provider_does_not_require_remote_zero_spend_attestation(self):
        with patch.dict(
            os.environ,
            {
                "HAL_PROVIDER_LOCAL_ENABLED": "true",
                "HAL_PROVIDER_HUGGINGFACE_ENABLED": "false",
                "HAL_PROVIDER_CLOUDFLARE_ENABLED": "false",
                "HAL_PROVIDER_MODAL_ENABLED": "false",
            },
            clear=True,
        ):
            route = choose_route("video", build_providers())
        self.assertIsNotNone(route)
        self.assertEqual(route["provider"], "local_hal")

    def test_fail_closed_when_provider_is_disabled(self):
        providers = {
            "cloudflare_workers_ai": {
                "enabled": False,
                "capabilities": ["inference"],
                "requires_zero_spend_ready": True,
                "zero_spend_ready": True,
            }
        }
        self.assertIsNone(choose_route("inference", providers))

    def test_provider_inventory_does_not_expose_secret_environment_values(self):
        with patch.dict(
            os.environ,
            {
                "HAL_PROVIDER_CLOUDFLARE_ENABLED": "true",
                "HAL_PROVIDER_CLOUDFLARE_ZERO_SPEND_READY": "true",
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
