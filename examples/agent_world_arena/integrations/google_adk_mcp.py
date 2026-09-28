from __future__ import annotations

import asyncio
import os

from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams


MCP_URL = os.environ.get(
    "HAL_AGENT_WORLD_MCP_URL",
    "http://127.0.0.1:8765/mcp",
)


async def main() -> None:
    """Discover Agent World through Google ADK's current MCP toolset."""

    toolset = McpToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=MCP_URL,
            timeout=10.0,
        )
    )
    try:
        tools = await toolset.get_tools()
        print("Agent World MCP tools:")
        for tool in tools:
            print(f"- {tool.name}")
    finally:
        await toolset.close()


if __name__ == "__main__":
    asyncio.run(main())
