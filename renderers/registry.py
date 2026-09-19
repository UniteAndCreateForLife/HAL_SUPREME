from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .base import Renderer


@dataclass
class RendererRegistry:
    _renderers: dict[str, Renderer]

    @classmethod
    def from_renderers(cls, renderers: Iterable[Renderer]) -> "RendererRegistry":
        values = list(renderers)
        mapping = {r.renderer_id: r for r in values}
        if len(mapping) != len(values):
            raise ValueError("duplicate renderer_id")
        return cls(mapping)

    def get(self, renderer_id: str) -> Renderer:
        try:
            return self._renderers[renderer_id]
        except KeyError as exc:
            raise KeyError(f"unknown renderer: {renderer_id}") from exc

    def healthy(self) -> list[Renderer]:
        return [r for r in self._renderers.values() if r.health().get("health") == "healthy"]

    def select(self, capability: str) -> Renderer:
        for renderer in self.healthy():
            if renderer.capabilities().get(capability) is True:
                return renderer
        raise RuntimeError(f"no healthy renderer provides capability={capability!r}")
