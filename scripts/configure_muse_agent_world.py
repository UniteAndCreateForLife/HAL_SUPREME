from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys
from typing import Any


DEFAULT_SETTINGS_PATH = Path.home() / ".config" / "muse" / "settings.json"
SERVER_NAME = "hal-agent-world"


def desired_server_config() -> dict[str, Any]:
    return {
        "transport": "streamable_http",
        "url": "${HAL_AGENT_WORLD_MCP_URL}",
        "enabled": True,
        "mode": "required",
    }


def load_settings(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Muse settings root must be a JSON object")
    return payload


def merged_settings(existing: dict[str, Any]) -> dict[str, Any]:
    payload = dict(existing)
    servers = payload.get("mcp_servers", {})
    if servers is None:
        servers = {}
    if not isinstance(servers, dict):
        raise ValueError("mcp_servers must be a JSON object")

    merged_servers = dict(servers)
    merged_servers[SERVER_NAME] = desired_server_config()
    payload["mcp_servers"] = merged_servers
    return payload


def write_settings(path: Path, payload: dict[str, Any]) -> Path | None:
    path.parent.mkdir(parents=True, exist_ok=True)
    backup: Path | None = None
    if path.exists():
        backup = path.with_suffix(path.suffix + ".hal-agent-world.bak")
        shutil.copy2(path, backup)

    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)
    return backup


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Safely merge HAL Agent World into Muse Code's MCP settings "
            "without overwriting unrelated Muse configuration."
        )
    )
    parser.add_argument(
        "--settings",
        type=Path,
        default=DEFAULT_SETTINGS_PATH,
        help="Muse settings.json path.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write the merged settings. Without this flag the command is dry-run only.",
    )
    args = parser.parse_args()

    existing = load_settings(args.settings)
    merged = merged_settings(existing)

    if not args.apply:
        print(json.dumps(merged, indent=2))
        print(
            f"\nDry run only. Re-run with --apply to update {args.settings}",
            file=sys.stderr,
        )
        return 0

    backup = write_settings(args.settings, merged)
    print(f"Updated Muse MCP settings: {args.settings}")
    if backup is not None:
        print(f"Backup: {backup}")
    print(
        "Set HAL_AGENT_WORLD_MCP_URL before starting Muse Code, for example "
        "http://127.0.0.1:8765/mcp"
    )
    print("Inside Muse Code, run /mcp to inspect the live server/tool inventory.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
