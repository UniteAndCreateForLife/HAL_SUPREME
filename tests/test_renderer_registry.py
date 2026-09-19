import unittest

from renderers.base import Renderer
from renderers.registry import RendererRegistry


class FakeRenderer(Renderer):
    provider_id = "test"
    model_id = "test"

    def __init__(self, renderer_id, healthy=True, t2v=True):
        self.renderer_id = renderer_id
        self._healthy = healthy
        self._t2v = t2v

    def health(self):
        return {"health": "healthy" if self._healthy else "offline"}

    def capabilities(self):
        return {"text_to_video": self._t2v}

    def render(self, request):
        raise NotImplementedError


class RegistryTests(unittest.TestCase):
    def test_selects_healthy_capable_renderer(self):
        registry = RendererRegistry.from_renderers([
            FakeRenderer("dead", healthy=False),
            FakeRenderer("good", healthy=True),
        ])
        self.assertEqual(registry.select("text_to_video").renderer_id, "good")

    def test_duplicate_ids_fail(self):
        with self.assertRaises(ValueError):
            RendererRegistry.from_renderers([FakeRenderer("x"), FakeRenderer("x")])


if __name__ == "__main__":
    unittest.main()
