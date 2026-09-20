"""HAL Studio persistent identity admission worker.

Evaluator workers provide normalized identity evidence; this module never generates,
tracks, or labels a person by itself. The existing HAL supervisor remains the sole
admission authority. Reference IDs and model/provenance strings are carried into the
decision so resumable production can reproduce why a shot passed or failed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping

DEFAULT_LIMITS = {
    "min_face_similarity": 0.55,
    "min_body_similarity": 0.45,
    "min_wardrobe_similarity": 0.50,
    "max_face_drift": 0.18,
}


@dataclass(frozen=True)
class IdentityObservation:
    frame_index: int
    face_similarity: float | None
    body_similarity: float | None
    wardrobe_similarity: float | None


@dataclass(frozen=True)
class IdentityDecision:
    accepted: bool
    reference_id: str
    evaluator: str
    frames_checked: int
    failures: tuple[str, ...] = field(default_factory=tuple)


def _validate01(name: str, value: float) -> float:
    value = float(value)
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be normalized to [0, 1]")
    return value


def evaluate_identity(
    observations: Iterable[IdentityObservation],
    *,
    reference_id: str,
    evaluator: str,
    limits: Mapping[str, float] | None = None,
    require_face: bool = True,
) -> IdentityDecision:
    """Fail closed on identity drift using evaluator-produced similarities.

    Face evidence is evaluated per visible sampled frame. Body/wardrobe evidence is
    enforced whenever supplied, allowing profile/back-facing frames to remain useful.
    A shot with no usable face evidence fails when ``require_face`` is true. Thresholds
    are policy defaults, not biometric truth; production calibration must use the
    actual approved reference set and evaluator.
    """
    if not reference_id.strip() or not evaluator.strip():
        raise ValueError("reference_id and evaluator provenance are required")
    thresholds = dict(DEFAULT_LIMITS)
    if limits:
        thresholds.update(limits)
    for key, value in thresholds.items():
        _validate01(f"limit:{key}", value)

    rows = list(observations)
    if not rows:
        return IdentityDecision(False, reference_id, evaluator, 0, ("missing_identity_observations",))

    failures: list[str] = []
    face_scores: list[tuple[int, float]] = []
    for row in rows:
        if row.face_similarity is not None:
            face = _validate01("face_similarity", row.face_similarity)
            face_scores.append((row.frame_index, face))
            if face < thresholds["min_face_similarity"]:
                failures.append(f"face_identity_drift:frame={row.frame_index}:score={face:.3f}")
        if row.body_similarity is not None:
            body = _validate01("body_similarity", row.body_similarity)
            if body < thresholds["min_body_similarity"]:
                failures.append(f"body_identity_drift:frame={row.frame_index}:score={body:.3f}")
        if row.wardrobe_similarity is not None:
            wardrobe = _validate01("wardrobe_similarity", row.wardrobe_similarity)
            if wardrobe < thresholds["min_wardrobe_similarity"]:
                failures.append(f"wardrobe_drift:frame={row.frame_index}:score={wardrobe:.3f}")

    if require_face and not face_scores:
        failures.append("missing_face_identity_evidence")
    if len(face_scores) >= 2:
        values = [score for _, score in face_scores]
        drift = max(values) - min(values)
        if drift > thresholds["max_face_drift"]:
            failures.append(f"temporal_face_drift:range={drift:.3f}")

    return IdentityDecision(not failures, reference_id, evaluator, len(rows), tuple(failures))
