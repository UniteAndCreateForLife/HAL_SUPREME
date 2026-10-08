from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import json


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def build_receipt(*, kind: str, source_sha: str | None, evidence: dict) -> dict:
    payload = {
        "schema": "hal-revenue-receipt/v1",
        "kind": kind,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_sha": source_sha,
        "evidence": evidence,
    }
    payload["receipt_sha256"] = hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
    return payload


def verify_receipt(receipt: dict) -> bool:
    expected = receipt.get("receipt_sha256")
    if not isinstance(expected, str):
        return False
    body = dict(receipt)
    body.pop("receipt_sha256", None)
    return hashlib.sha256(canonical_json_bytes(body)).hexdigest() == expected
