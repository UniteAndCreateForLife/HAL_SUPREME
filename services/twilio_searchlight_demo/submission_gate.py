from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
REQUIRED_FALSE_BOUNDARIES = (
    "application_submitted",
    "honoree_selected",
    "credits_awarded",
    "payment_received",
    "money_spent",
)


def current_source_sha() -> str:
    repo_root = Path(__file__).resolve().parents[2]
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repo_root, text=True
    ).strip()


def load_json(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_judge_packet(packet: dict[str, object], source_sha: str) -> None:
    if packet.get("schema_version") != 1:
        raise ValueError("unsupported judge packet schema")
    if packet.get("source_sha") != source_sha:
        raise ValueError("judge packet source SHA does not match current source")
    if packet.get("technical_rehearsal_ready") is not True:
        raise ValueError("judge packet technical rehearsal is not ready")
    boundaries = packet.get("boundaries")
    if not isinstance(boundaries, dict):
        raise ValueError("judge packet boundaries are missing")
    for name in REQUIRED_FALSE_BOUNDARIES:
        if boundaries.get(name) is not False:
            raise ValueError(f"judge packet boundary must remain false: {name}")


def validate_interaction_receipt(receipt: dict[str, object], source_sha: str) -> None:
    if receipt.get("schema_version") != 1:
        raise ValueError("unsupported interaction receipt schema")
    if receipt.get("source_sha") != source_sha:
        raise ValueError("interaction receipt source SHA does not match current source")
    interaction = receipt.get("interaction")
    if not isinstance(interaction, dict):
        raise ValueError("interaction receipt payload is missing")
    if interaction.get("status") != "ok":
        raise ValueError("interaction receipt is not successful")
    if interaction.get("signature_validation") != "twilio_sdk":
        raise ValueError("interaction receipt did not use Twilio SDK validation")
    if interaction.get("delivery_status") != "new":
        raise ValueError("interaction receipt is not for a newly processed delivery")
    if not re.fullmatch(r"[0-9a-f]{12}", str(interaction.get("message_ref", ""))):
        raise ValueError("interaction receipt message reference is invalid")
    if not str(interaction.get("decision_id", "")).strip():
        raise ValueError("interaction receipt decision id is missing")
    for name in ("webhook_url_sha256", "twiml_sha256"):
        if not HEX64_RE.fullmatch(str(interaction.get(name, ""))):
            raise ValueError(f"interaction receipt {name} is invalid")
    privacy = receipt.get("privacy")
    if not isinstance(privacy, dict) or any(
        privacy.get(name) is not False
        for name in (
            "phone_number_recorded",
            "message_body_recorded",
            "auth_token_recorded",
            "webhook_url_recorded",
        )
    ):
        raise ValueError("interaction receipt privacy boundary is invalid")
    boundaries = receipt.get("boundaries")
    if not isinstance(boundaries, dict):
        raise ValueError("interaction receipt boundaries are missing")
    for name in REQUIRED_FALSE_BOUNDARIES:
        if boundaries.get(name) is not False:
            raise ValueError(f"interaction receipt boundary must remain false: {name}")


def build_submission_readiness(
    judge_packet: dict[str, object],
    source_sha: str,
    interaction_receipt: dict[str, object] | None = None,
) -> dict[str, object]:
    source_sha = source_sha.strip().lower()
    if not GIT_SHA_RE.fullmatch(source_sha):
        raise ValueError("source SHA must be an exact 40-character Git SHA")
    validate_judge_packet(judge_packet, source_sha)
    live_verified = interaction_receipt is not None
    if interaction_receipt is not None:
        validate_interaction_receipt(interaction_receipt, source_sha)

    blockers = []
    if not live_verified:
        blockers.append("genuine_signed_twilio_interaction_receipt_missing")
    blockers.append("human_application_attestations_pending")
    return {
        "schema_version": 1,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_sha": source_sha,
        "technical_rehearsal_ready": True,
        "genuine_signed_twilio_interaction_verified": live_verified,
        "machine_evidence_ready": live_verified,
        "human_application_attestations_complete": False,
        "application_ready": False,
        "submission_state": "not_submitted",
        "award_state": "not_awarded",
        "payment_state": "not_paid",
        "blockers": blockers,
        "boundaries": {name: False for name in REQUIRED_FALSE_BOUNDARIES},
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a fail-closed Twilio Searchlight submission readiness receipt."
    )
    parser.add_argument("--judge-packet", type=Path, required=True)
    parser.add_argument("--interaction-receipt", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    source_sha = current_source_sha()
    judge_packet = load_json(args.judge_packet)
    interaction = (
        load_json(args.interaction_receipt) if args.interaction_receipt else None
    )
    readiness = build_submission_readiness(judge_packet, source_sha, interaction)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(readiness, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(readiness, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
