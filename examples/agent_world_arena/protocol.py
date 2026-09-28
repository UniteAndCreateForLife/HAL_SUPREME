from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
from typing import Any, Mapping

PROTOCOL_VERSION = "hal.agent_world.v0"
VALID_ACTIONS = frozenset({"idle", "move", "gather", "say"})


def canonical_json(payload: Mapping[str, Any]) -> str:
    """Return deterministic JSON suitable for hashing and replay receipts."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_payload(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ProviderDescriptor:
    """Public, non-secret metadata for an agent provider or worker."""

    provider_id: str
    model: str
    transport: str = "adapter"
    capabilities: tuple[str, ...] = ()
    protocol_version: str = PROTOCOL_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Action:
    """One bounded command from an agent to the simulation authority."""

    kind: str
    dx: int = 0
    dy: int = 0
    target: str | None = None
    message: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def validate(self, *, max_message_chars: int = 512) -> None:
        if self.kind not in VALID_ACTIONS:
            raise ValueError(f"unsupported action kind: {self.kind}")

        if self.kind == "move":
            if (self.dx, self.dy) not in {(1, 0), (-1, 0), (0, 1), (0, -1)}:
                raise ValueError("move must be exactly one cardinal step")
        elif self.dx != 0 or self.dy != 0:
            raise ValueError("dx/dy are only valid for move")

        if self.kind == "say":
            if not self.target:
                raise ValueError("say requires target agent id or '*'")
            if self.message is None:
                raise ValueError("say requires message")
            if len(self.message) > max_message_chars:
                raise ValueError("message exceeds configured limit")
        elif self.target is not None or self.message is not None:
            raise ValueError("target/message are only valid for say")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True)
class Observation:
    """Provider-independent snapshot delivered to one agent."""

    episode_id: str
    tick: int
    agent_id: str
    position: tuple[int, int]
    energy: int
    score: int
    visible_resources: tuple[Mapping[str, Any], ...]
    inbox: tuple[Mapping[str, Any], ...]
    capabilities: tuple[str, ...]
    protocol_version: str = PROTOCOL_VERSION

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["position"] = list(self.position)
        payload["visible_resources"] = [dict(item) for item in self.visible_resources]
        payload["inbox"] = [dict(item) for item in self.inbox]
        payload["capabilities"] = list(self.capabilities)
        return payload
