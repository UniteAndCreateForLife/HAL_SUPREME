"""HAL Studio anti-repetition admission worker.

This module compares evaluator-produced normalized similarity signals for a candidate
shot against already accepted shots. It never commits production state: the existing
HAL supervisor remains the sole admission authority.

Similarity inputs are intentionally renderer-agnostic so CLIP/DINO/video embeddings,
camera/action classifiers, or future evaluators can feed the same deterministic gate.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping


DEFAULT_LIMITS = {
    "visual_similarity": 0.94,
    "composition_similarity": 0.92,
    "motion_similarity": 0.93,
}


@dataclass(frozen=True)
class PriorShotSimilarity:
    shot_id: str
    visual_similarity: float
    composition_similarity: float
    motion_similarity: float


@dataclass(frozen=True)
class RepetitionDecision:
    accepted: bool
    max_repetition_score: float
    nearest_shot_id: str | None
    failures: tuple[str, ...] = field(default_factory=tuple)


def _validate01(name: str, value: float) -> float:
    value = float(value)
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be normalized to [0, 1]")
    return value


def evaluate_repetition(
    comparisons: Iterable[PriorShotSimilarity],
    *,
    limits: Mapping[str, float] | None = None,
    intentional_repeat: bool = False,
) -> RepetitionDecision:
    """Reject accidental near-duplicates while allowing manifest-declared callbacks.

    A comparison fails when visual similarity is excessive AND either composition or
    motion is also excessive. This avoids rejecting legitimate continuity shots that
    share a character/location but introduce a genuinely different camera or action.
    Missing comparisons fail closed unless this is the first accepted shot; callers
    represent the first shot with an empty iterable and accept that case explicitly.
    """
    thresholds = dict(DEFAULT_LIMITS)
    if limits:
        thresholds.update(limits)
    for key, value in thresholds.items():
        _validate01(f"limit:{key}", value)

    rows = list(comparisons)
    if intentional_repeat:
        return RepetitionDecision(True, 0.0, None, ())
    if not rows:
        return RepetitionDecision(True, 0.0, None, ())

    failures: list[str] = []
    nearest_id: str | None = None
    max_score = 0.0
    for row in rows:
        v = _validate01("visual_similarity", row.visual_similarity)
        c = _validate01("composition_similarity", row.composition_similarity)
        m = _validate01("motion_similarity", row.motion_similarity)
        score = (v + c + m) / 3.0
        if score > max_score:
            max_score, nearest_id = score, row.shot_id
        if v >= thresholds["visual_similarity"] and (
            c >= thresholds["composition_similarity"]
            or m >= thresholds["motion_similarity"]
        ):
            failures.append(
                f"near_duplicate:{row.shot_id}:visual={v:.3f}:composition={c:.3f}:motion={m:.3f}"
            )

    return RepetitionDecision(not failures, round(max_score, 4), nearest_id, tuple(failures))
