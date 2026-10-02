from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
REQUIRED_FALSE_BOUNDARIES = (
    "live_twilio_account_verified",
    "application_submitted",
    "honoree_selected",
    "credits_awarded",
    "payment_received",
    "money_spent",
)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def build_interaction_receipt(
    event: dict[str, str],
    source_sha: str,
    webhook_url: str,
    twiml: str,
) -> dict[str, object]:
    source_sha = source_sha.strip().lower()
    if not GIT_SHA_RE.fullmatch(source_sha):
        raise ValueError(
            "HAL_SEARCHLIGHT_SOURCE_SHA must be an exact 40-character Git SHA"
        )
    if event.get("status") != "ok":
        raise ValueError("only successful validated interactions may produce receipts")
    delivery_status = event.get("delivery_status", "").strip()
    if delivery_status != "new":
        raise ValueError(
            "only newly processed deliveries may produce interaction receipts"
        )
    message_ref = event.get("message_ref", "").strip().lower()
    if not re.fullmatch(r"[0-9a-f]{12}", message_ref):
        raise ValueError(
            "interaction event has no valid privacy-preserving message_ref"
        )
    decision_id = event.get("decision_id", "").strip()
    if not decision_id:
        raise ValueError("interaction event has no decision_id")
    if not webhook_url.startswith("https://"):
        raise ValueError(
            "receipt capture requires the configured public HTTPS webhook URL"
        )

    boundaries = {name: False for name in REQUIRED_FALSE_BOUNDARIES}
    return {
        "schema_version": 1,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_sha": source_sha,
        "scope": (
            "successful signature-validated webhook-to-HAL interaction evidence; "
            "not proof of Twilio account ownership, Searchlight eligibility, submission, award, or payment"
        ),
        "interaction": {
            "status": "ok",
            "signature_validation": "twilio_sdk",
            "delivery_status": delivery_status,
            "message_ref": message_ref,
            "decision_id": decision_id,
            "elapsed_ms": event.get("elapsed_ms", ""),
            "webhook_url_sha256": _sha256_text(webhook_url),
            "twiml_sha256": _sha256_text(twiml),
        },
        "privacy": {
            "phone_number_recorded": False,
            "message_body_recorded": False,
            "auth_token_recorded": False,
            "webhook_url_recorded": False,
        },
        "boundaries": boundaries,
    }


def write_interaction_receipt(
    output_dir: Path,
    event: dict[str, str],
    source_sha: str,
    webhook_url: str,
    twiml: str,
) -> Path:
    receipt = build_interaction_receipt(event, source_sha, webhook_url, twiml)
    output_dir.mkdir(parents=True, exist_ok=True)
    message_ref = str(receipt["interaction"]["message_ref"])
    destination = output_dir / f"interaction-{message_ref}.json"
    temporary = destination.with_suffix(".json.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(receipt, handle, indent=2, sort_keys=True)
        handle.write("\n")
    temporary.replace(destination)
    return destination
