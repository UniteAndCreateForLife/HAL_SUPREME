from __future__ import annotations

import json
import unittest
from pathlib import Path

from examples.agent_world_arena.a2a_card import (
    A2A_PROTOCOL_VERSION,
    build_agent_world_a2a_card,
)
from examples.agent_world_arena.participant import (
    ParticipantManifest,
    negotiate_capabilities,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


class AgentWorldInteropTests(unittest.TestCase):
    def test_a2a_card_targets_v1_and_advertises_agent_world_skills(self) -> None:
        card = build_agent_world_a2a_card(
            public_base_url="https://mcp.halsupreme.com",
            documentation_url="https://halsupreme.com/agent-world",
        )

        self.assertEqual(A2A_PROTOCOL_VERSION, "1.0")
        interface = card["supportedInterfaces"][0]
        self.assertEqual(interface["protocolBinding"], "JSONRPC")
        self.assertEqual(interface["protocolVersion"], "1.0")
        self.assertEqual(interface["url"], "https://mcp.halsupreme.com/a2a/v1")
        skill_ids = {skill["id"] for skill in card["skills"]}
        self.assertIn("agent-world-interoperability-trial", skill_ids)

    def test_a2a_card_rejects_insecure_public_endpoint(self) -> None:
        with self.assertRaises(ValueError):
            build_agent_world_a2a_card(
                public_base_url="http://example.com",
            )

    def test_portable_plugin_exposes_only_loopback_agent_world_mcp(self) -> None:
        plugin = json.loads(
            (REPO_ROOT / "plugins" / "agent-world-mcp" / "plugin.json").read_text(
                encoding="utf-8"
            )
        )
        mcp = json.loads(
            (REPO_ROOT / "plugins" / "agent-world-mcp" / "mcp.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(plugin["name"], "hal-agent-world-mcp")
        server = mcp["mcpServers"]["hal-agent-world"]
        self.assertEqual(server["type"], "streamable-http")
        self.assertEqual(server["url"], "http://127.0.0.1:8765/mcp")
        self.assertNotIn("headers", server)

    def test_participant_manifest_rejects_secret_like_metadata(self) -> None:
        participant = ParticipantManifest(
            participant_id="remote-agent",
            display_name="Remote Agent",
            framework="LangGraph",
            transport="mcp",
            endpoint="https://agent.example.com/mcp",
            capabilities=("observe", "act"),
            metadata={"api_key": "must-not-be-here"},
        )

        with self.assertRaises(ValueError):
            participant.validate()

    def test_participant_capability_negotiation_is_fail_closed(self) -> None:
        participant = ParticipantManifest(
            participant_id="autogen-agent",
            display_name="AutoGen entrant",
            framework="AutoGen",
            transport="mcp",
            endpoint="http://127.0.0.1:8765/mcp",
            capabilities=("observe", "act", "communicate"),
            protocol_versions={"mcp": "current"},
        )

        self.assertEqual(
            negotiate_capabilities(
                participant,
                ("observe", "act"),
            ),
            ("act", "observe"),
        )
        with self.assertRaises(ValueError):
            negotiate_capabilities(
                participant,
                ("observe", "build"),
            )


if __name__ == "__main__":
    unittest.main()
