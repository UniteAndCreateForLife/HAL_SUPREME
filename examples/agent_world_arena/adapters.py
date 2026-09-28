from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol, runtime_checkable

from .protocol import Action, Observation, ProviderDescriptor


@runtime_checkable
class AgentAdapter(Protocol):
    """Minimal provider boundary used by the reference episode runner."""

    provider: ProviderDescriptor

    def decide(self, observation: Observation) -> Action:
        """Return one bounded action for the supplied observation."""


@dataclass
class ScriptedAdapter:
    """Dependency-free baseline useful for contract tests and tournament controls."""

    provider: ProviderDescriptor
    policy: Callable[[Observation], Action]

    def decide(self, observation: Observation) -> Action:
        return self.policy(observation)
