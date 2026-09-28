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
from scripts.verify_muse_agent_world_mcp import jsonl_has_tool_call


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
        config = desired_server_config(
            transport="stdio",
            python_executable="python-test",
            repo_root=Path("/repo"),
        )

        merged = merged_settings(existing, server_config=config)

        self.assertEqual(merged["model"], "muse-spark-1.2")
        self.assertIn("existing-server", merged["mcp_servers"])
        self.assertEqual(merged["mcp_servers"][SERVER_NAME], config)

    def test_write_creates_backup_before_replacement(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            path.write_text('{"theme":"dark"}\n', encoding="utf-8")
            config = desired_server_config(
                transport="stdio",
                python_executable="python-test",
                repo_root=Path(tmp),
            )

            backup = write_settings(
                path,
                {"theme": "dark", "mcp_servers": {SERVER_NAME: config}},
            )

            self.assertIsNotNone(backup)
            assert backup is not None
            self.assertEqual(
                json.loads(backup.read_text(encoding="utf-8")),
                {"theme": "dark"},
            )
            self.assertIn(SERVER_NAME, load_settings(path)["mcp_servers"])

    def test_stdio_shape_matches_current_muse_docs(self) -> None:
        config = desired_server_config(
            transport="stdio",
            python_executable="C:/Python/python.exe",
            repo_root=Path("C:/HAL_SUPREME"),
        )
        self.assertEqual(config["transport"], "stdio")
        self.assertEqual(config["command"], "C:/Python/python.exe")
        self.assertEqual(
            config["args"],
            [
                "-m",
                "examples.agent_world_arena.mcp_server",
                "--transport",
                "stdio",
            ],
        )
        self.assertTrue(config["enabled"])
        self.assertEqual(config["mode"], "required")
        self.assertIn("PYTHONPATH", config["env"])

    def test_streamable_http_shape_is_available(self) -> None:
        config = desired_server_config(
            transport="streamable_http",
            http_url="http://127.0.0.1:9999/mcp",
        )
        self.assertEqual(config["transport"], "streamable_http")
        self.assertEqual(config["url"], "http://127.0.0.1:9999/mcp")
        self.assertNotIn("command", config)

    def test_jsonl_probe_requires_tool_event_evidence(self) -> None:
        self.assertTrue(
            jsonl_has_tool_call(
                '{"type":"tool_call","name":"list_episodes","server":"hal-agent-world"}',
                "list_episodes",
            )
        )
        self.assertFalse(
            jsonl_has_tool_call(
                '{"type":"assistant","text":"I might call a tool"}',
                "list_episodes",
            )
        )


if __name__ == "__main__":
    unittest.main()
