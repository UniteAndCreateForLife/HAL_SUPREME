from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from html import escape
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
    if set(forwarded) != {
        "capability_id",
        "input_fields",
        "message_body_chars",
        "message_body_sha256",
        "message_sid_forwarded",
        "phone_number_fields_forwarded",
    }:
        raise ValueError("forwarded payload is not minimized")
    expected_fields = {
        "conversation_id",
        "text",
        "provider_mode",
        "conversation_profile",
        "max_tokens",
        "present_on_oracle",
    }
    input_fields = forwarded.get("input_fields")
    body_hash = forwarded.get("message_body_sha256")
    if (
        forwarded.get("capability_id") != "operator.conversation"
        or not isinstance(input_fields, list)
        or any(not isinstance(item, str) for item in input_fields)
        or set(input_fields) != expected_fields
        or not isinstance(forwarded.get("message_body_chars"), int)
        or forwarded.get("message_body_chars", 0) <= 0
        or not isinstance(body_hash, str)
        or len(body_hash) != 64
        or any(char not in "0123456789abcdef" for char in body_hash)
        or forwarded.get("message_sid_forwarded") is not False
        or forwarded.get("phone_number_fields_forwarded") is not False
    ):
        raise ValueError("forwarded payload is not minimized")


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
            "outcome": "A valid signed request enters the canonical operator.conversation Gateway contract and returns local mock TwiML; a bad signature fails closed before the Gateway.",
            "ai_decision_moment": "The local rehearsal exercises the canonical Gateway payload and a mock verified provider response. It does not prove live HAL inference.",
            "twilio_role": "Twilio Messaging supplies the webhook contract, SDK signature validation, and TwiML response path.",
        },
        "judge_criteria": {
            "creativity": {
                "status": "technical_evidence_present",
                "evidence": "Twilio Messaging is used as a bounded HAL operator channel with fail-closed signature validation.",
            },
            "technical_impact": {
                "status": "technical_evidence_present",
                "evidence": "Official Twilio SDK signature validation, minimized operator.conversation payload construction, and TwiML serialization are exercised locally against a mock Gateway and provider response.",
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
            "HAL Operator Gateway operator.conversation",
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


def render_html(packet: dict[str, object]) -> str:
    def e(value: object) -> str:
        return escape(str(value), quote=True)

    framework = packet["demo_framework"]
    criteria = packet["judge_criteria"]
    architecture = packet["architecture"]
    gates = packet["human_account_gates"]
    boundaries = packet["boundaries"]

    criteria_html = "\n".join(
        (
            '<article class="card">'
            f"<h3>{e(name.replace('_', ' ').title())}</h3>"
            f'<p class="status">{e(item["status"].replace("_", " ").upper())}</p>'
            f"<p>{e(item['evidence'])}</p>"
            "</article>"
        )
        for name, item in criteria.items()
    )
    architecture_html = "\n".join(
        f"<li><span>{index}</span>{e(step)}</li>"
        for index, step in enumerate(architecture, start=1)
    )
    gates_html = "\n".join(f"<li>{e(gate)}</li>" for gate in gates)
    boundary_html = "\n".join(
        (
            "<tr>"
            f'<th scope="row">{e(name.replace("_", " ").title())}</th>'
            f'<td><span class="not-verified">NOT VERIFIED</span></td>'
            "</tr>"
        )
        for name, verified in boundaries.items()
        if verified is False
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Twilio Searchlight judge-readiness report</title>
<style>
:root {{ color-scheme: dark; --ink:#f8fbff; --muted:#b7c5d6; --panel:#142238;
  --accent:#39e7c2; --warning:#ffd166; --line:#37506f; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:#08111f; color:var(--ink); font:16px/1.55 system-ui,sans-serif; }}
a {{ color:var(--accent); }}
.skip {{ position:absolute; left:-9999px; top:1rem; }}
.skip:focus {{ left:1rem; padding:.75rem; background:#fff; color:#000; z-index:10; }}
header,main,footer {{ width:min(1100px,calc(100% - 2rem)); margin:auto; }}
header {{ padding:3rem 0 1.5rem; }}
.eyebrow,.status {{ color:var(--accent); font-weight:800; letter-spacing:.08em; }}
h1 {{ max-width:16ch; font-size:clamp(2rem,7vw,4.5rem); line-height:1.02; margin:.3rem 0 1rem; }}
.lede {{ max-width:72ch; color:var(--muted); }}
.badges {{ display:flex; flex-wrap:wrap; gap:.6rem; margin:1.5rem 0; }}
.badge,.not-verified {{ border:2px solid var(--warning); border-radius:999px; color:var(--warning);
  display:inline-block; font-weight:800; padding:.25rem .7rem; }}
section {{ margin:1rem 0 2rem; padding:clamp(1rem,4vw,2rem); background:var(--panel);
  border:1px solid var(--line); border-radius:1rem; }}
.grid {{ display:grid; gap:1rem; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); }}
.card {{ border-left:4px solid var(--accent); padding:0 1rem; }}
dl {{ display:grid; grid-template-columns:minmax(9rem,1fr) 3fr; gap:.7rem 1rem; }}
dt {{ font-weight:800; }}
dd {{ margin:0; color:var(--muted); }}
.flow {{ list-style:none; display:flex; flex-wrap:wrap; gap:.65rem; padding:0; }}
.flow li {{ background:#0b1728; border:1px solid var(--line); border-radius:.6rem; padding:.65rem; }}
.flow li span {{ color:var(--accent); font-weight:800; margin-right:.5rem; }}
table {{ width:100%; border-collapse:collapse; }}
th,td {{ text-align:left; padding:.75rem; border-bottom:1px solid var(--line); }}
footer {{ color:var(--muted); padding:0 0 3rem; overflow-wrap:anywhere; }}
@media (max-width:600px) {{ dl {{ grid-template-columns:1fr; }} dd {{ margin-bottom:.7rem; }}
  th,td {{ display:block; }} td {{ padding-top:0; }} }}
</style>
</head>
<body>
<a class="skip" href="#evidence">Skip to evidence</a>
<header>
<p class="eyebrow">SOURCE-BOUND LOCAL REHEARSAL</p>
<h1>HAL operator control through Twilio Messaging</h1>
<p class="lede">{e(framework["story"])}</p>
<div class="badges">
<span class="badge">LOCAL REHEARSAL PASSED</span>
<span class="not-verified">LIVE TWILIO NOT VERIFIED</span>
</div>
<p>Source SHA: <code>{e(packet["source_sha"])}</code></p>
</header>
<main id="evidence">
<section aria-labelledby="boundary-title">
<h2 id="boundary-title">Evidence boundary</h2>
<p>This report proves a deterministic, source-bound local rehearsal. It is not a live
Twilio account demo, application receipt, honoree selection, credit award, or payment receipt.</p>
<table>
<caption>Claims intentionally held as unverified</caption>
<tbody>{boundary_html}</tbody>
</table>
</section>
<section aria-labelledby="story-title">
<h2 id="story-title">One story, one persona, one outcome</h2>
<dl>
<dt>Persona</dt><dd>{e(framework["persona"])}</dd>
<dt>Outcome</dt><dd>{e(framework["outcome"])}</dd>
<dt>AI decision moment</dt><dd>{e(framework["ai_decision_moment"])}</dd>
<dt>Twilio role</dt><dd>{e(framework["twilio_role"])}</dd>
</dl>
</section>
<section aria-labelledby="architecture-title">
<h2 id="architecture-title">Request architecture</h2>
<ol class="flow" aria-label="Twilio to HAL architecture">{architecture_html}</ol>
</section>
<section aria-labelledby="criteria-title">
<h2 id="criteria-title">Judging-criteria evidence map</h2>
<div class="grid">{criteria_html}</div>
</section>
<section aria-labelledby="gates-title">
<h2 id="gates-title">Human and account gates</h2>
<ol>{gates_html}</ol>
</section>
<section aria-labelledby="state-title">
<h2 id="state-title">Machine-readable state</h2>
<dl>
<dt>Technical rehearsal ready</dt><dd>{e(str(packet["technical_rehearsal_ready"]).lower())}</dd>
<dt>Live working demo verified</dt><dd><span class="not-verified">NOT VERIFIED</span></dd>
<dt>Application ready</dt><dd><span class="not-verified">NOT VERIFIED</span></dd>
<dt>Submission</dt><dd>{e(packet["submission_state"])}</dd>
<dt>Award</dt><dd>{e(packet["award_state"])}</dd>
<dt>Payment</dt><dd>{e(packet["payment_state"])}</dd>
</dl>
</section>
</main>
<footer>
<p>Official deadline as published: {e(packet["deadline_as_published"])}</p>
<p>Program source: <a href="{e(packet["program_url"])}">{e(packet["program_url"])}</a></p>
</footer>
</body>
</html>
"""


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
    parser.add_argument("--html-output", type=Path, required=True)
    args = parser.parse_args()

    source_sha = current_source_sha()
    receipt = load_json(args.rehearsal)
    packet = build_judge_packet(receipt, source_sha)
    write_json(args.json_output, packet)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.write_text(
        render_markdown(packet), encoding="utf-8", newline="\n"
    )
    args.html_output.parent.mkdir(parents=True, exist_ok=True)
    args.html_output.write_text(render_html(packet), encoding="utf-8", newline="\n")
    print(json.dumps(packet, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
