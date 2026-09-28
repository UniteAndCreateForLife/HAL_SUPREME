from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable, Mapping

SCHEMA = "hal.leverage_lens.v1"
AUTHORITY = "DERIVED_NON_AUTHORITATIVE"

BENEFIT_WEIGHTS = {
    "impact": 0.22,
    "unblock": 0.18,
    "compounding": 0.15,
    "strategy_alignment": 0.13,
    "proof": 0.10,
    "monetization": 0.10,
    "reuse": 0.07,
    "urgency": 0.05,
}

BAND_ORDER = {"NOW": 0, "NEXT": 1, "LATER": 2, "BLOCKED": 3}


class LeverageInputError(ValueError):
    pass


def _rating(task: Mapping[str, Any], key: str, default: float, minimum: float = 0.0) -> float:
    value = task.get(key, default)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise LeverageInputError(f"{key} must be numeric")
    value = float(value)
    if value < minimum or value > 5.0:
        raise LeverageInputError(f"{key} must be between {minimum:g} and 5")
    return value


def score_task(task: Mapping[str, Any]) -> dict[str, Any]:
    """Score one proposed task without mutating it or any external state."""
    source = deepcopy(dict(task))
    task_id = str(source.get("id", "")).strip()
    title = str(source.get("title", task_id)).strip()
    if not task_id:
        raise LeverageInputError("task id is required")

    ratings = {key: _rating(source, key, 0.0) for key in BENEFIT_WEIGHTS}
    effort = _rating(source, "effort", 3.0, minimum=1.0)
    risk = _rating(source, "risk", 2.0)

    caps: list[str] = []
    if not source.get("evidence") and ratings["proof"] > 2.0:
        ratings["proof"] = 2.0
        caps.append("proof capped at 2/5 because no evidence references were supplied")
    if not source.get("strategy_refs") and ratings["strategy_alignment"] > 2.0:
        ratings["strategy_alignment"] = 2.0
        caps.append("strategy_alignment capped at 2/5 because no strategy references were supplied")

    contributions = {
        key: round(weight * (ratings[key] / 5.0) * 100.0, 2)
        for key, weight in BENEFIT_WEIGHTS.items()
    }
    benefit_score = sum(contributions.values())

    execution_factor = max(0.50, 1.0 - (0.07 * effort) - (0.03 * risk))
    leverage_score = round(benefit_score * execution_factor, 1)

    blocked = bool(source.get("human_blocked")) or source.get("dependency_ready", True) is False
    if blocked:
        band = "BLOCKED"
    elif leverage_score >= 70.0:
        band = "NOW"
    elif leverage_score >= 50.0:
        band = "NEXT"
    else:
        band = "LATER"

    top_drivers = [
        key for key, _ in sorted(contributions.items(), key=lambda item: (-item[1], item[0]))[:3]
    ]
    return {
        "id": task_id,
        "title": title,
        "leverage_score": leverage_score,
        "priority_band": band,
        "blocked": blocked,
        "benefit_score_before_friction": round(benefit_score, 1),
        "execution_factor": round(execution_factor, 3),
        "effective_ratings": ratings,
        "top_drivers": top_drivers,
        "caps": caps,
        "epistemic_state": str(source.get("epistemic_state", "UNKNOWN")).upper(),
        "acceptance": list(source.get("acceptance", [])),
    }


def rank_tasks(tasks: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    ranked = [score_task(task) for task in tasks]
    return sorted(
        ranked,
        key=lambda row: (BAND_ORDER[row["priority_band"]], -row["leverage_score"], row["id"]),
    )


def build_projection(tasks: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "authority": AUTHORITY,
        "formula": {
            "benefit_weights": BENEFIT_WEIGHTS,
            "execution_factor": "max(0.50, 1 - 0.07*effort - 0.03*risk)",
            "bands": {"NOW": ">=70", "NEXT": ">=50", "LATER": "<50", "BLOCKED": "human/dependency blocked"},
        },
        "tasks": rank_tasks(tasks),
    }


def _load_tasks(path: Path) -> list[Mapping[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        payload = payload.get("tasks")
    if not isinstance(payload, list):
        raise LeverageInputError("input must be a JSON list or an object with a tasks list")
    if not all(isinstance(item, dict) for item in payload):
        raise LeverageInputError("every task must be a JSON object")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Rank proposed HAL work without mutating canonical state.")
    parser.add_argument("input", type=Path, help="JSON list of proposed tasks")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    projection = build_projection(_load_tasks(args.input))
    encoded = json.dumps(projection, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(encoded + "\n", encoding="utf-8")
    else:
        print(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
