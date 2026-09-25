from __future__ import annotations
from datetime import datetime, timezone
import math
from .models import Opportunity, PayoutType, ScoreBreakdown


def _clamp5(value: int) -> float:
    return max(1, min(5, int(value))) / 5.0


def _days_left(deadline: str | None) -> float | None:
    if not deadline:
        return None
    try:
        raw = deadline.replace("Z", "+00:00")
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (dt.astimezone(timezone.utc) - datetime.now(timezone.utc)).total_seconds() / 86400
    except (TypeError, ValueError):
        return None


def score(op: Opportunity) -> ScoreBreakdown:
    reasons: list[str] = []
    payout = min(math.log1p(max(op.payout_amount, 0)) / math.log1p(10000), 1) * 28
    certainty_weight = {
        PayoutType.CONTRACT: 1.0,
        PayoutType.FIXED: 0.9,
        PayoutType.COMPETITIVE: 0.45,
        PayoutType.CRYPTO: 0.35,
        PayoutType.CREDIT: 0.15,
        PayoutType.UNKNOWN: 0.05,
    }[op.payout_type]
    certainty = certainty_weight * 18
    certainty += 4 if op.submission_route_verified else 0
    certainty += 4 if op.payout_route_verified else 0
    certainty += 4 if op.eligibility_verified else 0
    fit = _clamp5(op.fit) * 14
    reuse = _clamp5(op.hal_reuse) * 8
    evidence = _clamp5(op.evidence_quality) * 6
    contention = (1.2 - _clamp5(op.contention)) * 8
    payout_per_hour = max(op.payout_amount, 1) / max(op.effort_hours, 1)
    effort = min(math.log1p(payout_per_hour) / math.log1p(500), 1) * 10

    urgency = 0.0
    days = _days_left(op.deadline)
    if days is not None:
        if days < 0:
            urgency -= 40
            reasons.append("deadline expired")
        elif days <= 2:
            urgency += 8
            reasons.append("deadline within 48h")
        elif days <= 7:
            urgency += 6
        elif days <= 21:
            urgency += 3

    penalties = 0.0
    if not op.eligibility_verified:
        penalties -= 8
        reasons.append("eligibility unverified")
    if not op.submission_route_verified:
        penalties -= 7
        reasons.append("submission route unverified")
    if op.blockers:
        penalties -= min(20, 4 * len(op.blockers))
        reasons.extend(op.blockers[:3])
    if op.payout_type in {PayoutType.COMPETITIVE, PayoutType.CRYPTO, PayoutType.UNKNOWN}:
        reasons.append(f"{op.payout_type.value} payout receives certainty discount")

    total = max(0.0, min(100.0, payout + certainty + fit + urgency + contention + effort + reuse + evidence + penalties))
    return ScoreBreakdown(
        total=round(total, 1), payout=round(payout, 1), certainty=round(certainty, 1),
        fit=round(fit, 1), urgency=round(urgency, 1), contention=round(contention, 1),
        effort=round(effort, 1), reuse=round(reuse, 1), evidence=round(evidence, 1),
        penalties=round(penalties, 1), reasons=reasons,
    )
