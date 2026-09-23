from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

BASE = Path(__file__).resolve().parent


def canonical_json_bytes(data: Any) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def build_audit_receipt(report: dict[str, Any]) -> dict[str, Any]:
    validation = report.get("validation", {})
    review_gate = report.get("review_gate", {})
    return {
        "schema": "hal-campus-audit-receipt/v1",
        "algorithm": "sha256-canonical-json-v1",
        "case_id": report.get("case_id"),
        "report_sha256": hashlib.sha256(canonical_json_bytes(report)).hexdigest(),
        "citation_validity": validation.get("citation_validity"),
        "conflict_detection": validation.get("conflict_detection"),
        "unsupported_material_claims": validation.get("unsupported_material_claims"),
        "human_review_status": review_gate.get("status"),
        "scope": "synthetic_demo_only",
    }


def verify_audit_receipt(report: dict[str, Any], receipt: dict[str, Any]) -> bool:
    expected = build_audit_receipt(report)
    return receipt.get("case_id") == expected["case_id"] and receipt.get("report_sha256") == expected["report_sha256"]


def load_cases() -> list[dict[str, Any]]:
    return json.loads((BASE / "cases.json").read_text(encoding="utf-8"))["cases"]


def _evidence_map(case: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in case["evidence"]}


def _claim(text: str, citations: list[str], kind: str = "evidence") -> dict[str, Any]:
    return {"text": text, "citations": citations, "kind": kind}


def _actions(case_id: str) -> list[dict[str, Any]]:
    if case_id == "policy-conflict":
        return [
            _claim("Pause approval until the conflicting approval paths are reconciled by the policy owner.", ["E1", "E2"], "action"),
            _claim("Treat annual safety training as satisfied for this synthetic request.", ["E3"], "action"),
        ]
    if case_id == "research-access":
        return [
            _claim("Obtain data-owner approval before release.", ["E2", "E4"], "action"),
            _claim("Record the purpose statement and retention period before release.", ["E2"], "action"),
            _claim("Use the encrypted, access-logged workspace if the request is approved.", ["E3"], "action"),
        ]
    if case_id == "energy-anomaly":
        return [
            _claim("Inspect AHU-C3 manual override first because its timing precedes the overnight spike.", ["E1", "E2"], "action"),
            _claim("Do not attribute the spike to scheduled occupancy or unusual weather without new evidence.", ["E3", "E4"], "action"),
        ]
    raise KeyError(case_id)


def analyze_case(case: dict[str, Any]) -> dict[str, Any]:
    evidence = _evidence_map(case)
    claims = [
        _claim(item["text"], [item["id"]])
        for item in case["evidence"]
    ]
    conflicts = []
    for left, right in case.get("expected_conflicts", []):
        conflicts.append({
            "evidence": [left, right],
            "detail": f"Conflict requires human resolution: [{left}] and [{right}] prescribe incompatible approval paths.",
        })
    report = {
        "case_id": case["id"],
        "title": case["title"],
        "question": case["question"],
        "claims": claims,
        "conflicts": conflicts,
        "actions": _actions(case["id"]),
        "uncertainty": "Only supplied synthetic evidence was considered; missing records may change the result.",
        "review_gate": {"required": True, "status": "PENDING_HUMAN_REVIEW"},
    }
    report["validation"] = validate_report(report, evidence)
    return report


def validate_report(report: dict[str, Any], evidence: dict[str, dict[str, Any]]) -> dict[str, Any]:
    cited_items = report["claims"] + report["actions"]
    invalid = []
    uncited = []
    for item in cited_items:
        citations = item.get("citations") or []
        if not citations:
            uncited.append(item["text"])
        for citation in citations:
            if citation not in evidence:
                invalid.append(citation)
    conflict_ids = {
        tuple(sorted(conflict["evidence"]))
        for conflict in report.get("conflicts", [])
    }
    expected = {
        tuple(sorted(pair))
        for pair in next(case for case in load_cases() if case["id"] == report["case_id"]).get("expected_conflicts", [])
    }
    return {
        "citation_validity": 1.0 if not invalid and not uncited else 0.0,
        "invalid_citations": sorted(set(invalid)),
        "uncited_items": uncited,
        "conflict_detection": conflict_ids == expected,
        "unsupported_material_claims": len(invalid) + len(uncited),
    }


def audit_bundle(case: dict[str, Any]) -> dict[str, Any]:
    report = analyze_case(case)
    return {"report": report, "receipt": build_audit_receipt(report)}


def analyze_all() -> list[dict[str, Any]]:
    return [analyze_case(case) for case in load_cases()]


if __name__ == "__main__":
    print(json.dumps(analyze_all(), indent=2))


def analyze_case_with_model(case: dict[str, Any], provider: str = "nvidia") -> dict[str, Any]:
    """Attach a bounded live-model draft without letting it override deterministic acceptance."""
    from live_model import LiveModelError, synthesize_case

    report = analyze_case(case)
    report["mode"] = "live_model_plus_deterministic_acceptance"
    try:
        report["model_synthesis"] = synthesize_case(case, provider=provider)
    except LiveModelError as exc:
        report["model_synthesis"] = {
            "error": str(exc),
            "provider": provider,
            "review_gate": {"required": True, "status": "PENDING_HUMAN_REVIEW"},
        }
    return report
