from __future__ import annotations

import hashlib
import json
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

from twilio.request_validator import RequestValidator

from services.twilio_searchlight_demo.app import call_hal_decision, process_incoming


class OperatorGatewayHandler(BaseHTTPRequestHandler):
    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        if self.path != "/operator/commands":
            self._json(404, {"error": "not_found"})
            return
        length = int(self.headers.get("Content-Length", "0"))
        self.server.last_command = json.loads(self.rfile.read(length))
        self._json(200, self.server.command_response)

    def do_GET(self) -> None:
        if self.path != "/operator/operations/op_test_1":
            self._json(404, {"error": "not_found"})
            return
        self.server.poll_count += 1
        if self.server.poll_count <= self.server.pending_polls:
            self._json(
                200,
                {
                    "operation_id": "op_test_1",
                    "capability_id": "operator.conversation",
                    "state": "EXECUTING",
                },
            )
        else:
            self._json(200, self.server.operation_response)

    def log_message(self, fmt: str, *args: object) -> None:
        return


class TwilioOperatorAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), OperatorGatewayHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f"http://127.0.0.1:{cls.server.server_address[1]}/operator/commands"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self) -> None:
        self.server.last_command = None
        self.server.poll_count = 0
        self.server.pending_polls = 1
        self.server.command_response = {
            "operation_id": "op_test_1",
            "state": "ACCEPTED",
            "capability_id": "operator.conversation",
        }
        self.server.operation_response = {
            "operation_id": "op_test_1",
            "capability_id": "operator.conversation",
            "state": "VERIFIED",
            "verification": {"verified": True},
            "after": {
                "ok": True,
                "reply": "HAL chose the bounded next step.",
                "model": "qwen3.5:9b",
                "response_state": "PROVIDER_RESPONSE",
            },
        }

    def test_submits_minimized_private_conversation_and_uses_verified_reply(
        self,
    ) -> None:
        result = call_hal_decision(self.url, "SM123456", "What is next?", 2.0)

        self.assertEqual(result["reply"], "HAL chose the bounded next step.")
        self.assertEqual(result["decision_id"], "op_test_1")
        self.assertGreaterEqual(self.server.poll_count, 2)
        command = self.server.last_command
        self.assertEqual(command["capability_id"], "operator.conversation")
        self.assertEqual(command["input"]["text"], "What is next?")
        self.assertEqual(command["input"]["provider_mode"], "private_local")
        self.assertEqual(
            command["input"]["conversation_profile"], "FAST_PRIVATE_CHOICE"
        )
        self.assertFalse(command["input"]["present_on_oracle"])
        self.assertEqual(
            command["input"]["conversation_id"],
            "twilio_sms_" + hashlib.sha256(b"SM123456").hexdigest()[:24],
        )
        self.assertNotIn("SM123456", json.dumps(command))
        self.assertNotIn("From", json.dumps(command))
        self.assertNotIn("To", json.dumps(command))

    def test_signature_gate_precedes_operator_conversation(self) -> None:
        webhook_url = "https://demo.example/twilio/incoming"
        auth_token = "unit-test-token"
        form = {
            "MessageSid": "SM123456",
            "Body": "What is next?",
            "From": "+15555550123",
        }
        signature = RequestValidator(auth_token).compute_signature(webhook_url, form)

        status, twiml, event = process_incoming(
            webhook_url, form, signature, auth_token, self.url
        )
        self.assertEqual(status, 200)
        self.assertIn("HAL chose the bounded next step.", twiml)
        self.assertEqual(event["decision_id"], "op_test_1")
        self.assertNotIn("+15555550123", json.dumps(self.server.last_command))

        self.server.last_command = None
        status, _, event = process_incoming(
            webhook_url, form, "bad-signature", auth_token, self.url
        )
        self.assertEqual(status, 403)
        self.assertEqual(event["status"], "invalid_signature")
        self.assertIsNone(self.server.last_command)

    def test_failed_or_unverified_operation_never_becomes_sms_reply(self) -> None:
        self.server.operation_response["state"] = "FAILED"
        with self.assertRaises(ValueError):
            call_hal_decision(self.url, "SM123456", "hello", 1.0)
        self.assertEqual(
            self.server.last_command["capability_id"], "operator.conversation"
        )

        self.server.poll_count = 0
        self.server.operation_response["state"] = "VERIFIED"
        self.server.operation_response["verification"]["verified"] = False
        with self.assertRaises(ValueError):
            call_hal_decision(self.url, "SM123456", "hello", 1.0)
        self.assertGreater(self.server.poll_count, 0)

    def test_non_model_reply_and_missing_operation_id_fail_closed(self) -> None:
        self.server.operation_response["after"]["response_state"] = (
            "DEGRADED_CONTINUITY_REPLY"
        )
        with self.assertRaises(ValueError):
            call_hal_decision(self.url, "SM123456", "hello", 1.0)
        self.assertGreater(self.server.poll_count, 0)

        self.server.poll_count = 0
        self.server.command_response = {"state": "ACCEPTED", "operation_id": None}
        with self.assertRaises(ValueError):
            call_hal_decision(self.url, "SM123456", "hello", 1.0)
        self.assertEqual(self.server.poll_count, 0)

    def test_operator_gateway_must_be_loopback_and_poll_is_bounded(self) -> None:
        with patch(
            "urllib.request.urlopen", side_effect=AssertionError("network used")
        ):
            with self.assertRaises(ValueError):
                call_hal_decision(
                    "https://public.example/operator/commands", "SM123456", "hello", 1.0
                )
        self.server.pending_polls = 1000
        started = time.monotonic()
        with self.assertRaises(TimeoutError):
            call_hal_decision(self.url, "SM123456", "hello", 0.25)
        self.assertLess(time.monotonic() - started, 1.0)

    def test_external_decision_fallback_is_not_supported(self) -> None:
        with patch(
            "urllib.request.urlopen", side_effect=AssertionError("network used")
        ):
            with self.assertRaisesRegex(ValueError, "exact loopback commands URL"):
                call_hal_decision(
                    "http://127.0.0.1:8766/decision",
                    "SM123456",
                    "hello",
                    1.0,
                )


if __name__ == "__main__":
    unittest.main()
