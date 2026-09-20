"""HAL V11 scene-aware lighting admission worker.

This module scores measured lighting evidence only. It does not render, relight,
or claim 3D reconstruction. The single HAL supervisor remains the sole authority
that may commit an accepted take.
"""
from dataclasses import dataclass
from math import isfinite
from typing import Mapping


@dataclass(frozen=True)
class LightingPolicy:
    min_subject_scene_harmony: float = 0.70
    min_temporal_stability: float = 0.72
    min_key_direction_consistency: float = 0.68
    min_contact_shadow_consistency: float = 0.66
    max_unmotivated_light_change: float = 0.12


@dataclass(frozen=True)
class LightingDecision:
    accepted: bool
    reasons: tuple[str, ...]
    checkpoint: Mapping[str, object]


def _metric(evidence: Mapping[str, object], name: str) -> float:
    if name not in evidence:
        raise ValueError(f"missing lighting evidence: {name}")
    value = evidence[name]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"invalid lighting metric: {name}")
    value = float(value)
    if not isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"lighting metric outside [0,1]: {name}")
    return value


def evaluate_scene_lighting(
    evidence: Mapping[str, object],
    *,
    shot_id: str,
    evaluator_id: str,
    contact_critical: bool = False,
    policy: LightingPolicy = LightingPolicy(),
) -> LightingDecision:
    """Fail-closed admission check for scene-aware lighting measurements."""
    required = (
        "subject_scene_harmony",
        "temporal_stability",
        "key_direction_consistency",
        "unmotivated_light_change",
    )
    try:
        m = {name: _metric(evidence, name) for name in required}
        if contact_critical:
            m["contact_shadow_consistency"] = _metric(evidence, "contact_shadow_consistency")
    except ValueError as exc:
        return LightingDecision(False, (str(exc),), {
            "shot_id": shot_id, "evaluator_id": evaluator_id, "status": "REJECTED"
        })

    reasons = []
    if m["subject_scene_harmony"] < policy.min_subject_scene_harmony:
        reasons.append("subject lighting does not harmonize with scene")
    if m["temporal_stability"] < policy.min_temporal_stability:
        reasons.append("lighting flicker/temporal instability")
    if m["key_direction_consistency"] < policy.min_key_direction_consistency:
        reasons.append("key-light direction is inconsistent with scene")
    if m["unmotivated_light_change"] > policy.max_unmotivated_light_change:
        reasons.append("unmotivated lighting change exceeds tolerance")
    if contact_critical and m["contact_shadow_consistency"] < policy.min_contact_shadow_consistency:
        reasons.append("contact shadow is inconsistent with interaction")

    accepted = not reasons
    return LightingDecision(accepted, tuple(reasons), {
        "shot_id": shot_id,
        "evaluator_id": evaluator_id,
        "status": "ACCEPTED" if accepted else "REJECTED",
        "metrics": m,
        "provenance": "measured-lighting-evidence; not a true-3D claim",
    })
