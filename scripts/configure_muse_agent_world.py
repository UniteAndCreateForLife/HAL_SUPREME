from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SETTINGS_PATH = Path.home() / ".config" / "muse" / "settings.json"
SERVER_NAME = "hal-agent-world"
DEFAULT_HTTP_URL = "http://127.0.0.1:8765/mcp"


def desired_server_config(
    *,
    transport: str = "stdio",
    python_executable: str | None = None,
    repo_root: Path | None = None,
    http_url: str = DEFAULT_HTTP_URL,
) -> dict[str, Any]:
    if transport == "stdio":
        return {
            "transport": "stdio",
            "command": python_executable or sys.executable,
            "args": [
                "-m",
                "examples.agent_world_arena.mcp_server",
                "--transport",
                "stdio",
            ],
            "env": {
                "PYTHONPATH": str((repo_root or REPO_ROOT).resolve()),
            },
            "enabled": True,
            "mode": "required",
        }

    if transport == "streamable_http":
        return {
            "transport": "streamable_http",
            "url": http_url,
            "enabled": True,
            "mode": "required",
        }

    raise ValueError(f"unsupported Muse MCP transport: {transport}")


def load_settings(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Muse settings root must be a JSON object")
    return payload


def merged_settings(
    existing: dict[str, Any],
    *,
    server_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = dict(existing)
    servers = payload.get("mcp_servers", {})
    if servers is None:
        servers = {}
    if not isinstance(servers, dict):
        raise ValueError("mcp_servers must be a JSON object")

    merged_servers = dict(servers)
    merged_servers[SERVER_NAME] = server_config or desired_server_config()
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
        "--transport",
        choices=("stdio", "streamable_http"),
        default="stdio",
        help=(
            "Local Muse should normally use stdio so Muse launches Agent World "
            "directly. Streamable HTTP is available for an already-running server."
        ),
    )
    parser.add_argument(
        "--http-url",
        default=DEFAULT_HTTP_URL,
        help="Agent World MCP URL when --transport streamable_http is selected.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write the merged settings. Without this flag the command is dry-run only.",
    )
    args = parser.parse_args()

    config = desired_server_config(
        transport=args.transport,
        http_url=args.http_url,
    )
    existing = load_settings(args.settings)
    merged = merged_settings(existing, server_config=config)

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
    print(f"Muse Agent World MCP transport: {args.transport}")
    print("Inside Muse Code, run /mcp to inspect the live server/tool inventory.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
