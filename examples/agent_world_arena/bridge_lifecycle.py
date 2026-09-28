from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ConnectionState(str, Enum):
    UNBOUND = "unbound"
    ACTIVE = "active"
    QUARANTINED = "quarantined"
    CLOSED = "closed"


TERMINAL_REQUEST_OUTCOMES = frozenset(
    {
        "accepted",
        "timeout",
        "malformed",
        "rejected",
        "worker_crash",
        "transport_closed",
    }
)


@dataclass(frozen=True)
class RequestOutcome:
    request_id: str
    outcome: str
    fault_class: str | None = None
    fallback: str | None = None

    def validate(self) -> None:
        if not self.request_id:
            raise ValueError("request_id is required")
        if self.outcome not in TERMINAL_REQUEST_OUTCOMES:
            raise ValueError(f"unsupported terminal outcome: {self.outcome}")
        if self.outcome == "accepted" and self.fault_class is not None:
            raise ValueError("accepted request cannot carry a fault_class")


@dataclass
class FaultLedger:
    """Count one terminal result per request, never one fault per retry/poll."""

    outcomes: dict[str, RequestOutcome] = field(default_factory=dict)
    transport_events: list[dict[str, Any]] = field(default_factory=list)

    def record_outcome(self, outcome: RequestOutcome) -> None:
        outcome.validate()
        existing = self.outcomes.get(outcome.request_id)
        if existing is not None:
            if existing != outcome:
                raise RuntimeError(
                    f"request already has terminal outcome: {outcome.request_id}"
                )
            return
        self.outcomes[outcome.request_id] = outcome

    def record_transport_event(self, *, event: str, detail: str = "") -> None:
        self.transport_events.append({"event": event, "detail": detail})

    @property
    def fault_count(self) -> int:
        return sum(
            1
            for outcome in self.outcomes.values()
            if outcome.outcome != "accepted"
        )


@dataclass
class SlotConnection:
    """Reference lifecycle for one arena participant slot.

    A timeout quarantines the active connection. Rebinding is legal only after
    the old connection has been closed. Each successful bind increments the
    generation, preventing stale connection state from being reused implicitly.
    """

    slot_id: str
    state: ConnectionState = ConnectionState.UNBOUND
    generation: int = 0
    active_peer_id: str | None = None
    outstanding_request_id: str | None = None

    def bind(self, *, peer_id: str) -> int:
        if self.state not in {ConnectionState.UNBOUND, ConnectionState.CLOSED}:
            raise RuntimeError(
                f"slot {self.slot_id} cannot bind while state={self.state.value}"
            )
        if not peer_id:
            raise ValueError("peer_id is required")

        self.generation += 1
        self.active_peer_id = peer_id
        self.outstanding_request_id = None
        self.state = ConnectionState.ACTIVE
        return self.generation

    def begin_request(self, request_id: str) -> None:
        if self.state != ConnectionState.ACTIVE:
            raise RuntimeError("request requires an active connection")
        if self.outstanding_request_id is not None:
            raise RuntimeError(
                f"slot already has outstanding request: {self.outstanding_request_id}"
            )
        if not request_id:
            raise ValueError("request_id is required")
        self.outstanding_request_id = request_id

    def accept_response(
        self,
        *,
        peer_id: str,
        generation: int,
        request_id: str,
    ) -> None:
        if self.state != ConnectionState.ACTIVE:
            raise RuntimeError("response arrived on a non-active connection")
        if peer_id != self.active_peer_id:
            raise RuntimeError("response peer does not own this slot")
        if generation != self.generation:
            raise RuntimeError("response generation is stale")
        if request_id != self.outstanding_request_id:
            raise RuntimeError("response request_id is stale or unexpected")
        self.outstanding_request_id = None

    def timeout(self, request_id: str) -> None:
        if self.state != ConnectionState.ACTIVE:
            raise RuntimeError("timeout requires an active connection")
        if request_id != self.outstanding_request_id:
            raise RuntimeError("timeout request_id is not outstanding")
        self.outstanding_request_id = None
        self.state = ConnectionState.QUARANTINED

    def close_quarantined(self) -> None:
        if self.state != ConnectionState.QUARANTINED:
            raise RuntimeError("only a quarantined connection may use this close path")
        self.active_peer_id = None
        self.outstanding_request_id = None
        self.state = ConnectionState.CLOSED

    def close(self) -> None:
        self.active_peer_id = None
        self.outstanding_request_id = None
        self.state = ConnectionState.CLOSED
