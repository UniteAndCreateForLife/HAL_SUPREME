from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .protocol import Action, Observation
from .sim import Arena


@dataclass(frozen=True)
class SessionStatus:
    episode_id: str
    tick: int
    done: bool
    expected_agents: tuple[str, ...]
    submitted_agents: tuple[str, ...]
    waiting_for: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "tick": self.tick,
            "done": self.done,
            "expected_agents": list(self.expected_agents),
            "submitted_agents": list(self.submitted_agents),
            "waiting_for": list(self.waiting_for),
        }


class EpisodeSession:
    """Network/MCP-ready simultaneous-action coordinator.

    Each agent may submit at most one action for the current tick. The world
    advances only when the arena authority explicitly commits the complete
    action set, preventing provider request order from silently changing game
    semantics.
    """

    def __init__(self, arena: Arena) -> None:
        if not arena.agents:
            raise ValueError("session requires at least one registered agent")
        self.arena = arena
        self._pending: dict[str, Action] = {}

    def observe(self, agent_id: str) -> Observation:
        return self.arena.observe(agent_id)

    def submit_action(self, agent_id: str, action: Action) -> SessionStatus:
        if self.arena.done:
            raise RuntimeError("episode is complete")
        if agent_id not in self.arena.agents:
            raise KeyError(f"unknown agent_id: {agent_id}")
        if agent_id in self._pending:
            raise RuntimeError(f"action already submitted for {agent_id} at tick {self.arena.tick}")

        action.validate(max_message_chars=self.arena.config.max_message_chars)
        self._pending[agent_id] = action
        return self.status()

    def can_advance(self) -> bool:
        return not self.arena.done and not self.status().waiting_for

    def advance(self) -> dict[str, Any]:
        if self.arena.done:
            raise RuntimeError("episode is complete")
        waiting = self.status().waiting_for
        if waiting:
            raise RuntimeError(f"cannot advance; waiting for agents: {list(waiting)}")

        actions = dict(self._pending)
        self._pending.clear()
        receipt = self.arena.step(actions)
        receipt["session_commit"] = {
            "policy": "all-agents-submitted",
            "submitted_agents": sorted(actions),
        }
        return receipt

    def advance_with_idle_for_missing(self, *, reason: str = "deadline") -> dict[str, Any]:
        """Operator/runner timeout path that fails missing agents to idle."""

        if self.arena.done:
            raise RuntimeError("episode is complete")

        missing = self.status().waiting_for
        for agent_id in missing:
            self._pending[agent_id] = Action("idle")

        actions = dict(self._pending)
        self._pending.clear()
        receipt = self.arena.step(actions)
        receipt["session_commit"] = {
            "policy": "idle-for-missing",
            "reason": reason,
            "submitted_agents": sorted(set(actions) - set(missing)),
            "idled_agents": list(missing),
        }
        return receipt

    def status(self) -> SessionStatus:
        expected = tuple(sorted(self.arena.agents))
        submitted = tuple(sorted(self._pending))
        waiting = tuple(agent_id for agent_id in expected if agent_id not in self._pending)
        return SessionStatus(
            episode_id=self.arena.episode_id,
            tick=self.arena.tick,
            done=self.arena.done,
            expected_agents=expected,
            submitted_agents=submitted,
            waiting_for=waiting,
        )
