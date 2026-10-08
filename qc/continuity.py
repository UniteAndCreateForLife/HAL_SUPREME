from __future__ import annotations

from typing import Any, Mapping


class ContinuityQCError(RuntimeError):
    pass


REQUIRED_DOMAINS = ("identity", "wardrobe", "set_geometry", "props", "lighting", "atmosphere")


def require_continuity_audit(audit: Mapping[str, Any], *, min_confidence: float = 0.70) -> dict[str, Any]:
    """Fail closed on visual continuity audits produced by a VLM or deterministic checker."""
    shot_id = audit.get("shot_id")
    if not isinstance(shot_id, str) or not shot_id:
        raise ContinuityQCError("continuity audit requires shot_id")
    checks = audit.get("checks")
    if not isinstance(checks, Mapping):
        raise ContinuityQCError("continuity audit requires checks mapping")

    failures: list[str] = []
    for domain in REQUIRED_DOMAINS:
        item = checks.get(domain)
        if not isinstance(item, Mapping):
            failures.append(f"{domain}:missing")
            continue
        status = item.get("status")
        confidence = item.get("confidence")
        if status != "pass":
            failures.append(f"{domain}:{status or 'unknown'}")
            continue
        if not isinstance(confidence, (int, float)) or float(confidence) < min_confidence:
            failures.append(f"{domain}:low_confidence")

    if failures:
        raise ContinuityQCError(f"shot {shot_id!r} failed continuity audit: {', '.join(failures)}")
    return {"shot_id": shot_id, "status": "pass", "domains": list(REQUIRED_DOMAINS)}
