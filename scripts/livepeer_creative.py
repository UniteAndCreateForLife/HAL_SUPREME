#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integrations.livepeer_creative import LivepeerCreativeClient, McpError  # noqa: E402


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="HAL operator CLI for Livepeer Agent Creative MCP."
    )
    p.add_argument("--endpoint", help="Override LIVEPEER_CREATIVE_MCP_URL.")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser(
        "doctor",
        help="Initialize MCP and report discovered creative tools without generating media.",
    )
    sub.add_parser("tools", help="List creative MCP tool names.")

    schema = sub.add_parser("schema", help="Print one tool's runtime input schema.")
    schema.add_argument("tool")

    call = sub.add_parser(
        "call", help="Call an exact discovered tool. This may consume Livepeer balance."
    )
    call.add_argument("tool")
    call.add_argument(
        "--args-json",
        default="{}",
        help="JSON object matching the runtime tool schema.",
    )
    call.add_argument(
        "--confirm-spend",
        action="store_true",
        help="Required safety latch for tools/call because generation/finishing may consume balance.",
    )
    return p


def main() -> int:
    args = parser().parse_args()
    client = LivepeerCreativeClient(endpoint=args.endpoint)

    try:
        if args.command == "doctor":
            tools = client.list_tools(refresh=True)
            names = sorted(tool.name for tool in tools)
            likely_creation = [
                name
                for name in names
                if any(
                    token in name.lower()
                    for token in ("create", "generate", "render", "media", "project")
                )
            ]
            print(
                json.dumps(
                    {
                        "ok": True,
                        "endpoint": client.endpoint,
                        "auth_mode": client.auth_mode(),
                        "tool_count": len(names),
                        "likely_creation_tools": likely_creation[:40],
                    },
                    indent=2,
                )
            )
            return 0

        if args.command == "tools":
            print("\n".join(client.tool_names(refresh=True)))
            return 0

        if args.command == "schema":
            tool = client.get_tool(args.tool)
            print(
                json.dumps(
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": tool.input_schema,
                    },
                    indent=2,
                )
            )
            return 0

        if args.command == "call":
            if not args.confirm_spend:
                print(
                    "Refusing tools/call without --confirm-spend. Inspect the tool schema first.",
                    file=sys.stderr,
                )
                return 2
            parsed = json.loads(args.args_json)
            if not isinstance(parsed, dict):
                raise ValueError("--args-json must decode to a JSON object")
            result = client.call_tool(args.tool, parsed)
            print(json.dumps(result, indent=2))
            return 0

    except (McpError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
