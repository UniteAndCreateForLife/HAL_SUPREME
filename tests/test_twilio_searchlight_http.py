from __future__ import annotations

import json
import tempfile
import threading
import unittest
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib import parse, request
from unittest.mock import patch

from twilio.request_validator import RequestValidator

from services.twilio_searchlight_demo.app import Handler


class DecisionHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        self.server.last_payload = json.loads(self.rfile.read(length).decode("utf-8"))
        payload = json.dumps(
            {"reply": "HAL end-to-end reply.", "decision_id": "decision-http-1"}
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt: str, *args: object) -> None:
        return


class TwilioSearchlightHttpTests(unittest.TestCase):
    def test_signed_webhook_round_trip_over_http(self) -> None:
        decision = ThreadingHTTPServer(("127.0.0.1", 0), DecisionHandler)
        decision.last_payload = None
        decision_thread = threading.Thread(target=decision.serve_forever, daemon=True)
        decision_thread.start()
        webhook = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        webhook_thread = threading.Thread(target=webhook.serve_forever, daemon=True)
        webhook_thread.start()
        try:
            decision_url = f"http://127.0.0.1:{decision.server_address[1]}/decision"
            local_url = f"http://127.0.0.1:{webhook.server_address[1]}/twilio/incoming"
            signed_url = "https://demo.example/twilio/incoming"
            auth_token = "unit-test-token"
            form = {"MessageSid": "SMHTTP123", "Body": "hello from signed webhook"}
            signature = RequestValidator(auth_token).compute_signature(signed_url, form)
            data = parse.urlencode(form).encode("utf-8")
            req = request.Request(
                local_url,
                data=data,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "X-Twilio-Signature": signature,
                },
                method="POST",
            )
            with (
                tempfile.TemporaryDirectory() as receipt_dir,
                patch.dict(
                    "os.environ",
                    {
                        "TWILIO_AUTH_TOKEN": auth_token,
                        "HAL_TWILIO_WEBHOOK_URL": signed_url,
                        "HAL_SEARCHLIGHT_DECISION_URL": decision_url,
                        "HAL_SEARCHLIGHT_RECEIPT_DIR": receipt_dir,
                        "HAL_SEARCHLIGHT_SOURCE_SHA": "f" * 40,
                    },
                    clear=False,
                ),
            ):
                with request.urlopen(req, timeout=3) as response:
                    twiml = response.read().decode("utf-8")
                    self.assertEqual(response.status, 200)
                receipts = list(Path(receipt_dir).glob("interaction-*.json"))
                self.assertEqual(len(receipts), 1)
                receipt = json.loads(receipts[0].read_text(encoding="utf-8"))
                self.assertEqual(receipt["source_sha"], "f" * 40)
                self.assertEqual(
                    receipt["interaction"]["signature_validation"], "twilio_sdk"
                )
                self.assertFalse(receipt["privacy"]["message_body_recorded"])
            self.assertIn("HAL end-to-end reply.", twiml)
            self.assertEqual(decision.last_payload["channel"], "twilio_sms")
            self.assertEqual(decision.last_payload["message_sid"], "SMHTTP123")
            self.assertEqual(decision.last_payload["body"], "hello from signed webhook")
        finally:
            webhook.shutdown()
            webhook.server_close()
            decision.shutdown()
            decision.server_close()


if __name__ == "__main__":
    unittest.main()
