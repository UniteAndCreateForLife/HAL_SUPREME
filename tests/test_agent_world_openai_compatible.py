from __future__ import annotations

import json
import unittest

from examples.agent_world_arena.http_action_adapter import OpenAICompatibleActionAdapter
from examples.agent_world_arena.ollama_local import OllamaActionAdapter
from examples.agent_world_arena.protocol import Observation


class FakeTransport:
    def __init__(self) -> None:
        self.calls = []

    def post_json(self, url, *, headers, payload, timeout_seconds):
        self.calls.append(
            {
                "url": url,
                "headers": dict(headers),
                "payload": dict(payload),
                "timeout_seconds": timeout_seconds,
            }
        )
        return {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "kind": "idle",
                                "dx": 0,
                                "dy": 0,
                                "target": None,
                                "message": None,
                            }
                        )
                    }
                }
            ]
        }


def observation() -> Observation:
    return Observation(
        episode_id="compat",
        tick=0,
        agent_id="slot-a",
        position=(0, 0),
        energy=100,
        score=0,
        visible_resources=(),
        inbox=(),
        capabilities=("idle", "move", "gather", "say"),
    )


class OpenAICompatibleAdapterTests(unittest.TestCase):
    def test_hosted_adapter_uses_bearer_without_exposing_key_in_repr(self) -> None:
        transport = FakeTransport()
        adapter = OpenAICompatibleActionAdapter(
            provider_id="hosted-x",
            model="model-x",
            base_url="https://example.invalid/v1",
            api_key="secret-x",
            transport=transport,
        )

        adapter.decide(observation())

        self.assertEqual(
            transport.calls[0]["headers"]["Authorization"],
            "Bearer secret-x",
        )
        self.assertNotIn("secret-x", repr(adapter))
        self.assertEqual(
            transport.calls[0]["url"],
            "https://example.invalid/v1/chat/completions",
        )

    def test_local_adapter_can_run_without_authorization_header(self) -> None:
        transport = FakeTransport()
        adapter = OllamaActionAdapter(model="local-test", transport=transport)

        action = adapter.decide(observation())

        self.assertEqual(action.kind, "idle")
        self.assertNotIn("Authorization", transport.calls[0]["headers"])
        self.assertEqual(
            transport.calls[0]["url"],
            "http://127.0.0.1:11434/v1/chat/completions",
        )
        self.assertIn("response_format", transport.calls[0]["payload"])
        self.assertNotIn("reasoning_effort", transport.calls[0]["payload"])

    def test_non_structured_compatibility_mode_omits_response_format(self) -> None:
        transport = FakeTransport()
        adapter = OpenAICompatibleActionAdapter(
            provider_id="legacy",
            model="legacy-model",
            base_url="http://127.0.0.1:9999/v1",
            structured_output=False,
            transport=transport,
        )

        adapter.decide(observation())

        self.assertNotIn("response_format", transport.calls[0]["payload"])
        self.assertNotIn("structured-output", adapter.provider.capabilities)


if __name__ == "__main__":
    unittest.main()
