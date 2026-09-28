from __future__ import annotations

import asyncio
import os

from langchain_mcp_adapters.client import MultiServerMCPClient


MCP_URL = os.environ.get(
    "HAL_AGENT_WORLD_MCP_URL",
    "http://127.0.0.1:8765/mcp",
)


async def main() -> None:
    """Load Agent World MCP tools as LangChain-compatible tools."""

    client = MultiServerMCPClient(
        {
            "agent_world": {
                "transport": "http",
                "url": MCP_URL,
            }
        },
        tool_name_prefix=True,
    )
    tools = await client.get_tools()
    print("Agent World MCP tools:")
    for tool in tools:
        print(f"- {tool.name}")


if __name__ == "__main__":
    asyncio.run(main())
