"""Human-gated job application preparation for HAL SUPREME.

The module prepares truthful application payloads from an approved profile while
keeping identity, legal, payment, demographic, authentication, and attestation
fields under explicit human control. It does not scrape sites, bypass anti-bot
measures, or claim that an application was submitted without a receipt.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Iterable, Mapping


APPLICATION_STAGES = (
    "discovered",
    "qualified",
    "application_ready",
    "prepared",
    "approved",
    "submitted",
    "assessment",
    "interview",
    "accepted",
    "matched",
    "closed",
)

HUMAN_ONLY_PATTERNS = (
    r"password|passcode|otp|one[- ]?time|mfa|2fa|captcha",
    r"social security|\bssn\b|tax id|ein|routing number|bank account|card number",
)
CONFIRM_PATTERNS = (
    r"work authorization|authorized to work|visa|sponsorship|citizenship",
    r"race|ethnicity|gender|sex|veteran|disability|demographic",
    r"background check|criminal|conviction|drug test",
    r"date of birth|birth date|age\b",
    r"signature|certify|attest|i agree|terms|consent|non[- ]?compete|confidentiality",
    r"salary expectation|compensation expectation|desired salary|desired rate",
)
DRAFT_PATTERNS = (
    r"cover letter|why (?:are|do|would)|tell us|describe|summary|additional information",
    r"experience with|project example|portfolio note|motivation|interest in",
)

FIELD_ALIASES = {
    "name": ("name", "full name", "preferred name"),
    "email": ("email", "email address"),
    "phone": ("phone", "phone number", "mobile"),
    "location": ("location", "city", "city/state", "city, state"),
    "website": ("website", "personal website", "site"),
    "portfolio": ("portfolio", "portfolio url", "portfolio link"),
    "github": ("github", "github url", "github profile"),
    "linkedin": ("linkedin", "linkedin url", "linkedin profile"),
}


def _norm(value: Any) -> str:
    text = str(value or "").strip().lower()
    return re.sub(r"\s+", " ", text)


def classify_field(field: Mapping[str, Any]) -> str:
    """Classify one application field by the minimum required human control."""
    label = " ".join(
        _norm(field.get(key)) for key in ("label", "name", "placeholder", "help")
    )
    field_type = _norm(field.get("type"))
    if field_type in {"password", "file_secret"} or any(
        re.search(pattern, label) for pattern in HUMAN_ONLY_PATTERNS
    ):
        return "human_only"
    if field_type in {"checkbox_attestation", "signature"} or any(
        re.search(pattern, label) for pattern in CONFIRM_PATTERNS
    ):
        return "requires_confirmation"
    if field_type in {"textarea", "long_text"} or any(
        re.search(pattern, label) for pattern in DRAFT_PATTERNS
    ):
        return "draft_only"
    return "auto_fill"


def profile_key_for_field(field: Mapping[str, Any]) -> str | None:
    explicit = _norm(field.get("profile_key"))
    if explicit:
        return explicit
    label = _norm(field.get("label") or field.get("name"))
    for key, aliases in FIELD_ALIASES.items():
        if label in aliases:
            return key
    return None


def _field_id(field: Mapping[str, Any], index: int) -> str:
    return str(field.get("id") or field.get("name") or f"field_{index}")


def build_application_plan(
    job: Mapping[str, Any],
    fields: Iterable[Mapping[str, Any]],
    profile: Mapping[str, Any],
    drafted_responses: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a deterministic preview without performing an external write."""
    drafted_responses = drafted_responses or {}
    prepared_fields: list[dict[str, Any]] = []
    blockers: list[str] = []
    confirmations: list[str] = []

    for index, field in enumerate(fields):
        field_id = _field_id(field, index)
        control = classify_field(field)
        profile_key = profile_key_for_field(field)
        value = None
        source = "unset"

        if control == "auto_fill" and profile_key:
            value = profile.get(profile_key)
            source = f"profile:{profile_key}" if value not in (None, "") else "unset"
        elif control == "draft_only":
            value = drafted_responses.get(field_id)
            source = "draft" if value not in (None, "") else "unset"
        elif control == "requires_confirmation":
            value = drafted_responses.get(field_id)
            source = "user_confirmed_value_pending" if value not in (None, "") else "unset"
            confirmations.append(field_id)
        else:
            blockers.append(field_id)

        required = bool(field.get("required", False))
        if required and value in (None, "") and control != "human_only":
            blockers.append(field_id)

        prepared_fields.append(
            {
                "id": field_id,
                "label": str(field.get("label") or field.get("name") or field_id),
                "control": control,
                "required": required,
                "profile_key": profile_key,
                "value": value,
                "source": source,
            }
        )

    plan = {
        "schema_version": 1,
        "job": {
            "id": str(job.get("id") or "unknown"),
            "provider": str(job.get("provider") or "unknown"),
            "title": str(job.get("title") or "Unknown role"),
            "url": str(job.get("url") or ""),
        },
        "stage": "prepared",
        "fields": prepared_fields,
        "requires_confirmation": sorted(set(confirmations)),
        "blockers": sorted(set(blockers)),
        "submission_authorized": False,
    }
    plan["digest"] = plan_digest(plan)
    return plan


def plan_digest(plan: Mapping[str, Any]) -> str:
    canonical = {
        "job": plan.get("job"),
        "fields": plan.get("fields"),
        "requires_confirmation": plan.get("requires_confirmation"),
        "blockers": plan.get("blockers"),
    }
    raw = json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def approval_phrase(plan: Mapping[str, Any]) -> str:
    return f"APPROVE {str(plan.get('digest') or '')[:12]}"


def authorize_plan(plan: Mapping[str, Any], phrase: str) -> dict[str, Any]:
    """Authorize one already-reviewed plan; blocked plans cannot be authorized."""
    if plan.get("blockers"):
        raise ValueError("plan has unresolved or human-only blockers")
    if _norm(phrase) != _norm(approval_phrase(plan)):
        raise ValueError("approval phrase does not match this exact plan")
    approved = dict(plan)
    approved["stage"] = "approved"
    approved["submission_authorized"] = True
    return approved


def mark_submitted(plan: Mapping[str, Any], receipt: Mapping[str, Any]) -> dict[str, Any]:
    """Promote to submitted only when an external system returns concrete evidence."""
    if plan.get("stage") != "approved" or plan.get("submission_authorized") is not True:
        raise ValueError("submission was not explicitly approved")
    receipt_id = str(receipt.get("id") or receipt.get("confirmation") or "").strip()
    receipt_url = str(receipt.get("url") or "").strip()
    if not receipt_id and not receipt_url:
        raise ValueError("submission receipt evidence is required")
    submitted = dict(plan)
    submitted["stage"] = "submitted"
    submitted["submission_receipt"] = dict(receipt)
    return submitted
