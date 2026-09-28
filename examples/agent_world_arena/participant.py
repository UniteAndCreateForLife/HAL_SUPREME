from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


SUPPORTED_TRANSPORTS = frozenset(
    {
        "scripted",
        "local-python",
        "openai-compatible",
        "mcp",
        "a2a",
    }
)

_FORBIDDEN_METADATA_FRAGMENTS = (
    "authorization",
    "api_key",
    "apikey",
    "password",
    "secret",
    "token",
)


@dataclass(frozen=True)
class ParticipantManifest:
    """Public-safe descriptor for one Agent World participant integration."""

    participant_id: str
    display_name: str
    framework: str
    transport: str
    capabilities: tuple[str, ...]
    protocol_versions: Mapping[str, str] = field(default_factory=dict)
    endpoint: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
    schema: str = "hal.agent_world.participant.v0"

    def validate(self) -> None:
        if not self.participant_id:
            raise ValueError("participant_id is required")
        if not self.display_name:
            raise ValueError("display_name is required")
        if not self.framework:
            raise ValueError("framework is required")
        if self.transport not in SUPPORTED_TRANSPORTS:
            raise ValueError(f"unsupported transport: {self.transport}")
        if len(self.capabilities) != len(set(self.capabilities)):
            raise ValueError("capabilities must be unique")

        if self.endpoint is not None:
            if self.transport in {"mcp", "a2a", "openai-compatible"}:
                if not (
                    self.endpoint.startswith("https://")
                    or self.endpoint.startswith("http://127.0.0.1")
                    or self.endpoint.startswith("http://localhost")
                ):
                    raise ValueError(
                        "network endpoint must use https or explicit loopback"
                    )

        self._reject_secret_metadata(self.metadata)

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["capabilities"] = list(self.capabilities)
        payload["protocol_versions"] = dict(self.protocol_versions)
        payload["metadata"] = dict(self.metadata)
        return payload

    @staticmethod
    def _reject_secret_metadata(metadata: Mapping[str, Any]) -> None:
        for key in metadata:
            normalized = str(key).lower().replace("-", "_")
            if any(fragment in normalized for fragment in _FORBIDDEN_METADATA_FRAGMENTS):
                raise ValueError(
                    f"credential-like metadata key is not allowed: {key}"
                )


def negotiate_capabilities(
    participant: ParticipantManifest,
    required: tuple[str, ...],
) -> tuple[str, ...]:
    """Fail closed when a scenario requires unsupported capabilities."""

    participant.validate()
    missing = sorted(set(required) - set(participant.capabilities))
    if missing:
        raise ValueError(
            "participant lacks required capabilities: " + ", ".join(missing)
        )
    return tuple(sorted(required))
