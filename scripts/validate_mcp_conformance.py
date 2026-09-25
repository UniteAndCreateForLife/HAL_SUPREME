#!/usr/bin/env python3
"""Validate HAL MCP provider conformance records without third-party packages."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RECORD_DIR = ROOT / "examples" / "mcp_conformance"
REQUIRED_IDS = {"P1", "P2", "P3", "P4", "P5", "H1", "H2", "H3", "H4", "H5", "H6"}
ALLOWED_STATES = {"verified", "documented", "not_observed", "not_applicable"}
ALLOWED_TRANSPORTS = {"stdio", "streamable_http", "other", "not_recorded"}


def validate_record(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    if record.get("schema_version") != "hal.mcp_provider_conformance/v1":
        errors.append("schema_version must be hal.mcp_provider_conformance/v1")

    provider_id = record.get("provider_id")
    if not isinstance(provider_id, str) or not provider_id.strip():
        errors.append("provider_id must be a non-empty string")

    transport = record.get("transport")
    if transport not in ALLOWED_TRANSPORTS:
        errors.append(f"transport must be one of {sorted(ALLOWED_TRANSPORTS)}")

    protocol_version = record.get("protocol_version")
    if not isinstance(protocol_version, str) or not protocol_version.strip():
        errors.append("protocol_version must be a non-empty string")

    controls = record.get("controls")
    if not isinstance(controls, list):
        return errors + ["controls must be a list"]

    ids = [c.get("id") for c in controls if isinstance(c, dict)]
    if len(ids) != len(set(ids)):
        errors.append("control ids must be unique")

    missing = REQUIRED_IDS - set(ids)
    extra = set(ids) - REQUIRED_IDS
    if missing:
        errors.append(f"missing controls: {sorted(missing)}")
    if extra:
        errors.append(f"unknown controls: {sorted(extra)}")

    for index, control in enumerate(controls):
        if not isinstance(control, dict):
            errors.append(f"controls[{index}] must be an object")
            continue

        cid = control.get("id", f"index-{index}")
        state = control.get("state")
        if state not in ALLOWED_STATES:
            errors.append(f"{cid}: invalid state {state!r}")

        finding = control.get("finding")
        if not isinstance(finding, str) or not finding.strip():
            errors.append(f"{cid}: finding must be a non-empty string")

        evidence = control.get("evidence")
        if not isinstance(evidence, list) or not all(
            isinstance(item, str) and item.strip() for item in evidence
        ):
            errors.append(f"{cid}: evidence must be a list of non-empty strings")
            continue

        if state in {"verified", "documented"} and not evidence:
            errors.append(f"{cid}: {state} requires public evidence")

    return errors


def validate_file(path: Path) -> list[str]:
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{path.name}: cannot read JSON: {exc}"]
    return [f"{path.name}: {error}" for error in validate_record(record)]


def main() -> int:
    paths = sorted(RECORD_DIR.glob("*.json"))
    if not paths:
        print("no MCP conformance records found")
        return 1

    errors = [error for path in paths for error in validate_file(path)]
    if errors:
        for error in errors:
            print(error)
        return 1

    print(f"ok: {len(paths)} MCP conformance record(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
