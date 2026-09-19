from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .base import Renderer
from .registry import RendererRegistry


@dataclass(frozen=True)
class RouteDecision:
    renderer: Renderer
    reason: str


class CapabilityRouter:
    """Selects a healthy backend by required capability and explicit priority."""

    def __init__(self, registry: RendererRegistry, priority: Iterable[str]):
        self.registry = registry
        self.priority = tuple(priority)

    def choose(self, capability: str) -> RouteDecision:
        failures: list[str] = []
        for renderer_id in self.priority:
            try:
                renderer = self.registry.get(renderer_id)
            except KeyError:
                failures.append(f"{renderer_id}:missing")
                continue
            health = renderer.health()
            if health.get("health") != "healthy":
                failures.append(f"{renderer_id}:{health.get('health', 'unknown')}")
                continue
            if renderer.capabilities().get(capability) is not True:
                failures.append(f"{renderer_id}:no-{capability}")
                continue
            return RouteDecision(renderer, f"priority match for {capability}")
        raise RuntimeError("no acceptable renderer; " + ", ".join(failures))
