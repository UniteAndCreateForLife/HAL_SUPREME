from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import Any, Mapping

BRIDGE_PROTOCOL_VERSION = "hal.agent_world.brain_bridge.v0"
MAX_FRAME_BYTES = 256_000
MAX_ACTION_METADATA_KEYS = 32


def _reject_forbidden_keys(payload: Mapping[str, Any]) -> None:
    forbidden_fragments = (
        "authorization",
        "api_key",
        "apikey",
        "password",
        "secret",
        "token",
        "cookie",
        "credential",
    )
    stack: list[tuple[str, Any]] = [("", payload)]
    while stack:
        path, value = stack.pop()
        if isinstance(value, Mapping):
            for key, child in value.items():
                normalized = str(key).lower().replace("-", "_")
                if any(fragment in normalized for fragment in forbidden_fragments):
                    raise ValueError(f"credential-like field is forbidden: {path}{key}")
                stack.append((f"{path}{key}.", child))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                stack.append((f"{path}{index}.", child))


@dataclass(frozen=True)
class BrainRequest:
    episode_id: str
    tick: int
    slot_id: str
    deadline_ms: int
    observation: Mapping[str, Any]
    allowed_actions: tuple[str, ...]
    request_id: str
    protocol_version: str = BRIDGE_PROTOCOL_VERSION

    def validate(self) -> None:
        if not self.episode_id or not self.slot_id or not self.request_id:
            raise ValueError("episode_id, slot_id, and request_id are required")
        if self.tick < 0:
            raise ValueError("tick cannot be negative")
        if self.deadline_ms < 1:
            raise ValueError("deadline_ms must be positive")
        if len(self.allowed_actions) != len(set(self.allowed_actions)):
            raise ValueError("allowed_actions must be unique")
        _reject_forbidden_keys(self.observation)

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "protocol_version": self.protocol_version,
            "request_id": self.request_id,
            "episode_id": self.episode_id,
            "tick": self.tick,
            "slot_id": self.slot_id,
            "deadline_ms": self.deadline_ms,
            "allowed_actions": list(self.allowed_actions),
            "observation": dict(self.observation),
        }


@dataclass(frozen=True)
class BrainResponse:
    request_id: str
    episode_id: str
    tick: int
    slot_id: str
    action: Mapping[str, Any]
    diagnostics: Mapping[str, Any] = field(default_factory=dict)
    protocol_version: str = BRIDGE_PROTOCOL_VERSION

    def validate_against(self, request: BrainRequest) -> None:
        request.validate()
        if self.protocol_version != request.protocol_version:
            raise ValueError("brain bridge protocol version mismatch")
        if self.request_id != request.request_id:
            raise ValueError("request_id mismatch")
        if self.episode_id != request.episode_id:
            raise ValueError("episode_id mismatch")
        if self.tick != request.tick:
            raise ValueError("tick mismatch")
        if self.slot_id != request.slot_id:
            raise ValueError("slot_id mismatch")
        if not isinstance(self.action, Mapping):
            raise ValueError("action must be a JSON object")
        kind = self.action.get("kind")
        if kind not in request.allowed_actions:
            raise ValueError(f"action kind not allowed for this request: {kind}")
        if len(self.diagnostics) > MAX_ACTION_METADATA_KEYS:
            raise ValueError("diagnostics contains too many keys")
        _reject_forbidden_keys(self.action)
        _reject_forbidden_keys(self.diagnostics)

    def to_dict(self) -> dict[str, Any]:
        return {
            "protocol_version": self.protocol_version,
            "request_id": self.request_id,
            "episode_id": self.episode_id,
            "tick": self.tick,
            "slot_id": self.slot_id,
            "action": dict(self.action),
            "diagnostics": dict(self.diagnostics),
        }


def encode_frame(payload: Mapping[str, Any]) -> bytes:
    rendered = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    if len(rendered) > MAX_FRAME_BYTES:
        raise ValueError("brain bridge frame exceeds maximum size")
    return rendered + b"\n"


def decode_frame(raw: bytes) -> dict[str, Any]:
    if len(raw) > MAX_FRAME_BYTES + 1:
        raise ValueError("brain bridge frame exceeds maximum size")
    if not raw.endswith(b"\n"):
        raise ValueError("brain bridge frame must be newline-delimited")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid brain bridge JSON frame") from exc
    if not isinstance(payload, dict):
        raise ValueError("brain bridge frame must be a JSON object")
    return payload


def request_from_dict(payload: Mapping[str, Any]) -> BrainRequest:
    request = BrainRequest(
        protocol_version=str(payload.get("protocol_version", "")),
        request_id=str(payload["request_id"]),
        episode_id=str(payload["episode_id"]),
        tick=int(payload["tick"]),
        slot_id=str(payload["slot_id"]),
        deadline_ms=int(payload["deadline_ms"]),
        allowed_actions=tuple(str(item) for item in payload["allowed_actions"]),
        observation=dict(payload["observation"]),
    )
    request.validate()
    return request


def response_from_dict(payload: Mapping[str, Any]) -> BrainResponse:
    return BrainResponse(
        protocol_version=str(payload.get("protocol_version", "")),
        request_id=str(payload["request_id"]),
        episode_id=str(payload["episode_id"]),
        tick=int(payload["tick"]),
        slot_id=str(payload["slot_id"]),
        action=dict(payload["action"]),
        diagnostics=dict(payload.get("diagnostics", {})),
    )
