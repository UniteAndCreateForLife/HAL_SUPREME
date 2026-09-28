from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.configure_muse_agent_world import (
    SERVER_NAME,
    desired_server_config,
    load_settings,
    merged_settings,
    write_settings,
)
from scripts.verify_muse_agent_world_mcp import output_mentions_expected_tool


class MuseAgentWorldConfigTests(unittest.TestCase):
    def test_merge_preserves_unrelated_muse_settings(self) -> None:
        existing = {
            "model": "muse-spark-1.2",
            "permissions": {"default_profile": "auto-review"},
            "mcp_servers": {
                "existing-server": {
                    "transport": "stdio",
                    "command": "existing",
                    "args": [],
                    "enabled": True,
                    "mode": "optional",
                }
            },
        }

        merged = merged_settings(existing)

        self.assertEqual(merged["model"], "muse-spark-1.2")
        self.assertIn("existing-server", merged["mcp_servers"])
        self.assertEqual(
            merged["mcp_servers"][SERVER_NAME],
            desired_server_config(),
        )

    def test_write_creates_backup_before_replacement(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            path.write_text('{"theme":"dark"}\n', encoding="utf-8")

            backup = write_settings(
                path,
                {"theme": "dark", "mcp_servers": {SERVER_NAME: desired_server_config()}},
            )

            self.assertIsNotNone(backup)
            assert backup is not None
            self.assertEqual(
                json.loads(backup.read_text(encoding="utf-8")),
                {"theme": "dark"},
            )
            self.assertIn(
                SERVER_NAME,
                load_settings(path)["mcp_servers"],
            )

    def test_expected_muse_server_shape_matches_current_docs(self) -> None:
        config = desired_server_config()
        self.assertEqual(config["transport"], "streamable_http")
        self.assertTrue(config["enabled"])
        self.assertEqual(config["mode"], "required")
        self.assertEqual(config["url"], "${HAL_AGENT_WORLD_MCP_URL}")

    def test_smoke_output_requires_server_and_tool_evidence(self) -> None:
        self.assertTrue(
            output_mentions_expected_tool(
                '{"server":"hal-agent-world","tool":"list_episodes"}'
            )
        )
        self.assertFalse(output_mentions_expected_tool("list_episodes"))
        self.assertFalse(output_mentions_expected_tool("hal-agent-world"))


if __name__ == "__main__":
    unittest.main()
