from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

from .sim import ArenaConfig


@dataclass(frozen=True)
class AgentSlot:
    slot_id: str
    start: tuple[int, int]
    team: str | None = None
    role: str | None = None

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "AgentSlot":
        start = payload.get("start")
        if not isinstance(start, list) or len(start) != 2:
            raise ValueError("slot start must be a two-item list")
        return cls(
            slot_id=str(payload["slot_id"]),
            start=(int(start[0]), int(start[1])),
            team=str(payload["team"]) if payload.get("team") is not None else None,
            role=str(payload["role"]) if payload.get("role") is not None else None,
        )


@dataclass(frozen=True)
class ResourceSpec:
    resource_id: str
    position: tuple[int, int]
    value: int = 1

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ResourceSpec":
        position = payload.get("position")
        if not isinstance(position, list) or len(position) != 2:
            raise ValueError("resource position must be a two-item list")
        return cls(
            resource_id=str(payload["resource_id"]),
            position=(int(position[0]), int(position[1])),
            value=int(payload.get("value", 1)),
        )


@dataclass(frozen=True)
class ScenarioManifest:
    scenario_id: str
    seed: int
    width: int
    height: int
    max_ticks: int
    mode: str
    slots: tuple[AgentSlot, ...]
    resources: tuple[ResourceSpec, ...] = ()
    description: str = ""
    schema: str = "hal.agent_world.scenario.v0"

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ScenarioManifest":
        manifest = cls(
            scenario_id=str(payload["scenario_id"]),
            seed=int(payload["seed"]),
            width=int(payload["width"]),
            height=int(payload["height"]),
            max_ticks=int(payload["max_ticks"]),
            mode=str(payload["mode"]),
            slots=tuple(AgentSlot.from_dict(item) for item in payload.get("slots", [])),
            resources=tuple(
                ResourceSpec.from_dict(item) for item in payload.get("resources", [])
            ),
            description=str(payload.get("description", "")),
            schema=str(payload.get("schema", "hal.agent_world.scenario.v0")),
        )
        manifest.validate()
        return manifest

    def validate(self) -> None:
        if not self.scenario_id:
            raise ValueError("scenario_id is required")
        if len(self.slots) < 1:
            raise ValueError("scenario requires at least one agent slot")

        slot_ids = [slot.slot_id for slot in self.slots]
        if len(slot_ids) != len(set(slot_ids)):
            raise ValueError("slot ids must be unique")

        resource_ids = [resource.resource_id for resource in self.resources]
        if len(resource_ids) != len(set(resource_ids)):
            raise ValueError("resource ids must be unique")

        config = self.arena_config()
        for slot in self.slots:
            self._require_in_bounds(slot.start, config)
        for resource in self.resources:
            if resource.value < 1:
                raise ValueError("resource value must be positive")
            self._require_in_bounds(resource.position, config)

    def arena_config(self) -> ArenaConfig:
        return ArenaConfig(
            width=self.width,
            height=self.height,
            max_ticks=self.max_ticks,
            max_agents=len(self.slots),
            mode=self.mode,
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for slot in payload["slots"]:
            slot["start"] = list(slot["start"])
        for resource in payload["resources"]:
            resource["position"] = list(resource["position"])
        return payload

    @staticmethod
    def _require_in_bounds(position: tuple[int, int], config: ArenaConfig) -> None:
        x, y = position
        if not (0 <= x < config.width and 0 <= y < config.height):
            raise ValueError(f"scenario position out of bounds: {position}")
