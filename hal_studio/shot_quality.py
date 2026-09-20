"""HAL Studio deterministic shot-quality admission gate.

This module does not render or inspect pixels itself. It consumes measured QA metrics
from renderer/evaluator workers and returns a deterministic ACCEPT/REJECT decision.
The HAL supervisor remains the sole authority that commits accepted shots.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


DEFAULT_THRESHOLDS = {
    "imaging_quality": 0.70,
    "subject_consistency": 0.90,
    "background_consistency": 0.90,
    "motion_smoothness": 0.90,
    "dynamic_degree": 0.20,
    "contact_integrity": 0.80,
    "depth_occlusion": 0.80,
}


@dataclass(frozen=True)
class ShotQualityDecision:
    accepted: bool
    score: float
    failures: tuple[str, ...] = field(default_factory=tuple)


def evaluate_shot(
    metrics: Mapping[str, float],
    *,
    thresholds: Mapping[str, float] | None = None,
    motion_required: bool = True,
    contact_required: bool = False,
) -> ShotQualityDecision:
    """Reject shots that fail required measured quality dimensions.

    Missing required measurements fail closed. `dynamic_degree` is required only for
    motion-critical shots; `contact_integrity` only when the shot manifest declares
    physical contact. Values are normalized to [0, 1].
    """
    limits = dict(DEFAULT_THRESHOLDS)
    if thresholds:
        limits.update(thresholds)

    required = [
        "imaging_quality",
        "subject_consistency",
        "background_consistency",
        "motion_smoothness",
        "depth_occlusion",
    ]
    if motion_required:
        required.append("dynamic_degree")
    if contact_required:
        required.append("contact_integrity")

    failures: list[str] = []
    valid_scores: list[float] = []
    for name in required:
        value = metrics.get(name)
        if value is None:
            failures.append(f"missing:{name}")
            continue
        if not 0.0 <= float(value) <= 1.0:
            failures.append(f"invalid:{name}")
            continue
        value = float(value)
        valid_scores.append(value)
        if value < limits[name]:
            failures.append(f"below_threshold:{name}:{value:.3f}<{limits[name]:.3f}")

    score = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0
    return ShotQualityDecision(not failures, round(score, 4), tuple(failures))
