"""HAL Studio depth/occlusion consistency admission worker.

Evaluator workers provide normalized geometric evidence. This module does not infer
3D geometry and never upgrades 2D/2.5D evidence into a true-3D provenance claim.
The existing HAL supervisor remains the sole admission authority.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping

DEFAULT_LIMITS = {
    "min_depth_consistency": 0.68,
    "min_occlusion_consistency": 0.72,
    "min_contact_depth": 0.70,
    "max_order_flips": 0.08,
}


@dataclass(frozen=True)
class GeometryObservation:
    frame_index: int
    depth_consistency: float | None
    occlusion_consistency: float | None
    contact_depth: float | None = None
    order_flip_rate: float | None = None


@dataclass(frozen=True)
class GeometryDecision:
    accepted: bool
    evaluator: str
    frames_checked: int
    failures: tuple[str, ...] = field(default_factory=tuple)


def _validate01(name: str, value: float) -> float:
    value = float(value)
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be normalized to [0, 1]")
    return value


def evaluate_depth_occlusion(
    observations: Iterable[GeometryObservation],
    *,
    evaluator: str,
    limits: Mapping[str, float] | None = None,
    require_contact: bool = False,
) -> GeometryDecision:
    """Fail closed on temporal depth/occlusion contradictions.

    ``order_flip_rate`` is the normalized fraction of tracked foreground/background
    pairs whose relative depth ordering flips without an evaluator-declared physical
    crossing. Contact-critical shots additionally require contact-depth evidence.
    Thresholds are policy defaults and must be calibrated against real rendered shots.
    """
    if not evaluator.strip():
        raise ValueError("evaluator provenance is required")
    thresholds = dict(DEFAULT_LIMITS)
    if limits:
        thresholds.update(limits)
    for key, value in thresholds.items():
        _validate01(f"limit:{key}", value)

    rows = list(observations)
    if not rows:
        return GeometryDecision(False, evaluator, 0, ("missing_geometry_observations",))

    failures: list[str] = []
    contact_seen = False
    for row in rows:
        if row.depth_consistency is None:
            failures.append(f"missing_depth_evidence:frame={row.frame_index}")
        else:
            depth = _validate01("depth_consistency", row.depth_consistency)
            if depth < thresholds["min_depth_consistency"]:
                failures.append(f"depth_drift:frame={row.frame_index}:score={depth:.3f}")

        if row.occlusion_consistency is None:
            failures.append(f"missing_occlusion_evidence:frame={row.frame_index}")
        else:
            occ = _validate01("occlusion_consistency", row.occlusion_consistency)
            if occ < thresholds["min_occlusion_consistency"]:
                failures.append(f"occlusion_error:frame={row.frame_index}:score={occ:.3f}")

        if row.order_flip_rate is not None:
            flips = _validate01("order_flip_rate", row.order_flip_rate)
            if flips > thresholds["max_order_flips"]:
                failures.append(f"depth_order_flip:frame={row.frame_index}:rate={flips:.3f}")

        if row.contact_depth is not None:
            contact_seen = True
            contact = _validate01("contact_depth", row.contact_depth)
            if require_contact and contact < thresholds["min_contact_depth"]:
                failures.append(f"contact_depth_error:frame={row.frame_index}:score={contact:.3f}")

    if require_contact and not contact_seen:
        failures.append("missing_contact_depth_evidence")

    return GeometryDecision(not failures, evaluator, len(rows), tuple(failures))
