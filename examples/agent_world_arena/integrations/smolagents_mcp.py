from __future__ import annotations

import os

from smolagents import MCPClient


MCP_URL = os.environ.get(
    "HAL_AGENT_WORLD_MCP_URL",
    "http://127.0.0.1:8765/mcp",
)


def main() -> None:
    """Discover Agent World tools through Hugging Face smolagents."""

    params = {
        "url": MCP_URL,
        "transport": "streamable-http",
    }
    with MCPClient(params, structured_output=True) as tools:
        print("Agent World MCP tools:")
        for tool in tools:
            print(f"- {tool.name}")


if __name__ == "__main__":
    main()
