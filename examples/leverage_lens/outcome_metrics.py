from __future__ import annotations

from statistics import mean
from typing import Any, Iterable, Mapping

SCHEMA = "hal.outcome_metrics.v1"
AUTHORITY = "DERIVED_NON_AUTHORITATIVE"


class OutcomeMetricsError(ValueError):
    pass


def _bool(record: Mapping[str, Any], key: str) -> bool:
    value = record.get(key)
    if not isinstance(value, bool):
        raise OutcomeMetricsError(f"{key} must be boolean")
    return value


def _nonnegative_number(record: Mapping[str, Any], key: str) -> float:
    value = record.get(key, 0)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise OutcomeMetricsError(f"{key} must be numeric")
    value = float(value)
    if value < 0:
        raise OutcomeMetricsError(f"{key} must be >= 0")
    return value


def summarize_outcomes(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Summarize observed execution outcomes without changing task state."""
    rows = [dict(record) for record in records]
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for record in rows:
        run_id = str(record.get("id", "")).strip()
        if not run_id:
            raise OutcomeMetricsError("each record requires id")
        if run_id in seen:
            raise OutcomeMetricsError(f"duplicate outcome id: {run_id}")
        seen.add(run_id)
        normalized.append(
            {
                "id": run_id,
                "accepted": _bool(record, "accepted"),
                "verification_passed": _bool(record, "verification_passed"),
                "session_visibility_loss": _bool(record, "session_visibility_loss"),
                "reusable_artifact": _bool(record, "reusable_artifact"),
                "external_outcome": _bool(record, "external_outcome"),
                "attempts": _nonnegative_number(record, "attempts"),
                "human_interventions": _nonnegative_number(
                    record, "human_interventions"
                ),
                "duration_s": _nonnegative_number(record, "duration_s"),
            }
        )

    total = len(normalized)
    if total == 0:
        return {
            "schema": SCHEMA,
            "authority": AUTHORITY,
            "sample_size": 0,
            "metrics": {},
        }

    accepted = [row for row in normalized if row["accepted"]]
    verified = [row for row in normalized if row["verification_passed"]]
    accepted_attempts = [row["attempts"] for row in accepted]
    accepted_interventions = [row["human_interventions"] for row in accepted]
    accepted_duration = [row["duration_s"] for row in accepted]

    def rate(predicate) -> float:
        return round(sum(1 for row in normalized if predicate(row)) / total, 4)

    metrics = {
        "accepted_rate": rate(lambda row: row["accepted"]),
        "verification_pass_rate": rate(lambda row: row["verification_passed"]),
        "session_visibility_loss_rate": rate(
            lambda row: row["session_visibility_loss"]
        ),
        "reusable_artifact_rate": rate(lambda row: row["reusable_artifact"]),
        "external_outcome_rate": rate(lambda row: row["external_outcome"]),
        "mean_attempts_per_accepted": (
            round(mean(accepted_attempts), 3) if accepted_attempts else None
        ),
        "mean_human_interventions_per_accepted": (
            round(mean(accepted_interventions), 3)
            if accepted_interventions
            else None
        ),
        "mean_duration_s_per_accepted": (
            round(mean(accepted_duration), 3) if accepted_duration else None
        ),
        "false_success_count": sum(
            1
            for row in normalized
            if row["accepted"] and not row["verification_passed"]
        ),
    }
    return {
        "schema": SCHEMA,
        "authority": AUTHORITY,
        "sample_size": total,
        "accepted_count": len(accepted),
        "verified_count": len(verified),
        "metrics": metrics,
    }
