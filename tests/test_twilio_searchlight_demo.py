from __future__ import annotations

import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from twilio.request_validator import RequestValidator

from services.twilio_searchlight_demo.app import (
    MAX_BODY_CHARS,
    call_hal_decision,
    process_incoming,
    validate_twilio_request,
)


class DecisionHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        self.server.last_payload = payload
        body = json.dumps(
            {"reply": "HAL routed this safely.", "decision_id": "decision-demo-1"}
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: object) -> None:
        return


class TwilioSearchlightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), DecisionHandler)
        cls.server.last_payload = None
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        host, port = cls.server.server_address
        cls.decision_url = f"http://{host}:{port}/decision"
        cls.webhook_url = "https://demo.example/twilio/incoming"
        cls.auth_token = "unit-test-token"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self) -> None:
        self.server.last_payload = None

    def signed_form(
        self, body: str = "Route this through HAL"
    ) -> tuple[dict[str, str], str]:
        form = {"MessageSid": "SM123456", "Body": body}
        signature = RequestValidator(self.auth_token).compute_signature(
            self.webhook_url, form
        )
        return form, signature

    def test_valid_signed_request_calls_hal_and_returns_twiml(self) -> None:
        form, signature = self.signed_form()
        status, twiml, event = process_incoming(
            self.webhook_url,
            form,
            signature,
            self.auth_token,
            self.decision_url,
        )
        self.assertEqual(status, 200)
        self.assertIn("HAL routed this safely.", twiml)
        self.assertEqual(event["status"], "ok")
        self.assertEqual(event["decision_id"], "decision-demo-1")
        self.assertEqual(self.server.last_payload["channel"], "twilio_sms")
        self.assertEqual(self.server.last_payload["message_sid"], "SM123456")
        self.assertNotIn("From", self.server.last_payload)
        self.assertNotIn("To", self.server.last_payload)

    def test_invalid_signature_fails_closed_before_hal(self) -> None:
        form, _ = self.signed_form()
        status, _, event = process_incoming(
            self.webhook_url, form, "invalid", self.auth_token, self.decision_url
        )
        self.assertEqual(status, 403)
        self.assertEqual(event["status"], "invalid_signature")
        self.assertIsNone(self.server.last_payload)

    def test_missing_body_is_rejected(self) -> None:
        form = {"MessageSid": "SM123456", "Body": ""}
        signature = RequestValidator(self.auth_token).compute_signature(
            self.webhook_url, form
        )
        status, _, event = process_incoming(
            self.webhook_url, form, signature, self.auth_token, self.decision_url
        )
        self.assertEqual(status, 400)
        self.assertEqual(event["status"], "invalid_form")
        self.assertIsNone(self.server.last_payload)

    def test_body_is_bounded_before_forwarding(self) -> None:
        form, signature = self.signed_form("x" * (MAX_BODY_CHARS + 100))
        status, _, _ = process_incoming(
            self.webhook_url, form, signature, self.auth_token, self.decision_url
        )
        self.assertEqual(status, 200)
        self.assertEqual(len(self.server.last_payload["body"]), MAX_BODY_CHARS)

    def test_missing_auth_material_never_validates(self) -> None:
        form, signature = self.signed_form()
        self.assertFalse(validate_twilio_request("", form, signature, self.auth_token))
        self.assertFalse(
            validate_twilio_request(self.webhook_url, form, "", self.auth_token)
        )
        self.assertFalse(validate_twilio_request(self.webhook_url, form, signature, ""))

    def test_missing_decision_url_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            call_hal_decision("", "SM123", "hello")


if __name__ == "__main__":
    unittest.main()
