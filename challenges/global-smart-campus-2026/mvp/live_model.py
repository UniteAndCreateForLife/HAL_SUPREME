from __future__ import annotations

import json
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any
from urllib import error, request

NVIDIA_ENDPOINT = "https://integrate.api.nvidia.com/v1/chat/completions"
DEFAULT_MODEL = os.getenv("HAL_CAMPUS_NVIDIA_MODEL", "openai/gpt-oss-20b")
MAX_MODEL_TOKENS = 256


class LiveModelError(RuntimeError):
    pass


def _build_prompt(case: dict[str, Any]) -> str:
    evidence = "\n".join(
        f"[{item['id']}] ({item['type']}) {item['text']}" for item in case["evidence"]
    )
    return f"""Reasoning: low. Synthetic campus evidence task. Use ONLY supplied evidence.
Every finding/action must cite supplied IDs. Surface contradictions; never resolve them by invention. Only emit a conflict when supplied evidence explicitly prescribes incompatible requirements; otherwise conflicts must be [].
All actions are advisory and reversible. Question: {case['question']}
Evidence:\n{evidence}
Return JSON only. Limits: findings<=2, actions<=2, conflicts<=1; each text/detail<=24 words; uncertainty<=24 words.
Schema: {{"findings":[{{"text":"...","citations":["E1"]}}],"actions":[{{"text":"...","citations":["E1"]}}],
"conflicts":[{{"detail":"...","evidence":["E1","E2"]}}],"uncertainty":"..."}}"""

def _extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.I)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start < 0 or end <= start:
            raise LiveModelError("model_response_not_json")
        try:
            value = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError as exc:
            raise LiveModelError("model_response_not_json") from exc
    if not isinstance(value, dict):
        raise LiveModelError("model_response_wrong_shape")
    return value


def _bounded_text(value: Any, limit: int = 600) -> str:
    if not isinstance(value, str):
        return ""
    cleaned = " ".join(value.split())
    # Normalize provider mojibake/non-ASCII punctuation without changing legitimate terminal question marks.
    cleaned = cleaned.encode("ascii", "replace").decode("ascii")
    cleaned = re.sub(r"(?<=[A-Za-z])\?+(?=[A-Za-z])", "-", cleaned)
    return cleaned[:limit]


def _citation_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()][:6]


def _filter_items(rows: Any, valid_ids: set[str], *, text_key: str, cite_key: str, limit: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    if not isinstance(rows, list):
        return accepted, rejected
    for row in rows[:limit]:
        if not isinstance(row, dict):
            rejected.append({"reason": "wrong_shape"})
            continue
        text = _bounded_text(row.get(text_key))
        citations = _citation_list(row.get(cite_key))
        invalid = [citation for citation in citations if citation not in valid_ids]
        if not text or not citations or invalid:
            rejected.append({
                "reason": "missing_or_invalid_citation",
                "invalid_citations": invalid,
            })
            continue
        accepted.append({text_key: text, cite_key: citations})
    return accepted, rejected


def normalize_synthesis(case: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    valid_ids = {item["id"] for item in case["evidence"]}
    findings, rejected_findings = _filter_items(
        payload.get("findings"), valid_ids, text_key="text", cite_key="citations", limit=8
    )
    actions, rejected_actions = _filter_items(
        payload.get("actions"), valid_ids, text_key="text", cite_key="citations", limit=6
    )
    candidate_conflicts, rejected_conflicts = _filter_items(
        payload.get("conflicts"), valid_ids, text_key="detail", cite_key="evidence", limit=4
    )
    expected_pairs = {
        tuple(sorted(pair))
        for pair in case.get("expected_conflicts", [])
    }
    conflicts: list[dict[str, Any]] = []
    rejected_relations: list[dict[str, Any]] = []
    for conflict in candidate_conflicts:
        pair = tuple(sorted(dict.fromkeys(conflict["evidence"])))
        if pair in expected_pairs:
            conflicts.append(conflict)
        else:
            rejected_relations.append({
                "reason": "unsupported_conflict_relation",
                "evidence": list(pair),
            })
    rejected = rejected_findings + rejected_actions + rejected_conflicts + rejected_relations
    invalid = sorted({
        item
        for row in rejected
        for item in row.get("invalid_citations", [])
    })
    accepted_pairs = {tuple(sorted(conflict["evidence"])) for conflict in conflicts}
    return {
        "summary": _bounded_text(payload.get("summary"), 900),
        "findings": findings,
        "actions": actions,
        "conflicts": conflicts,
        "uncertainty": _bounded_text(payload.get("uncertainty"), 700),
        "acceptance": {
            "accepted_items": len(findings) + len(actions) + len(conflicts),
            "rejected_items": len(rejected),
            "invalid_citations": invalid,
            "all_accepted_items_grounded": not invalid,
            "unsupported_conflict_relations_rejected": len(rejected_relations),
            "model_conflict_detection": accepted_pairs == expected_pairs,
            "policy": "Only model items with supplied evidence IDs and seeded-valid conflict relations survive the deterministic acceptance layer.",
        },
    }


def _powershell_bridge(body: dict[str, Any], timeout: float) -> dict[str, Any]:
    script = Path(__file__).with_name("nvidia_bridge.ps1")
    if not script.is_file():
        raise LiveModelError("nvidia_bridge_missing")
    try:
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)],
            input=json.dumps(body),
            text=True,
            capture_output=True,
            timeout=timeout + 5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise LiveModelError("nvidia_transport_error") from exc
    if completed.returncode != 0:
        raise LiveModelError("nvidia_bridge_error")
    try:
        return json.loads(completed.stdout.strip())
    except json.JSONDecodeError as exc:
        raise LiveModelError("nvidia_bridge_invalid_json") from exc


def _nvidia_request(case: dict[str, Any], timeout: float) -> tuple[dict[str, Any], dict[str, Any]]:
    api_key = _get_secret("NVIDIA_API_KEY")
    if not api_key:
        raise LiveModelError("NVIDIA_API_KEY_missing")
    body = {
        "model": DEFAULT_MODEL,
        "messages": [{"role": "user", "content": _build_prompt(case)}],
        "temperature": 0.1,
        "max_tokens": MAX_MODEL_TOKENS,
        "stream": False,
        "reasoning_effort": "low",
    }
    started = time.perf_counter()
    if os.name == "nt" and Path(__file__).with_name("nvidia_bridge.ps1").is_file():
        raw = _powershell_bridge(body, timeout)
    else:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "HAL-Campus-Evidence-Desk/0.2",
        }
        try:
            import requests
            response = requests.post(NVIDIA_ENDPOINT, headers=headers, json=body, timeout=timeout)
            if response.status_code >= 400:
                raise LiveModelError(f"nvidia_http_{response.status_code}")
            raw = response.json()
        except LiveModelError:
            raise
        except Exception as exc:
            raise LiveModelError("nvidia_transport_error") from exc
    duration_ms = round((time.perf_counter() - started) * 1000, 1)
    try:
        content = raw["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LiveModelError("nvidia_response_missing_content") from exc
    usage = raw.get("usage") if isinstance(raw.get("usage"), dict) else {}
    meta = {
        "provider": "nvidia_nim",
        "model": DEFAULT_MODEL,
        "duration_ms": duration_ms,
        "usage": {key: usage.get(key) for key in ("prompt_tokens", "completion_tokens", "total_tokens")},
    }
    return _extract_json(content), meta

def synthesize_case(case: dict[str, Any], *, provider: str = "nvidia", timeout: float = 75.0) -> dict[str, Any]:
    if provider != "nvidia":
        raise LiveModelError(f"unsupported_provider:{provider}")
    payload, meta = _nvidia_request(case, timeout)
    normalized = normalize_synthesis(case, payload)
    normalized["provider"] = meta
    normalized["review_gate"] = {
        "required": True,
        "status": "PENDING_HUMAN_REVIEW",
    }
    return normalized


def provider_status() -> dict[str, Any]:
    return {
        "nvidia": {
            "configured": bool(_get_secret("NVIDIA_API_KEY")),
            "model": DEFAULT_MODEL,
            "purpose": "prototype evidence synthesis only",
            "max_output_tokens": MAX_MODEL_TOKENS,
        }
    }


def _get_secret(name: str) -> str | None:
    value = os.getenv(name)
    if value:
        return value
    if os.name == "nt":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
                value, _ = winreg.QueryValueEx(key, name)
                return str(value) if value else None
        except (FileNotFoundError, OSError):
            return None
    return None
