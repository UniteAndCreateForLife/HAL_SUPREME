from __future__ import annotations

import os
import sys

from crewai_tools import MCPServerAdapter
from mcp import StdioServerParameters


def main() -> None:
    """Launch Agent World as a local stdio MCP subprocess for CrewAI."""

    server_python = os.environ.get(
        "HAL_AGENT_WORLD_SERVER_PYTHON",
        sys.executable,
    )
    params = StdioServerParameters(
        command=server_python,
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
