from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .protocol import Action, Observation, sha256_payload


@dataclass(frozen=True)
class ArenaConfig:
    width: int = 12
    height: int = 12
    max_ticks: int = 200
    max_agents: int = 16
    starting_energy: int = 100
    move_cost: int = 1
    gather_cost: int = 1
    say_cost: int = 1
    sight_radius: int = 4
    max_message_chars: int = 512
    mode: str = "hybrid"

    def __post_init__(self) -> None:
        if self.width < 2 or self.height < 2:
            raise ValueError("arena dimensions must be at least 2x2")
        if self.max_ticks < 1 or self.max_agents < 1:
            raise ValueError("max_ticks and max_agents must be positive")
        if self.starting_energy < 0:
            raise ValueError("starting_energy cannot be negative")
        if self.mode not in {"compete", "cooperate", "hybrid", "sandbox"}:
            raise ValueError("unsupported arena mode")


@dataclass
class AgentState:
    agent_id: str
    provider_id: str
    position: tuple[int, int]
    energy: int
    score: int = 0
    inbox: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ResourceState:
    resource_id: str
    position: tuple[int, int]
    value: int = 1


class Arena:
    """Deterministic authority used to validate the cross-provider contract."""

    capabilities = ("idle", "move", "gather", "say")

    def __init__(self, config: ArenaConfig | None = None, *, episode_id: str = "episode-0") -> None:
        self.config = config or ArenaConfig()
        self.episode_id = episode_id
        self.tick = 0
        self.done = False
        self.agents: dict[str, AgentState] = {}
        self.resources: dict[str, ResourceState] = {}
        self.transcript: list[dict[str, Any]] = []

    def register_agent(
        self,
        agent_id: str,
        provider_id: str,
        *,
        position: tuple[int, int] = (0, 0),
    ) -> None:
        if self.tick != 0:
            raise RuntimeError("agents must register before the episode starts")
        if agent_id in self.agents:
            raise ValueError(f"duplicate agent_id: {agent_id}")
        if len(self.agents) >= self.config.max_agents:
            raise ValueError("arena agent limit reached")
        self._require_in_bounds(position)
        self.agents[agent_id] = AgentState(
            agent_id=agent_id,
            provider_id=provider_id,
            position=position,
            energy=self.config.starting_energy,
        )

    def add_resource(
        self,
        resource_id: str,
        position: tuple[int, int],
        *,
        value: int = 1,
    ) -> None:
        if self.tick != 0:
            raise RuntimeError("resources must be added before the episode starts")
        if resource_id in self.resources:
            raise ValueError(f"duplicate resource_id: {resource_id}")
        if value < 1:
            raise ValueError("resource value must be positive")
        self._require_in_bounds(position)
        self.resources[resource_id] = ResourceState(resource_id, position, value)

    def observe(self, agent_id: str) -> Observation:
        agent = self._agent(agent_id)
        visible = []
        for resource in sorted(self.resources.values(), key=lambda item: item.resource_id):
            if self._distance(agent.position, resource.position) <= self.config.sight_radius:
                visible.append(
                    {
                        "resource_id": resource.resource_id,
                        "position": list(resource.position),
                        "value": resource.value,
                    }
                )
        inbox = tuple(dict(item) for item in agent.inbox)
        agent.inbox.clear()
        return Observation(
            episode_id=self.episode_id,
            tick=self.tick,
            agent_id=agent.agent_id,
            position=agent.position,
            energy=agent.energy,
            score=agent.score,
            visible_resources=tuple(visible),
            inbox=inbox,
            capabilities=self.capabilities,
        )

    def step(self, actions: Mapping[str, Action]) -> dict[str, Any]:
        if self.done:
            raise RuntimeError("episode is complete")

        unknown = sorted(set(actions) - set(self.agents))
        if unknown:
            raise ValueError(f"actions supplied for unknown agents: {unknown}")

        resolved: dict[str, Action] = {}
        action_events: list[dict[str, Any]] = []
        outgoing_messages: list[tuple[str, str, str]] = []

        for agent_id in sorted(self.agents):
            action = actions.get(agent_id, Action("idle"))
            action.validate(max_message_chars=self.config.max_message_chars)
            resolved[agent_id] = action

        next_positions: dict[str, tuple[int, int]] = {}
        for agent_id, action in resolved.items():
            agent = self.agents[agent_id]
            if action.kind != "move":
                continue
            if agent.energy < self.config.move_cost:
                action_events.append({"agent_id": agent_id, "kind": "move", "status": "no_energy"})
                continue
            candidate = (agent.position[0] + action.dx, agent.position[1] + action.dy)
            if not self._in_bounds(candidate):
                action_events.append({"agent_id": agent_id, "kind": "move", "status": "out_of_bounds"})
                continue
            next_positions[agent_id] = candidate

        for agent_id, position in next_positions.items():
            agent = self.agents[agent_id]
            agent.position = position
            agent.energy -= self.config.move_cost
            action_events.append(
                {"agent_id": agent_id, "kind": "move", "status": "ok", "position": list(position)}
            )

        gathered: set[str] = set()
        for agent_id in sorted(self.agents):
            action = resolved[agent_id]
            if action.kind != "gather":
                continue
            agent = self.agents[agent_id]
            if agent.energy < self.config.gather_cost:
                action_events.append({"agent_id": agent_id, "kind": "gather", "status": "no_energy"})
                continue
            matches = [
                item
                for item in sorted(self.resources.values(), key=lambda item: item.resource_id)
                if item.position == agent.position and item.resource_id not in gathered
            ]
            agent.energy -= self.config.gather_cost
            if not matches:
                action_events.append({"agent_id": agent_id, "kind": "gather", "status": "empty"})
                continue
            resource = matches[0]
            gathered.add(resource.resource_id)
            agent.score += resource.value
            action_events.append(
                {
                    "agent_id": agent_id,
                    "kind": "gather",
                    "status": "ok",
                    "resource_id": resource.resource_id,
                    "value": resource.value,
                }
            )

        for resource_id in gathered:
            self.resources.pop(resource_id, None)

        for agent_id in sorted(self.agents):
            action = resolved[agent_id]
            if action.kind != "say":
                continue
            agent = self.agents[agent_id]
            if agent.energy < self.config.say_cost:
                action_events.append({"agent_id": agent_id, "kind": "say", "status": "no_energy"})
                continue
            recipients = (
                [target for target in sorted(self.agents) if target != agent_id]
                if action.target == "*"
                else [action.target]
            )
            if any(target not in self.agents for target in recipients):
                action_events.append({"agent_id": agent_id, "kind": "say", "status": "unknown_target"})
                continue
            agent.energy -= self.config.say_cost
            for target in recipients:
                outgoing_messages.append((agent_id, target, action.message or ""))
            action_events.append(
                {
                    "agent_id": agent_id,
                    "kind": "say",
                    "status": "ok",
                    "recipients": recipients,
                }
            )

        for sender, target, message in outgoing_messages:
            self.agents[target].inbox.append(
                {"from": sender, "message": message, "sent_tick": self.tick}
            )

        self.tick += 1
        self.done = self.tick >= self.config.max_ticks

        receipt = {
            "schema": "hal.agent_world.step_receipt.v0",
            "episode_id": self.episode_id,
            "tick": self.tick,
            "events": action_events,
            "state": self.state_payload(),
        }
        receipt["state_sha256"] = sha256_payload(receipt["state"])
        self.transcript.append(receipt)
        return receipt

    def state_payload(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "tick": self.tick,
            "done": self.done,
            "mode": self.config.mode,
            "agents": [
                {
                    "agent_id": agent.agent_id,
                    "provider_id": agent.provider_id,
                    "position": list(agent.position),
                    "energy": agent.energy,
                    "score": agent.score,
                    "inbox_depth": len(agent.inbox),
                }
                for agent in sorted(self.agents.values(), key=lambda item: item.agent_id)
            ],
            "resources": [
                {
                    "resource_id": resource.resource_id,
                    "position": list(resource.position),
                    "value": resource.value,
                }
                for resource in sorted(self.resources.values(), key=lambda item: item.resource_id)
            ],
        }

    def _agent(self, agent_id: str) -> AgentState:
        try:
            return self.agents[agent_id]
        except KeyError as exc:
            raise KeyError(f"unknown agent_id: {agent_id}") from exc

    def _in_bounds(self, position: tuple[int, int]) -> bool:
        x, y = position
        return 0 <= x < self.config.width and 0 <= y < self.config.height

    def _require_in_bounds(self, position: tuple[int, int]) -> None:
        if not self._in_bounds(position):
            raise ValueError(f"position out of bounds: {position}")

    @staticmethod
    def _distance(left: tuple[int, int], right: tuple[int, int]) -> int:
        return abs(left[0] - right[0]) + abs(left[1] - right[1])
