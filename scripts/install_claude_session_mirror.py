from __future__ import annotations

import json
import shlex
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SETTINGS = Path.home() / ".claude" / "settings.json"
MIRROR = ROOT / "scripts" / "claude_session_mirror.py"
HOOK_MARKER = "claude_session_mirror.py"


def load_settings() -> dict[str, Any]:
    if not SETTINGS.is_file():
        return {}
    value = json.loads(SETTINGS.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("settings.local.json must contain a JSON object")
    return value


def command_string() -> str:
    python = Path(sys.executable).resolve()
    if sys.platform.startswith("win"):
        return subprocess.list2cmdline([str(python), str(MIRROR), "hook", "--project-substring", "HAL_SUPREME"])
    return shlex.join([str(python), str(MIRROR), "hook", "--project-substring", "HAL_SUPREME"])


def ensure_event(hooks: dict[str, Any], event: str, command: str, timeout: int = 8) -> None:
    entries = hooks.setdefault(event, [])
    if not isinstance(entries, list):
        raise ValueError(f"hooks.{event} must be an array")
    for entry in entries:
        if HOOK_MARKER in json.dumps(entry):
            return
    entries.append(
        {
            "hooks": [
                {
                    "type": "command",
                    "command": command,
                    "timeout": timeout,
                }
            ]
        }
    )


def main() -> int:
    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    if SETTINGS.is_file():
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = SETTINGS.with_name(f"settings.before-hal-session-mirror.{stamp}.json")
        shutil.copy2(SETTINGS, backup)
        print(f"SETTINGS_BACKUP={backup}")
    settings = load_settings()
    hooks = settings.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError("settings hooks must be an object")

    cmd = command_string()
    for event in ("UserPromptSubmit", "Stop", "PreCompact", "SessionEnd"):
        ensure_event(hooks, event, cmd)

    tmp = SETTINGS.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(settings, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(SETTINGS)

    subprocess.run(
        [sys.executable, str(MIRROR), "backfill", "--limit", "12", "--project-substring", "HAL_SUPREME"],
        cwd=str(ROOT),
        check=False,
    )

    print(f"CLAUDE_SESSION_MIRROR_INSTALLED={SETTINGS}")
    print(f"MIRROR_INDEX={ROOT / 'data' / 'runtime' / 'claude_session_mirror' / 'latest_sessions.md'}")
    print("User-level hooks installed for HAL_SUPREME sessions.")
    print("Existing Claude sessions may need /hooks, a settings reload, or one new turn before the hook fires.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
