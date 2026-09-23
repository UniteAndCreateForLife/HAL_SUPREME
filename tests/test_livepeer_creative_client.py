from __future__ import annotations

import json
import unittest

from integrations.livepeer_creative.client import (
    LivepeerCreativeClient,
    McpError,
    TransportResponse,
)


class FakeTransport:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, str], dict]] = []

    def __call__(
        self, endpoint: str, headers: dict[str, str], body: str
    ) -> TransportResponse:
        payload = json.loads(body)
        self.calls.append((endpoint, dict(headers), payload))
        method = payload.get("method")

        if method == "initialize":
            return TransportResponse(
                200,
                {"Mcp-Session-Id": "session-123"},
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": payload["id"],
                        "result": {"protocolVersion": "2025-03-26", "capabilities": {}},
                    }
                ),
            )
        if method == "notifications/initialized":
            return TransportResponse(202, {}, "")
        if method == "tools/list":
            return TransportResponse(
                200,
                {},
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": payload["id"],
                        "result": {
                            "tools": [
                                {
                                    "name": "create_media",
                                    "description": "Create a finished media asset.",
                                    "inputSchema": {
                                        "type": "object",
                                        "properties": {"goal": {"type": "string"}},
                                        "required": ["goal"],
                                    },
                                }
                            ]
                        },
                    }
                ),
            )
        if method == "tools/call":
            return TransportResponse(
                200,
                {},
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": payload["id"],
                        "result": {"content": [{"type": "text", "text": "ok"}]},
                    }
                ),
            )
        raise AssertionError(f"unexpected method {method}")


class LivepeerCreativeClientTests(unittest.TestCase):
    def test_discovers_runtime_schema_and_reuses_session(self) -> None:
        transport = FakeTransport()
        client = LivepeerCreativeClient(transport=transport)
        tools = client.list_tools()
        self.assertEqual([tool.name for tool in tools], ["create_media"])
        list_call = next(
            call for call in transport.calls if call[2].get("method") == "tools/list"
        )
        self.assertEqual(list_call[1]["mcp-session-id"], "session-123")
        self.assertEqual(tools[0].input_schema["required"], ["goal"])

    def test_call_tool_requires_discovered_name(self) -> None:
        client = LivepeerCreativeClient(transport=FakeTransport())
        with self.assertRaises(McpError):
            client.call_tool("definitely_not_real", {})

    def test_call_tool_uses_runtime_tool_name_and_arguments(self) -> None:
        transport = FakeTransport()
        client = LivepeerCreativeClient(transport=transport)
        result = client.call_tool("create_media", {"goal": "science hero"})
        self.assertEqual(result["result"]["content"][0]["text"], "ok")
        rpc = [
            call[2] for call in transport.calls if call[2].get("method") == "tools/call"
        ][0]
        self.assertEqual(rpc["params"]["name"], "create_media")
        self.assertEqual(rpc["params"]["arguments"]["goal"], "science hero")

    def test_bearer_stays_in_header_not_rpc_body(self) -> None:
        transport = FakeTransport()
        client = LivepeerCreativeClient(bearer="sk_secret_value", transport=transport)
        client.list_tools()
        endpoint, headers, rpc = transport.calls[0]
        self.assertEqual(headers["authorization"], "Bearer sk_secret_value")
        self.assertNotIn("sk_secret_value", json.dumps(rpc))


if __name__ == "__main__":
    unittest.main()
