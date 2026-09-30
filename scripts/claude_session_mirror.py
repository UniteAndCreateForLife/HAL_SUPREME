from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MIRROR_ROOT = ROOT / "data" / "runtime" / "claude_session_mirror"

_SECRET_PATTERNS = [
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{8,}"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"(?i)([?&](?:token|key|secret|code)=)[^&\s\"']+"),
    re.compile(r"(?i)\b((?:TOKEN|API_KEY|APIKEY|PASSWORD|SECRET)=)[^\s\"']+"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{8,}\b"),
]
_WINDOWS_HOME = re.compile(r"(?i)\b[A-Z]:\\Users\\[^\\\s\"']+")
_UNIX_HOME = re.compile(r"/(?:home|Users)/[^/\s\"']+")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def redact_text(text: str) -> str:
    value = text
    for pattern in _SECRET_PATTERNS:
        if pattern.groups:
            value = pattern.sub(lambda m: m.group(1) + "[REDACTED]", value)
        else:
            value = pattern.sub("[REDACTED]", value)
    value = _WINDOWS_HOME.sub("[LOCAL_HOME]", value)
    value = _UNIX_HOME.sub("[LOCAL_HOME]", value)
    return value


def safe_session_id(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._")
    if not cleaned:
        raise ValueError("session_id is empty")
    return cleaned[:180]


def source_fingerprint(path: Path) -> str:
    return hashlib.sha256(str(path).encode("utf-8")).hexdigest()


def copy_sanitized_transcript(source: Path, target: Path) -> dict[str, Any]:
    if not source.is_file():
        raise FileNotFoundError(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    line_count = 0
    with source.open("r", encoding="utf-8", errors="replace") as src, tmp.open(
        "w", encoding="utf-8", newline="\n"
    ) as dst:
        for raw in src:
            dst.write(redact_text(raw.rstrip("\r\n")) + "\n")
            line_count += 1
    os.replace(tmp, target)
    return {
        "source_size_bytes": source.stat().st_size,
        "source_mtime_ns": source.stat().st_mtime_ns,
        "mirror_size_bytes": target.stat().st_size,
        "line_count": line_count,
        "source_path_sha256": source_fingerprint(source),
    }


def load_index(root: Path) -> dict[str, Any]:
    path = root / "index.json"
    if not path.is_file():
        return {"schema_version": 1, "sessions": {}}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"schema_version": 1, "sessions": {}}
    if not isinstance(value, dict) or not isinstance(value.get("sessions"), dict):
        return {"schema_version": 1, "sessions": {}}
    return value


def write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def _clip(text: str | None, limit: int = 1200) -> str:
    value = redact_text(text or "").strip()
    if len(value) > limit:
        return value[: limit - 1] + "…"
    return value


def write_latest_markdown(root: Path, index: dict[str, Any]) -> None:
    sessions = list(index.get("sessions", {}).values())
    sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    lines = [
        "# Claude session mirror",
        "",
        "Private local mirror for ChatGPT/HAL continuity. Content is sanitized before writing.",
        "",
    ]
    for item in sessions[:10]:
        lines.extend(
            [
                f"## {item.get('session_id', 'unknown')}",
                f"- Updated: {item.get('updated_at', 'unknown')}",
                f"- Project: {item.get('project', 'unknown')}",
                f"- Last event: {item.get('hook_event_name', 'unknown')}",
                f"- Transcript: {item.get('mirror_relative_path', 'unknown')}",
            ]
        )
        if item.get("last_prompt"):
            lines.extend(["", "### Last prompt", "", item["last_prompt"]])
        if item.get("last_assistant_message"):
            lines.extend(["", "### Last assistant message", "", item["last_assistant_message"]])
        lines.append("")
    (root / "latest_sessions.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def mirror_hook(payload: dict[str, Any], root: Path) -> dict[str, Any]:
    session_id = safe_session_id(str(payload.get("session_id") or ""))
    transcript_raw = str(payload.get("transcript_path") or "")
    if not transcript_raw:
        raise ValueError("hook payload has no transcript_path")
    transcript = Path(transcript_raw).expanduser()
    cwd = Path(str(payload.get("cwd") or ROOT))
    session_dir = root / "sessions" / session_id
    mirror_path = session_dir / "transcript.sanitized.jsonl"
    copy_info = copy_sanitized_transcript(transcript, mirror_path)

    state_path = session_dir / "state.json"
    state: dict[str, Any] = {}
    if state_path.is_file():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            state = {}

    hook_name = str(payload.get("hook_event_name") or "unknown")
    prompt = payload.get("prompt")
    last_assistant = payload.get("last_assistant_message")
    if isinstance(prompt, str) and prompt.strip():
        state["last_prompt"] = _clip(prompt)
    if isinstance(last_assistant, str) and last_assistant.strip():
        state["last_assistant_message"] = _clip(last_assistant)

    state.update(
        {
            "schema_version": 1,
            "session_id": session_id,
            "updated_at": utc_now(),
            "hook_event_name": hook_name,
            "project": cwd.name or "HAL_SUPREME",
            "cwd_sha256": hashlib.sha256(str(cwd).encode("utf-8")).hexdigest(),
            "mirror_relative_path": str(mirror_path.relative_to(root)).replace("\\", "/"),
            **copy_info,
        }
    )
    write_json_atomic(state_path, state)

    index = load_index(root)
    index["updated_at"] = utc_now()
    index["sessions"][session_id] = state
    write_json_atomic(root / "index.json", index)
    write_latest_markdown(root, index)
    return state


def discover_recent_transcripts(
    *,
    limit: int,
    project_substring: str | None,
) -> list[Path]:
    home = Path.home()
    base = home / ".claude" / "projects"
    if not base.is_dir():
        return []
    candidates = [p for p in base.rglob("*.jsonl") if p.is_file()]
    if project_substring:
        needle = project_substring.lower()
        candidates = [p for p in candidates if needle in str(p.parent).lower()]
    candidates.sort(key=lambda p: p.stat().st_mtime_ns, reverse=True)
    return candidates[:limit]


def backfill(root: Path, *, limit: int, project_substring: str | None) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    index = load_index(root)
    for transcript in discover_recent_transcripts(limit=limit, project_substring=project_substring):
        session_id = safe_session_id(transcript.stem)
        session_dir = root / "sessions" / session_id
        mirror_path = session_dir / "transcript.sanitized.jsonl"
        info = copy_sanitized_transcript(transcript, mirror_path)
        state = {
            "schema_version": 1,
            "session_id": session_id,
            "updated_at": datetime.fromtimestamp(transcript.stat().st_mtime, timezone.utc).isoformat(),
            "hook_event_name": "backfill",
            "project": transcript.parent.name,
            "cwd_sha256": None,
            "mirror_relative_path": str(mirror_path.relative_to(root)).replace("\\", "/"),
            **info,
        }
        write_json_atomic(session_dir / "state.json", state)
        index["sessions"][session_id] = state
        results.append(state)
    index["updated_at"] = utc_now()
    write_json_atomic(root / "index.json", index)
    write_latest_markdown(root, index)
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Mirror Claude Code sessions into a private HAL runtime folder.")
    parser.add_argument("--root", type=Path, default=DEFAULT_MIRROR_ROOT)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("hook", help="Read one Claude hook payload from stdin and mirror that session.")

    b = sub.add_parser("backfill", help="Mirror recent local Claude Code transcript files.")
    b.add_argument("--limit", type=int, default=10)
    b.add_argument("--project-substring", default="HAL_SUPREME")

    sub.add_parser("list", help="Print the current mirror index.")

    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)

    if args.command == "hook":
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise SystemExit("hook input must be a JSON object")
        state = mirror_hook(payload, root)
        print(json.dumps({"ok": True, "session_id": state["session_id"]}))
        return 0

    if args.command == "backfill":
        rows = backfill(root, limit=max(1, args.limit), project_substring=args.project_substring)
        print(json.dumps({"ok": True, "mirrored": len(rows), "root": str(root)}))
        return 0

    if args.command == "list":
        print(json.dumps(load_index(root), indent=2, sort_keys=True))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
