from __future__ import annotations

import sys

from crewai_tools import MCPServerAdapter
from mcp import StdioServerParameters


def main() -> None:
    """Launch Agent World as a local stdio MCP subprocess for CrewAI."""

    params = StdioServerParameters(
        command=sys.executable,
        args=[
            "-m",
            "examples.agent_world_arena.mcp_server",
            "--transport",
            "stdio",
        ],
    )
    with MCPServerAdapter(params) as tools:
        print("Agent World MCP tools:")
        for tool in tools:
            print(f"- {tool.name}")


if __name__ == "__main__":
    main()
