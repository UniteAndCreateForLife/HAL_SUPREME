from __future__ import annotations

import hashlib
from typing import Any

from engine import canonical_json_bytes, verify_audit_receipt

GENESIS_HASH = "0" * 64
ALLOWED_EVENT_TYPES = {"REVIEW_OPENED", "REVIEW_NOTE", "REVIEW_APPROVED", "REVIEW_REJECTED"}
ALLOWED_ROLES = {"analyst", "reviewer", "auditor"}


def _event_hash(event_without_hash: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(event_without_hash)).hexdigest()


def append_event(
    chain: list[dict[str, Any]],
    *,
    report: dict[str, Any],
    receipt: dict[str, Any],
    event_type: str,
    actor_role: str,
    note: str = "",
) -> dict[str, Any]:
    """Append a deterministic, privacy-minimized review event.

    The chain stores role, event type, report hash, and an optional non-sensitive note;
    it deliberately does not store a reviewer identity or the underlying evidence text.
    """
    if event_type not in ALLOWED_EVENT_TYPES:
        raise ValueError(f"unsupported event_type: {event_type}")
    if actor_role not in ALLOWED_ROLES:
        raise ValueError(f"unsupported actor_role: {actor_role}")
    if not verify_audit_receipt(report, receipt):
        raise ValueError("report receipt failed verification")
    if event_type in {"REVIEW_APPROVED", "REVIEW_REJECTED"} and actor_role != "reviewer":
        raise PermissionError("only reviewer role may close review")
    if len(note) > 500:
        raise ValueError("audit note exceeds 500 characters")

    previous_hash = chain[-1]["event_sha256"] if chain else GENESIS_HASH
    event = {
        "schema": "hal-campus-review-event/v1",
        "sequence": len(chain) + 1,
        "previous_event_sha256": previous_hash,
        "event_type": event_type,
        "actor_role": actor_role,
        "case_id": report.get("case_id"),
        "report_sha256": receipt.get("report_sha256"),
        "note": note,
    }
    event["event_sha256"] = _event_hash(event)
    chain.append(event)
    return event


def verify_chain(chain: list[dict[str, Any]]) -> bool:
    previous_hash = GENESIS_HASH
    for index, event in enumerate(chain, start=1):
        if event.get("sequence") != index:
            return False
        if event.get("previous_event_sha256") != previous_hash:
            return False
        if event.get("event_type") not in ALLOWED_EVENT_TYPES:
            return False
        if event.get("actor_role") not in ALLOWED_ROLES:
            return False
        if event.get("event_type") in {"REVIEW_APPROVED", "REVIEW_REJECTED"} and event.get("actor_role") != "reviewer":
            return False
        supplied_hash = event.get("event_sha256")
        unsigned = {key: value for key, value in event.items() if key != "event_sha256"}
        if supplied_hash != _event_hash(unsigned):
            return False
        previous_hash = supplied_hash
    return True
