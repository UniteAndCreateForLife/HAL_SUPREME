from __future__ import annotations

import json
import unittest
from pathlib import Path

from examples.agent_world_arena import Action, ProviderDescriptor, ScriptedAdapter
from examples.agent_world_arena.conformance import run_adapter_conformance
from examples.agent_world_arena.participant import ParticipantManifest

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY = REPO_ROOT / "examples" / "agent_world_arena" / "integrations" / "registry.json"


class AgentWorldConformanceTests(unittest.TestCase):
    def test_scripted_external_adapter_earns_deterministic_receipt(self) -> None:
        participant = ParticipantManifest(
            participant_id="external-scripted",
            display_name="External scripted entrant",
            framework="reference-test",
            transport="scripted",
            capabilities=("observe", "act"),
            protocol_versions={"agent-world": "hal.agent_world.v0"},
        )
        adapter = ScriptedAdapter(
            provider=ProviderDescriptor(
                provider_id="external-scripted",
                model="idle-reference",
                transport="local-python",
            ),
            policy=lambda _observation: Action("idle"),
        )

        first = run_adapter_conformance(participant, adapter, seed=99)
        second = run_adapter_conformance(participant, adapter, seed=99)

        self.assertEqual(first.final_state_sha256, second.final_state_sha256)
        self.assertEqual(first.adapter_failures, 0)
        self.assertEqual(first.steps, 4)

    def test_conformance_rejects_identity_mismatch(self) -> None:
        participant = ParticipantManifest(
            participant_id="declared",
            display_name="Declared",
            framework="reference-test",
            transport="scripted",
            capabilities=("observe", "act"),
        )
        adapter = ScriptedAdapter(
            provider=ProviderDescriptor(
                provider_id="different",
                model="idle-reference",
            ),
            policy=lambda _observation: Action("idle"),
        )

        with self.assertRaises(ValueError):
            run_adapter_conformance(participant, adapter)

    def test_integration_registry_never_claims_live_proof_for_smoke_entries(self) -> None:
        payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
        allowed = {"contract-tested", "smoke-workflow", "card-contract-tested", "config-prepared"}
        for integration in payload["integrations"]:
            self.assertIn(integration["proof_status"], allowed)
            self.assertNotEqual(integration["proof_status"], "production-verified")


if __name__ == "__main__":
    unittest.main()
