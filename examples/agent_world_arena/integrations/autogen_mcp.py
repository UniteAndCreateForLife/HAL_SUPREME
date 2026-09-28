from __future__ import annotations

import asyncio
import os

from autogen_ext.tools.mcp import McpWorkbench, StreamableHttpServerParams


MCP_URL = os.environ.get(
    "HAL_AGENT_WORLD_MCP_URL",
    "http://127.0.0.1:8765/mcp",
)


async def main() -> None:
    """Connect AutoGen's MCP Workbench and list Agent World tools."""

    params = StreamableHttpServerParams(
        url=MCP_URL,
        timeout=10.0,
        sse_read_timeout=60.0,
    )
    async with McpWorkbench(server_params=params) as workbench:
        tools = await workbench.list_tools()
        print("Agent World MCP tools:")
        for tool in tools:
            name = getattr(tool, "name", None)
            if name is None and isinstance(tool, dict):
                name = tool.get("name")
            print(f"- {name}")


if __name__ == "__main__":
    asyncio.run(main())
