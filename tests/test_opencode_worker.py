from __future__ import annotations

import base64
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from integrations.opencode.worker import (
    OpenCodeClient,
    OpenCodeProtocolError,
    OpenCodeSecurityError,
)


class FakeOpenCodeHandler(BaseHTTPRequestHandler):
    requests_seen: list[dict] = []

    def log_message(self, format: str, *args: object) -> None:
        return

    def _body(self) -> object | None:
        length = int(self.headers.get("Content-Length", "0"))
        if not length:
            return None
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def _record(self, body: object | None) -> None:
        self.__class__.requests_seen.append(
            {
                "method": self.command,
                "path": urlparse(self.path).path,
                "authorization": self.headers.get("Authorization"),
                "body": body,
            }
        )

    def _json(self, status: int, payload: object) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _no_content(self) -> None:
        self.send_response(204)
        self.end_headers()

    def do_GET(self) -> None:
        self._record(None)
        if self.path == "/global/health":
            self._json(200, {"healthy": True, "version": "2.0.test"})
            return
        if self.path == "/api/session/active":
            self._json(200, {"data": {"ses_test": {"type": "running"}}})
            return
        if self.path == "/api/session/ses_test/context":
            self._json(
                200,
                {
                    "data": [
                        {"id": "msg_user", "role": "user"},
                        {"id": "msg_assistant", "role": "assistant"},
                    ]
                },
            )
            return
        self._json(404, {"error": "not found"})

    def do_POST(self) -> None:
        body = self._body()
        self._record(body)
        if self.path == "/api/session":
            self._json(
                200,
                {
                    "data": {
                        "id": "ses_test",
                        "location": body.get("location") if isinstance(body, dict) else None,
                    }
                },
            )
            return
        if self.path == "/api/session/ses_test/prompt":
            self._json(200, {"data": {"id": "input_test", "accepted": True}})
            return
        if self.path in {
            "/api/session/ses_test/wait",
            "/api/session/ses_test/interrupt",
        }:
            self._no_content()
            return
        self._json(404, {"error": "not found"})


class OpenCodeWorkerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        FakeOpenCodeHandler.requests_seen = []
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), FakeOpenCodeHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def setUp(self) -> None:
        FakeOpenCodeHandler.requests_seen = []

    def client(self, **kwargs: object) -> OpenCodeClient:
        return OpenCodeClient(base_url=self.base_url, timeout=2, **kwargs)

    def test_remote_server_is_denied_by_default(self) -> None:
        with self.assertRaises(OpenCodeSecurityError):
            OpenCodeClient(base_url="https://example.com:4096")

    def test_embedded_credentials_are_denied(self) -> None:
        with self.assertRaises(OpenCodeSecurityError):
            OpenCodeClient(base_url="http://opencode:secret@127.0.0.1:4096")

    def test_health_and_active_sessions_follow_v2_paths(self) -> None:
        client = self.client()
        self.assertTrue(client.health()["healthy"])
        self.assertIn("ses_test", client.active_sessions())
        self.assertEqual(
            [item["path"] for item in FakeOpenCodeHandler.requests_seen],
            ["/global/health", "/api/session/active"],
        )

    def test_basic_auth_is_sent_without_embedding_password_in_base_url(self) -> None:
        client = self.client(username="hal", password="super-secret")
        client.health()
        expected = "Basic " + base64.b64encode(b"hal:super-secret").decode("ascii")
        self.assertEqual(FakeOpenCodeHandler.requests_seen[0]["authorization"], expected)
        self.assertNotIn("super-secret", client.base_url)

    def test_run_hal_task_uses_only_bounded_session_endpoints(self) -> None:
        result = self.client().run_hal_task(
            directory="/workspace/HAL_SUPREME",
            mode="fix",
            task="Repair one regression and prove it.",
        )

        self.assertEqual(result["session_id"], "ses_test")
        self.assertEqual(result["mode"], "fix")
        paths = [item["path"] for item in FakeOpenCodeHandler.requests_seen]
        self.assertEqual(
            paths,
            [
                "/api/session",
                "/api/session/ses_test/prompt",
                "/api/session/ses_test/wait",
                "/api/session/ses_test/context",
            ],
        )
        self.assertFalse(any("/shell" in path or "/permission" in path for path in paths))

        create = FakeOpenCodeHandler.requests_seen[0]["body"]
        self.assertEqual(create["location"]["directory"], "/workspace/HAL_SUPREME")

        prompt = FakeOpenCodeHandler.requests_seen[1]["body"]["prompt"]["text"]
        self.assertIn("AGENTS.md", prompt)
        self.assertIn(".opencode/commands/hal-fix.md", prompt)
        self.assertIn("Repair one regression and prove it.", prompt)

    def test_windows_absolute_workspace_is_accepted(self) -> None:
        session = self.client().create_session(r"D:\HAL_SUPREME")
        self.assertEqual(session["id"], "ses_test")

    def test_relative_workspace_is_denied(self) -> None:
        with self.assertRaises(OpenCodeSecurityError):
            self.client().create_session("HAL_SUPREME")

    def test_only_known_hal_modes_are_accepted(self) -> None:
        with self.assertRaises(OpenCodeSecurityError):
            self.client().run_hal_task(
                directory="/workspace/HAL_SUPREME",
                mode="shell",
                task="Do anything",
            )
        self.assertEqual(FakeOpenCodeHandler.requests_seen, [])

    def test_prompt_size_is_bounded(self) -> None:
        with self.assertRaises(OpenCodeSecurityError):
            self.client().prompt("ses_test", "x" * 100_001)

    def test_unexpected_protocol_shape_fails_closed(self) -> None:
        with self.assertRaises(OpenCodeProtocolError):
            self.client().create_session("/does/not/match/fake-route")


if __name__ == "__main__":
    unittest.main()
