from __future__ import annotations

from dataclasses import asdict
import json
from typing import Any, Mapping, Sequence
from uuid import uuid4

from .protocol import Action
from .runner import build_arena
from .scenario import ScenarioManifest
from .session import EpisodeSession


class ArenaService:
    """Process-local authority facade suitable for MCP/HTTP wrappers.

    The service owns episode objects. Provider clients only receive serialized
    observations and submit serialized bounded actions. It intentionally has no
    provider credentials, shell access, filesystem write authority, or model SDK.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, EpisodeSession] = {}
        self._assignments: dict[str, dict[str, str]] = {}
        self._replays: dict[str, list[dict[str, Any]]] = {}

    def create_episode(
        self,
        scenario: Mapping[str, Any],
        provider_ids: Sequence[str],
        *,
        episode_id: str | None = None,
    ) -> dict[str, Any]:
        manifest = ScenarioManifest.from_dict(scenario)
        runtime_id = episode_id or f"{manifest.scenario_id}-{uuid4().hex[:12]}"
        if runtime_id in self._sessions:
            raise ValueError(f"episode already exists: {runtime_id}")

        # Preserve scenario semantics while making the runtime identity unique.
        runtime_manifest = ScenarioManifest(
            scenario_id=runtime_id,
            seed=manifest.seed,
            width=manifest.width,
            height=manifest.height,
            max_ticks=manifest.max_ticks,
            mode=manifest.mode,
            slots=manifest.slots,
            resources=manifest.resources,
            description=manifest.description,
            schema=manifest.schema,
        )
        arena, assignment = build_arena(runtime_manifest, provider_ids)
        self._sessions[runtime_id] = EpisodeSession(arena)
        self._assignments[runtime_id] = assignment
        self._replays[runtime_id] = []
        return {
            "episode_id": runtime_id,
            "scenario_id": manifest.scenario_id,
            "seed": manifest.seed,
            "provider_assignment": dict(assignment),
            "status": self.status(runtime_id),
        }

    def observe(self, episode_id: str, agent_id: str) -> dict[str, Any]:
        session = self._session(episode_id)
        return session.observe(agent_id).to_dict()

    def submit_action(
        self,
        episode_id: str,
        agent_id: str,
        action: Mapping[str, Any],
    ) -> dict[str, Any]:
        session = self._session(episode_id)
        parsed = Action(
            kind=str(action["kind"]),
            dx=int(action.get("dx", 0)),
            dy=int(action.get("dy", 0)),
            target=action.get("target"),
            message=action.get("message"),
            metadata=dict(action.get("metadata", {})),
        )
        status = session.submit_action(agent_id, parsed)
        return status.to_dict()

    def advance(self, episode_id: str) -> dict[str, Any]:
        session = self._session(episode_id)
        receipt = session.advance()
        self._replays[episode_id].append(receipt)
        return receipt

    def advance_with_idle_for_missing(
        self,
        episode_id: str,
        *,
        reason: str = "deadline",
    ) -> dict[str, Any]:
        session = self._session(episode_id)
        receipt = session.advance_with_idle_for_missing(reason=reason)
        self._replays[episode_id].append(receipt)
        return receipt

    def status(self, episode_id: str) -> dict[str, Any]:
        session = self._session(episode_id)
        payload = session.status().to_dict()
        payload["provider_assignment"] = dict(self._assignments[episode_id])
        payload["replay_steps"] = len(self._replays[episode_id])
        return payload

    def replay(self, episode_id: str) -> dict[str, Any]:
        self._session(episode_id)
        return {
            "schema": "hal.agent_world.replay.v0",
            "episode_id": episode_id,
            "provider_assignment": dict(self._assignments[episode_id]),
            "steps": list(self._replays[episode_id]),
        }

    def list_episodes(self) -> list[dict[str, Any]]:
        return [
            self.status(episode_id)
            for episode_id in sorted(self._sessions)
        ]

    def _session(self, episode_id: str) -> EpisodeSession:
        try:
            return self._sessions[episode_id]
        except KeyError as exc:
            raise KeyError(f"unknown episode_id: {episode_id}") from exc


def decode_json_object(value: str, *, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} must be valid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be a JSON object")
    return payload
