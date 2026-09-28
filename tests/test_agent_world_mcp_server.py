from __future__ import annotations

import asyncio
import unittest

from examples.agent_world_arena.mcp_server import build_mcp_server


EXPECTED_TOOLS = {
    "create_episode",
    "list_episodes",
    "read_observation",
    "submit_action",
    "episode_status",
    "advance_episode",
    "advance_episode_with_idle_timeout",
    "episode_replay",
}


class AgentWorldMCPServerTests(unittest.TestCase):
    def test_current_mcp_sdk_registers_expected_bounded_surface(self) -> None:
        server = build_mcp_server()
        tools = asyncio.run(server.list_tools())
        names = {tool.name for tool in tools}
        self.assertEqual(names, EXPECTED_TOOLS)

    def test_server_does_not_expose_generic_execution_tools(self) -> None:
        server = build_mcp_server()
        tools = asyncio.run(server.list_tools())
        names = {tool.name for tool in tools}
        for forbidden in ("shell", "exec", "filesystem", "browser", "run_command"):
            self.assertNotIn(forbidden, names)


if __name__ == "__main__":
    unittest.main()
