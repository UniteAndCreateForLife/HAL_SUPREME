from __future__ import annotations

import asyncio
import os

from agents.mcp import MCPServerStreamableHttp


MCP_URL = os.environ.get(
    "HAL_AGENT_WORLD_MCP_URL",
    "http://127.0.0.1:8765/mcp",
)


async def main() -> None:
    """Connect OpenAI Agents SDK to Agent World without making a model call."""

    async with MCPServerStreamableHttp(
        name="HAL Agent World",
        params={
            "url": MCP_URL,
            "timeout": 10,
        },
        cache_tools_list=False,
    ) as server:
        tools = await server.list_tools()
        print("Agent World MCP tools:")
        for tool in tools:
            print(f"- {tool.name}")


if __name__ == "__main__":
    asyncio.run(main())
