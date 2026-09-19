import unittest

from renderers.base import Renderer
from renderers.registry import RendererRegistry
from renderers.router import CapabilityRouter


class Fake(Renderer):
    provider_id = "test"
    model_id = "test"
    def __init__(self, renderer_id, health, supported=True):
        self.renderer_id = renderer_id
        self._health = health
        self._supported = supported
    def health(self):
        return {"health": self._health}
    def capabilities(self):
        return {"text_to_video": self._supported}
    def render(self, request):
        raise NotImplementedError


class RouterTests(unittest.TestCase):
    def test_skips_offline_backend(self):
        registry = RendererRegistry.from_renderers([
            Fake("wan", "offline"),
            Fake("fallback", "healthy"),
        ])
        decision = CapabilityRouter(registry, ["wan", "fallback"]).choose("text_to_video")
        self.assertEqual(decision.renderer.renderer_id, "fallback")

    def test_fails_when_no_backend_is_acceptable(self):
        registry = RendererRegistry.from_renderers([Fake("wan", "offline")])
        with self.assertRaises(RuntimeError):
            CapabilityRouter(registry, ["wan"]).choose("text_to_video")


if __name__ == "__main__":
    unittest.main()
