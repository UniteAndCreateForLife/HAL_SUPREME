from __future__ import annotations
from dataclasses import dataclass, field
from .circuit_breaker import CircuitBreaker


@dataclass
class Route:
    provider: str
    model: str
    role: str
    benchmark_score: float = 0.0
    latency_seconds: float = 999.0
    cost_class: str = "free"
    enabled: bool = True
    zero_spend_ready: bool = True
    breaker: CircuitBreaker = field(default_factory=CircuitBreaker)

    @property
    def utility(self) -> float:
        latency_penalty = min(self.latency_seconds / 20.0, 10.0)
        free_bonus = 5.0 if self.cost_class in {"free", "local", "subscription"} else -30.0
        return self.benchmark_score + free_bonus - latency_penalty


class ProviderRouter:
    """Rank routes already admitted by HAL's canonical provider mesh.

    This service never enables a provider, inspects credentials, or overrides
    HAL zero-spend readiness. Those remain canonical provider-mesh decisions.
    """

    def __init__(self, routes: list[Route]):
        self.routes = routes

    def ranked(self, role: str) -> list[Route]:
        choices = [
            route for route in self.routes
            if route.enabled and route.zero_spend_ready and route.role == role and route.breaker.allowed()
        ]
        return sorted(choices, key=lambda route: route.utility, reverse=True)

    def choose(self, role: str) -> Route:
        choices = self.ranked(role)
        if not choices:
            raise RuntimeError(f"no healthy zero-spend route for role={role}")
        return choices[0]
