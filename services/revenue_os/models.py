from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class PayoutType(str, Enum):
    FIXED = "fixed"
    CONTRACT = "contract"
    COMPETITIVE = "competitive"
    CRYPTO = "crypto"
    CREDIT = "credit"
    UNKNOWN = "unknown"


class MoneyState(str, Enum):
    ADVERTISED = "advertised"
    SUBMITTED = "submitted"
    MERGED = "merged"
    ACCEPTED = "accepted"
    AWARDED = "awarded"
    PAID = "paid"


class WorkState(str, Enum):
    DISCOVERED = "discovered"
    VERIFIED = "verified"
    READY = "ready"
    IMPLEMENTING = "implementing"
    TESTING = "testing"
    REVIEWING = "reviewing"
    SUBMISSION_READY = "submission_ready"
    SUBMITTED = "submitted"
    WON = "won"
    PAID = "paid"
    BLOCKED = "blocked"
    PARKED = "parked"


@dataclass(slots=True)
class Opportunity:
    id: str
    title: str
    source: str
    url: str
    payout_amount: float = 0.0
    payout_currency: str = "USD"
    payout_type: PayoutType = PayoutType.UNKNOWN
    deadline: str | None = None
    eligibility_verified: bool = False
    submission_route_verified: bool = False
    payout_route_verified: bool = False
    contention: int = 3
    fit: int = 3
    hal_reuse: int = 3
    effort_hours: float = 8.0
    evidence_quality: int = 1
    blockers: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["payout_type"] = self.payout_type.value
        return data


@dataclass(slots=True)
class ScoreBreakdown:
    total: float
    payout: float
    certainty: float
    fit: float
    urgency: float
    contention: float
    effort: float
    reuse: float
    evidence: float
    penalties: float
    reasons: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
