from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Iterable


SCHEMA = "hal.agent_task.v1"
STATUS_ORDER = (
    "planned",
    "implementing",
    "implemented",
    "focused_verified",
    "regression_verified",
    "reviewed",
    "promotion_ready",
    "promoted",
)
PROTECTED_ACTIONS = {
    "merge",
    "deploy",
    "publish",
    "spend",
    "external_message",
    "credential_change",
    "identity_change",
    "destructive_data_operation",
}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _non_empty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_list(
    payload: dict[str, Any],
    field: str,
    errors: list[str],
    *,
    required: bool,
) -> list[str]:
    value = payload.get(field)
    if not isinstance(value, list):
        if required:
            errors.append(f"{field} must be a list")
        return []
    invalid = [item for item in value if not _non_empty_string(item)]
    if invalid:
        errors.append(f"{field} entries must be non-empty strings")
    if required and not value:
        errors.append(f"{field} must not be empty")
    return [item.strip() for item in value if _non_empty_string(item)]


def _stage_at_least(status: str, required: str) -> bool:
    try:
        return STATUS_ORDER.index(status) >= STATUS_ORDER.index(required)
    except ValueError:
        return False


def _matching_pass(
    verification: Iterable[object],
    *,
    kind: str,
    revision: str,
) -> bool:
    for item in verification:
        if not isinstance(item, dict):
            continue
        if (
            item.get("kind") == kind
            and item.get("outcome") == "passed"
            and item.get("revision") == revision
            and _non_empty_string(item.get("command"))
            and _non_empty_string(item.get("worker"))
        ):
            evidence = item.get("evidence_sha256")
            if evidence is None or (isinstance(evidence, str) and SHA256_RE.fullmatch(evidence)):
                return True
    return False


def validate_task_packet(payload: object) -> list[str]:
    """Return validation errors for a HAL agent task packet.

    The contract is deliberately independent of any model/provider. It validates
    progression claims, revision pinning, independent review, and authorization
    evidence for protected promotion actions.
    """

    if not isinstance(payload, dict):
        return ["task packet root must be an object"]

    errors: list[str] = []

    for field in (
        "schema",
        "task_id",
        "objective",
        "scope",
        "constraints",
        "protected_actions",
        "acceptance",
        "status",
        "verification",
    ):
        if field not in payload:
            errors.append(f"missing required field: {field}")

    if payload.get("schema") != SCHEMA:
        errors.append(f"schema must be {SCHEMA}")

    task_id = payload.get("task_id")
    if not _non_empty_string(task_id) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{2,127}", task_id.strip()):
        errors.append("task_id is invalid")

    if not _non_empty_string(payload.get("objective")):
        errors.append("objective must be a non-empty string")

    _string_list(payload, "scope", errors, required=True)
    _string_list(payload, "constraints", errors, required=False)
    acceptance = _string_list(payload, "acceptance", errors, required=True)
    if not acceptance:
        errors.append("at least one acceptance criterion is required")

    protected = _string_list(payload, "protected_actions", errors, required=False)
    unknown_actions = sorted(set(protected) - PROTECTED_ACTIONS)
    if unknown_actions:
        errors.append(f"unknown protected_actions: {', '.join(unknown_actions)}")

    status = payload.get("status")
    if status not in STATUS_ORDER:
        errors.append(f"status must be one of: {', '.join(STATUS_ORDER)}")
        return errors

    revision = payload.get("revision")
    implementer = payload.get("implementer")

    verification = payload.get("verification", [])
    if not isinstance(verification, list):
        errors.append("verification must be a list")
        verification = []
    else:
        for index, item in enumerate(verification):
            if not isinstance(item, dict):
                errors.append(f"verification[{index}] must be an object")
                continue
            if item.get("kind") not in {"focused", "regression"}:
                errors.append(f"verification[{index}].kind must be focused or regression")
            if item.get("outcome") not in {"passed", "failed", "blocked"}:
                errors.append(f"verification[{index}].outcome is invalid")
            for field in ("command", "revision", "worker"):
                if not _non_empty_string(item.get(field)):
                    errors.append(f"verification[{index}].{field} must be a non-empty string")
            digest = item.get("evidence_sha256")
            if digest is not None and (
                not isinstance(digest, str) or not SHA256_RE.fullmatch(digest)
            ):
                errors.append(f"verification[{index}].evidence_sha256 must be a lowercase SHA-256 hex digest")

    if _stage_at_least(status, "implemented"):
        if not _non_empty_string(revision):
            errors.append(f"{status} requires a revision")
        if not _non_empty_string(implementer):
            errors.append(f"{status} requires an implementer")

    pinned_revision = revision.strip() if _non_empty_string(revision) else ""

    if _stage_at_least(status, "focused_verified") and not _matching_pass(
        verification, kind="focused", revision=pinned_revision
    ):
        errors.append("focused_verified or later requires a passing focused verification pinned to revision")

    if _stage_at_least(status, "regression_verified") and not _matching_pass(
        verification, kind="regression", revision=pinned_revision
    ):
        errors.append("regression_verified or later requires a passing regression verification pinned to revision")

    review = payload.get("review")
    if _stage_at_least(status, "reviewed"):
        if not isinstance(review, dict):
            errors.append(f"{status} requires a review object")
        else:
            reviewer = review.get("reviewer")
            if not _non_empty_string(reviewer):
                errors.append("review.reviewer must be a non-empty string")
            if review.get("outcome") != "passed":
                errors.append("reviewed or later requires review.outcome=passed")
            if review.get("revision") != pinned_revision:
                errors.append("review revision must match the task revision")
            if _non_empty_string(reviewer) and _non_empty_string(implementer) and reviewer == implementer:
                errors.append("independent review requires reviewer != implementer")

    receipt_sha256 = payload.get("receipt_sha256")
    if _stage_at_least(status, "promotion_ready"):
        if not isinstance(receipt_sha256, str) or not SHA256_RE.fullmatch(receipt_sha256):
            errors.append("promotion_ready or later requires receipt_sha256")

    promotion = payload.get("promotion")
    if status == "promoted":
        if not isinstance(promotion, dict):
            errors.append("promoted requires a promotion object")
        else:
            action = promotion.get("action")
            if action not in protected:
                errors.append("promotion.action must be listed in protected_actions")
            if promotion.get("authorized") is not True:
                errors.append("promoted requires promotion.authorized=true")
            if promotion.get("revision") != pinned_revision:
                errors.append("promotion revision must match the task revision")
            if not _non_empty_string(promotion.get("event_id")):
                errors.append("promoted requires promotion.event_id")

    return errors


def load_task_packet(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_file(path: Path) -> dict[str, Any]:
    try:
        payload = load_task_packet(path)
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "schema": "hal.agent_task_validation.v1",
            "ok": False,
            "path": str(path),
            "errors": [f"could not load task packet: {exc}"],
        }

    errors = validate_task_packet(payload)
    return {
        "schema": "hal.agent_task_validation.v1",
        "ok": not errors,
        "path": str(path),
        "task_id": payload.get("task_id") if isinstance(payload, dict) else None,
        "status": payload.get("status") if isinstance(payload, dict) else None,
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a HAL agent task packet")
    parser.add_argument("path", type=Path)
    args = parser.parse_args(argv)
    report = validate_file(args.path)
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
