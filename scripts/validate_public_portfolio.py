from __future__ import annotations

import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTFOLIO_PATH = REPO_ROOT / "portfolio" / "portfolio.json"
PUBLIC_TEXT_PATHS = (
    REPO_ROOT / "PORTFOLIO.md",
    REPO_ROOT / "case-studies",
    REPO_ROOT / "docs" / "PUBLIC_WORK_LOG.md",
    REPO_ROOT / "docs" / "PUBLIC_WORK_POLICY.md",
    REPO_ROOT / "evidence" / "portfolio",
    REPO_ROOT / "plugins" / "livepeer-creative-mcp",
    PORTFOLIO_PATH,
)

SECRET_PATTERNS = {
    "github_token": re.compile(r"\bgh[opusr]_[A-Za-z0-9]{20,}\b"),
    "openai_style_key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "bearer_token": re.compile(r"(?i)Bearer\s+[A-Za-z0-9._~+/-]{20,}"),
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "windows_absolute_path": re.compile(r"\b[A-Za-z]:\\"),
}


def _load_json(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid JSON {path.relative_to(REPO_ROOT).as_posix()}: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"JSON root must be an object: {path.relative_to(REPO_ROOT).as_posix()}")
        return {}
    return value


def _relative_file(value: object, field: str, errors: list[str]) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{field} must be a non-empty relative path")
        return None
    posix = PurePosixPath(value)
    if posix.is_absolute() or ".." in posix.parts or "\\" in value:
        errors.append(f"{field} is not a safe repository-relative path: {value!r}")
        return None
    path = REPO_ROOT.joinpath(*posix.parts)
    if not path.is_file():
        errors.append(f"{field} does not exist: {value}")
        return None
    return path


def _iter_public_text_files() -> list[Path]:
    files: set[Path] = set()
    for candidate in PUBLIC_TEXT_PATHS:
        if candidate.is_file():
            files.add(candidate)
        elif candidate.is_dir():
            files.update(
                path
                for path in candidate.rglob("*")
                if path.is_file() and path.suffix.lower() in {".md", ".json", ".txt", ".yml", ".yaml"}
            )
    return sorted(files)


def validate(repo_root: Path = REPO_ROOT) -> list[str]:
    if repo_root.resolve() != REPO_ROOT.resolve():
        raise ValueError("validate currently supports its containing repository only")

    errors: list[str] = []
    portfolio = _load_json(PORTFOLIO_PATH, errors)
    if portfolio.get("schema") != "hal.public_portfolio.v1":
        errors.append("portfolio schema must be hal.public_portfolio.v1")

    projects = portfolio.get("projects")
    if not isinstance(projects, list) or not projects:
        errors.append("portfolio projects must be a non-empty list")
        projects = []

    seen_ids: set[str] = set()
    evidence_documents: list[dict[str, Any]] = []
    for index, project in enumerate(projects):
        if not isinstance(project, dict):
            errors.append(f"projects[{index}] must be an object")
            continue
        project_id = project.get("id")
        if not isinstance(project_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,79}", project_id):
            errors.append(f"projects[{index}].id is invalid")
        elif project_id in seen_ids:
            errors.append(f"duplicate project id: {project_id}")
        else:
            seen_ids.add(project_id)

        evidence = project.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"projects[{index}].evidence must be a non-empty list")
            continue
        for evidence_index, value in enumerate(evidence):
            path = _relative_file(value, f"projects[{index}].evidence[{evidence_index}]", errors)
            if path and path.suffix.lower() == ".json" and "evidence/portfolio" in path.as_posix():
                evidence_documents.append(_load_json(path, errors))

        case_study = project.get("case_study")
        if case_study is not None:
            _relative_file(case_study, f"projects[{index}].case_study", errors)

    livepeer = next(
        (doc for doc in evidence_documents if doc.get("evidence_id") == "livepeer-chatgpt-mcp-2026-09-24"),
        None,
    )
    if not livepeer:
        errors.append("missing Livepeer portfolio evidence receipt")
    else:
        mcp = livepeer.get("mcp", {})
        caps = livepeer.get("capabilities", {})
        plugin = livepeer.get("chatgpt_plugin", {})
        bridge = livepeer.get("hal_bridge", {})
        verification = livepeer.get("verification", {})
        if mcp.get("method_count", 0) < 100 or mcp.get("required_methods_present") is not True:
            errors.append("Livepeer receipt does not prove the expected MCP method surface")
        if caps.get("total") != caps.get("ai", 0) + caps.get("tool", 0) + caps.get("mcp", 0):
            errors.append("Livepeer capability totals do not reconcile")
        if plugin.get("version") != "0.1.0" or plugin.get("installed_and_read_verified") is not True:
            errors.append("ChatGPT plugin receipt is incomplete")
        if bridge.get("method_count") != 11 or bridge.get("provider_execution_authority") is not False:
            errors.append("HAL bridge authority receipt is inconsistent")
        if verification.get("inventory_calls_read_only") is not True:
            errors.append("Livepeer inventory must be read-only")
        if verification.get("media_job_submitted") is not False:
            errors.append("Livepeer inventory unexpectedly submitted a media job")
        if verification.get("external_mutation") is not False:
            errors.append("Livepeer inventory unexpectedly mutated external state")

    plugin_manifest = _load_json(REPO_ROOT / "plugins" / "livepeer-creative-mcp" / "plugin.json", errors)
    mcp_manifest = _load_json(REPO_ROOT / "plugins" / "livepeer-creative-mcp" / "mcp.json", errors)
    if plugin_manifest.get("name") != "livepeer-creative-mcp" or plugin_manifest.get("version") != "0.1.0":
        errors.append("Livepeer ChatGPT plugin manifest identity is invalid")
    server = mcp_manifest.get("mcpServers", {}).get("livepeer-creative", {})
    if server.get("type") != "streamable-http" or server.get("url") != "https://agent.livepeer.org/api/mcp/creative":
        errors.append("Livepeer ChatGPT MCP server manifest is invalid")

    for path in _iter_public_text_files():
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(REPO_ROOT).as_posix()
        for name, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"{name} pattern found in {relative}")

    return errors


def main() -> int:
    errors = validate()
    report = {
        "schema": "hal.public_portfolio_validation.v1",
        "ok": not errors,
        "portfolio": PORTFOLIO_PATH.relative_to(REPO_ROOT).as_posix(),
        "projects": len(_load_json(PORTFOLIO_PATH, []).get("projects", [])),
        "public_text_files_scanned": len(_iter_public_text_files()),
        "errors": errors,
    }
    print(json.dumps(report, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
