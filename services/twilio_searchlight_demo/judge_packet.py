from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

PROGRAM_URL = "https://www.twilio.com/en-us/lp/twilio-ai-startup-searchlight"
DEADLINE_AS_PUBLISHED = "Friday, September 25th, 2026 at 11:45 pm PST"
REQUIRED_FALSE_BOUNDARIES = (
    "live_twilio_account_verified",
    "external_twilio_api_call",
    "money_spent",
    "application_submitted",
    "honoree_selected",
    "credits_awarded",
    "payment_received",
)


def current_source_sha() -> str:
    repo_root = Path(__file__).resolve().parents[2]
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repo_root, text=True
    ).strip()


def load_json(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_rehearsal(receipt: dict[str, object], source_sha: str) -> None:
    if receipt.get("schema_version") != 1:
        raise ValueError("unsupported rehearsal receipt schema")
    if receipt.get("source_sha") != source_sha:
        raise ValueError("rehearsal receipt source SHA does not match current source")
    if receipt.get("passed") is not True:
        raise ValueError("rehearsal receipt is not passing")

    checks = receipt.get("checks")
    if not isinstance(checks, dict) or not checks or not all(checks.values()):
        raise ValueError("rehearsal checks are incomplete or failing")

    boundaries = receipt.get("boundaries")
    if not isinstance(boundaries, dict):
        raise ValueError("rehearsal boundaries are missing")
    for name in REQUIRED_FALSE_BOUNDARIES:
        if boundaries.get(name) is not False:
            raise ValueError(f"rehearsal boundary must remain false: {name}")

    forwarded = receipt.get("forwarded_payload")
    if not isinstance(forwarded, dict):
        raise ValueError("forwarded payload evidence is missing")
    if set(forwarded) != {"channel", "message_sid", "body"}:
        raise ValueError("forwarded payload is not minimized")
    if forwarded.get("channel") != "twilio_sms":
        raise ValueError("forwarded channel is not Twilio SMS")


def build_judge_packet(
    receipt: dict[str, object], source_sha: str
) -> dict[str, object]:
    validate_rehearsal(receipt, source_sha)
    return {
        "schema_version": 1,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "program": "Twilio AI Startup Searchlight 2026",
        "program_url": PROGRAM_URL,
        "deadline_as_published": DEADLINE_AS_PUBLISHED,
        "source_sha": source_sha,
        "rehearsal_source_sha": receipt["source_sha"],
        "technical_rehearsal_ready": True,
        "live_working_demo_verified": False,
        "application_ready": False,
        "submission_state": "not_submitted",
        "award_state": "not_awarded",
        "payment_state": "not_paid",
        "demo_framework": {
            "story": "A HAL operator sends one SMS request and receives one bounded HAL decision reply.",
            "persona": "HAL operator using Messaging as a low-friction control channel.",
            "outcome": "A valid signed request reaches HAL and returns TwiML; a bad signature fails closed before HAL.",
            "ai_decision_moment": "HAL receives only channel, MessageSid, and bounded body, then returns a decision reply.",
            "twilio_role": "Twilio Messaging supplies the webhook contract, SDK signature validation, and TwiML response path.",
        },
        "judge_criteria": {
            "creativity": {
                "status": "technical_evidence_present",
                "evidence": "Twilio Messaging is used as a bounded HAL operator channel with fail-closed signature validation.",
            },
            "technical_impact": {
                "status": "technical_evidence_present",
                "evidence": "Official Twilio SDK signature validation, minimized HAL forwarding, and TwiML response are exercised locally.",
            },
            "long_term_impact": {
                "status": "human_narrative_required",
                "evidence": "No production or user-impact claim is inferred from the local rehearsal.",
            },
            "market_impact": {
                "status": "human_evidence_required",
                "evidence": "No traction, customer, revenue, or market-adoption claim is inferred.",
            },
        },
        "architecture": [
            "Twilio Messaging",
            "HTTPS webhook",
            "Twilio SDK signature validation",
            "HAL decision endpoint",
            "TwiML reply",
        ],
        "human_account_gates": [
            "Verify an eligible Twilio account and account ownership.",
            "Configure the exact public HTTPS webhook URL in Twilio.",
            "Perform and capture one real signed inbound Twilio interaction.",
            "Confirm startup funding eligibility and applicant age truthfully.",
            "Provide an accurate startup contact and representation authority.",
            "Review the final demo and submit the official application.",
        ],
        "boundaries": {
            "live_twilio_account_verified": False,
            "external_twilio_api_call": False,
            "application_submitted": False,
            "honoree_selected": False,
            "credits_awarded": False,
            "payment_received": False,
            "money_spent": False,
        },
    }


def render_markdown(packet: dict[str, object]) -> str:
    framework = packet["demo_framework"]
    criteria = packet["judge_criteria"]
    gates = packet["human_account_gates"]
    lines = [
        "# Twilio Searchlight judge-readiness packet",
        "",
        f"Source SHA: `{packet['source_sha']}`",
        f"Official deadline as published: **{packet['deadline_as_published']}**",
        "",
        "## Evidence boundary",
        "",
        "This packet proves a source-bound local technical rehearsal. It is **not** a live Twilio account demo, application receipt, honoree selection, credit award, or payment receipt.",
        "",
        "## One story → one persona → one outcome",
        f"- **Story:** {framework['story']}",
        f"- **Persona:** {framework['persona']}",
        f"- **Outcome:** {framework['outcome']}",
        f"- **AI decision moment:** {framework['ai_decision_moment']}",
        f"- **Twilio role:** {framework['twilio_role']}",
        "",
        "## Judging-criteria evidence map",
        "",
    ]
    for name, item in criteria.items():
        lines.append(
            f"- **{name.replace('_', ' ').title()}:** {item['status']} — {item['evidence']}"
        )
    lines.extend(["", "## Human/account gates", ""])
    lines.extend(f"- {gate}" for gate in gates)
    lines.extend(
        [
            "",
            "## Current machine-readable state",
            "",
            f"- Technical rehearsal ready: `{str(packet['technical_rehearsal_ready']).lower()}`",
            f"- Live working demo verified: `{str(packet['live_working_demo_verified']).lower()}`",
            f"- Application ready: `{str(packet['application_ready']).lower()}`",
            f"- Submission state: `{packet['submission_state']}`",
            f"- Award state: `{packet['award_state']}`",
            f"- Payment state: `{packet['payment_state']}`",
            "",
        ]
    )
    return "\n".join(lines)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a source-bound Twilio Searchlight judge-readiness packet."
    )
    parser.add_argument("--rehearsal", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()

    source_sha = current_source_sha()
    receipt = load_json(args.rehearsal)
    packet = build_judge_packet(receipt, source_sha)
    write_json(args.json_output, packet)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.write_text(
        render_markdown(packet), encoding="utf-8", newline="\n"
    )
    print(json.dumps(packet, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
