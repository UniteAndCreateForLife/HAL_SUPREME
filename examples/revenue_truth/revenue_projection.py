"""Conservative revenue and payout projections for the HAL Bounty Hunter UI.

This module derives display state from the existing canonical workstreams and
candidate intake.  It never promotes a record beyond the evidence encoded in
the source item or an explicit local display override.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping
from urllib.parse import urlparse


REVENUE_STAGES = (
    ("discovered", "Discovered"),
    ("qualified", "Qualified"),
    ("prepared", "Prepared"),
    ("submitted", "Submitted"),
    ("accepted_for_review", "Accepted for review"),
    ("merged_or_delivery_accepted", "Merged / delivery accepted"),
    ("sponsor_or_client_accepted", "Sponsor / client accepted"),
    ("awarded", "Awarded"),
    ("payout_initiated", "Payout initiated"),
    ("funds_available", "Funds available"),
    ("paid_and_reconciled", "Paid and reconciled"),
)
STAGE_IDS = tuple(stage for stage, _ in REVENUE_STAGES)
STAGE_INDEX = {stage: index for index, stage in enumerate(STAGE_IDS)}


def _text(value: Any) -> str:
    return str(value or "").strip()


def _lower(value: Any) -> str:
    return _text(value).lower()


def _money(value: Any) -> float:
    try:
        result = float(value or 0)
    except (TypeError, ValueError):
        return 0.0
    return round(max(0.0, result), 2)


def infer_stage(item: Mapping[str, Any]) -> str:
    """Return the most conservative evidenced revenue stage for one record."""

    explicit = _lower(item.get("revenue_stage"))
    if explicit in STAGE_INDEX:
        return explicit

    status = _lower(item.get("status"))
    paid_status = _lower(item.get("paid_status"))
    award_status = _lower(item.get("award_status"))
    submission_state = _lower(item.get("submission_state"))

    if (
        item.get("paid_and_reconciled") is True
        or paid_status in {"paid", "paid_and_reconciled", "received_and_reconciled"}
        or _money(item.get("verified_cash_received_usd")) > 0
    ):
        return "paid_and_reconciled"
    if item.get("funds_available") is True or paid_status == "funds_available":
        return "funds_available"
    if item.get("payout_initiated") is True or paid_status == "payout_initiated":
        return "payout_initiated"
    if item.get("awarded") is True or award_status in {"awarded", "winner", "honoree"}:
        return "awarded"
    if item.get("sponsor_or_client_accepted") is True:
        return "sponsor_or_client_accepted"
    if item.get("merged") is True or status.startswith("merged_") or "_merged_" in status:
        return "merged_or_delivery_accepted"
    if item.get("accepted_for_review") is True:
        return "accepted_for_review"

    negative_submission = any(
        token in status
        for token in ("not_submitted", "unsubmitted", "not_finally_submitted")
    )
    submission_evidence = (
        submission_state in {"submitted", "claim_submitted", "proposal_submitted"}
        or ("submitted" in status and not negative_submission)
        or "claimed" in status
    )
    if submission_evidence:
        return "submitted"
    if (
        item.get("proposal_prepared") is True
        or "prepared" in status
        or "draft" in status
        or "packet" in status
        or negative_submission
    ):
        return "prepared"
    if item.get("qualified") is True or "qualified" in status:
        return "qualified"
    return "discovered"


def _sponsor(item: Mapping[str, Any]) -> str:
    explicit = _text(item.get("sponsor") or item.get("client"))
    if explicit:
        return explicit
    url = _text(item.get("url") or item.get("pr"))
    parsed = urlparse(url)
    parts = [part for part in parsed.path.split("/") if part]
    if parsed.netloc.lower() == "github.com" and parts:
        return parts[0]
    if "upwork" in parsed.netloc.lower():
        return "Upwork client"
    return "Unverified sponsor/client"


def _contention(item: Mapping[str, Any]) -> dict[str, Any]:
    label = _text(item.get("contention_label"))
    if label:
        return {"label": label, "count": item.get("contention_count")}
    counts = []
    for key in ("open_claims", "github_contender_count", "github_pr_count"):
        try:
            counts.append(max(0, int(item.get(key) or 0)))
        except (TypeError, ValueError):
            counts.append(0)
    total = sum(counts)
    return {"label": str(total) if total else "unknown", "count": total or None}


def _funding_status(item: Mapping[str, Any]) -> str:
    explicit = _text(item.get("funding_status"))
    if explicit:
        return explicit
    pool = _text(item.get("payment_status"))
    if pool:
        return f"Bounty pool: {pool}; recipient payment unverified"
    return "unknown / unverified"


def _exact_sha(item: Mapping[str, Any]) -> str:
    for key in (
        "exact_evidence_sha256",
        "evidence_sha256",
        "tested_head_sha",
        "head_sha",
        "source_sha",
        "merge_commit_sha",
    ):
        value = _text(item.get(key))
        if value:
            return value
    return ""


def build_record(item: Mapping[str, Any], override: Mapping[str, Any] | None = None) -> dict[str, Any]:
    merged = dict(item)
    if isinstance(override, Mapping):
        merged.update(override)
    stage = infer_stage(merged)
    verified_paid = _money(merged.get("verified_cash_received_usd"))
    next_human_action = _text(merged.get("next_human_action"))
    if not next_human_action and "human" in _lower(merged.get("blocker")):
        next_human_action = _text(merged.get("next_action") or merged.get("blocker"))
    return {
        "id": _text(merged.get("id")) or "unknown",
        "title": _text(merged.get("title")) or _text(merged.get("id")) or "Unknown",
        "url": _text(merged.get("url") or merged.get("pr")),
        "sponsor": _sponsor(merged),
        "opportunity_type": _text(merged.get("opportunity_type") or merged.get("category")) or "opportunity",
        "value_type": _text(merged.get("value_type")) or "advertised opportunity value",
        "advertised_value_usd": _money(merged.get("reward_usd")),
        "verified_paid_usd": verified_paid,
        "stage": stage,
        "stage_index": STAGE_INDEX[stage],
        "stage_evidence": _text(merged.get("stage_evidence") or merged.get("status")),
        "funding_status": _funding_status(merged),
        "funded_or_escrowed": merged.get("funded_or_escrowed") is True,
        "contention": _contention(merged),
        "exact_evidence_sha": _exact_sha(merged),
        "evidence_uri": _text(merged.get("evidence_uri")),
        "terms_freshness": _text(merged.get("terms_freshness")) or "unknown",
        "payout_provider": _text(merged.get("payout_provider")) or "unknown",
        "payout_onboarding": _text(merged.get("payout_onboarding")) or "unknown",
        "payout_initiated": merged.get("payout_initiated") is True,
        "follow_up_due": _text(merged.get("follow_up_due")) or "not set",
        "next_human_action": next_human_action,
        "human_action_priority": int(merged.get("human_action_priority") or 99),
        "next_automatic_action": _text(merged.get("next_automatic_action")),
        "blocker": _text(merged.get("blocker")),
    }


def build_revenue_projection(
    workstreams: Iterable[Mapping[str, Any]],
    candidates: Iterable[Mapping[str, Any]],
    overrides: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    overrides = overrides if isinstance(overrides, Mapping) else {}
    records = []
    seen: set[str] = set()
    for item in [*workstreams, *candidates]:
        item_id = _text(item.get("id"))
        if not item_id or item_id in seen:
            continue
        seen.add(item_id)
        records.append(build_record(item, overrides.get(item_id)))
    records.sort(
        key=lambda row: (
            row["human_action_priority"],
            -row["advertised_value_usd"],
            row["title"].lower(),
        )
    )

    columns = {stage: [] for stage in STAGE_IDS}
    for record in records:
        columns[record["stage"]].append(record["id"])

    human_actions = [
        {
            "id": row["id"],
            "title": row["title"],
            "action": row["next_human_action"],
            "priority": row["human_action_priority"],
            "stage": row["stage"],
            "follow_up_due": row["follow_up_due"],
            "url": row["url"],
        }
        for row in records
        if row["next_human_action"]
    ]
    payout_records = [
        row
        for row in records
        if row["stage_index"] >= STAGE_INDEX["submitted"]
        or row["payout_provider"] != "unknown"
    ]
    sponsor_memory = [
        {
            "record_id": row["id"],
            "sponsor": row["sponsor"],
            "current_stage": row["stage"],
            "payment_rail": row["payout_provider"],
            "accepted_history": "unverified",
            "memory_basis": "current record only",
        }
        for row in records
        if row["sponsor"] != "Unverified sponsor/client"
    ]
    return {
        "schema_version": 1,
        "stages": [{"id": stage, "label": label} for stage, label in REVENUE_STAGES],
        "records": records,
        "columns": columns,
        "human_actions": human_actions,
        "payout_records": payout_records,
        "sponsor_memory": sponsor_memory,
        "kpis": {
            "records": len(records),
            "prepared": len(columns["prepared"]),
            "submitted": len(columns["submitted"]),
            "sponsor_or_client_accepted": len(columns["sponsor_or_client_accepted"]),
            "paid_and_reconciled": len(columns["paid_and_reconciled"]),
            "human_actions": len(human_actions),
            "funded_or_escrowed": sum(1 for row in records if row["funded_or_escrowed"]),
            "advertised_value_usd": round(sum(row["advertised_value_usd"] for row in records), 2),
            "verified_paid_usd": round(sum(row["verified_paid_usd"] for row in records), 2),
        },
    }
