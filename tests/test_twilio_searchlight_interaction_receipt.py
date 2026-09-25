from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from services.twilio_searchlight_demo.interaction_receipt import (
    build_interaction_receipt,
    write_interaction_receipt,
)


class TwilioInteractionReceiptTests(unittest.TestCase):
    def event(self) -> dict[str, str]:
        return {
            "status": "ok",
            "delivery_status": "new",
            "message_ref": "012345abcdef",
            "decision_id": "decision-live-1",
            "elapsed_ms": "42.0",
        }

    def test_receipt_is_source_bound_and_privacy_minimized(self) -> None:
        event = self.event()
        event.update(
            {
                "Body": "do-not-record-message-body",
                "From": "+15555550123",
                "auth_token": "do-not-record-auth-token",
            }
        )
        receipt = build_interaction_receipt(
            event,
            "a" * 40,
            "https://demo.example/twilio/incoming",
            "<Response><Message>bounded reply</Message></Response>",
        )
        self.assertEqual(receipt["source_sha"], "a" * 40)
        self.assertEqual(receipt["interaction"]["signature_validation"], "twilio_sdk")
        self.assertEqual(receipt["interaction"]["delivery_status"], "new")
        self.assertFalse(receipt["privacy"]["phone_number_recorded"])
        self.assertFalse(receipt["privacy"]["message_body_recorded"])
        serialized = json.dumps(receipt, sort_keys=True)
        self.assertNotIn("do-not-record-message-body", serialized)
        self.assertNotIn("+15555550123", serialized)
        self.assertNotIn("do-not-record-auth-token", serialized)
        self.assertNotIn("https://demo.example/twilio/incoming", serialized)

    def test_human_and_financial_boundaries_remain_false(self) -> None:
        receipt = build_interaction_receipt(
            self.event(),
            "b" * 40,
            "https://demo.example/twilio/incoming",
            "<Response />",
        )
        self.assertTrue(all(value is False for value in receipt["boundaries"].values()))

    def test_invalid_source_sha_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "40-character Git SHA"):
            build_interaction_receipt(
                self.event(), "not-a-sha", "https://demo.example/twilio/incoming", "x"
            )

    def test_non_success_event_cannot_generate_receipt(self) -> None:
        event = self.event()
        event["status"] = "invalid_signature"
        with self.assertRaisesRegex(ValueError, "successful validated interactions"):
            build_interaction_receipt(
                event, "c" * 40, "https://demo.example/twilio/incoming", "x"
            )

    def test_non_https_webhook_cannot_generate_receipt(self) -> None:
        with self.assertRaisesRegex(ValueError, "public HTTPS webhook"):
            build_interaction_receipt(
                self.event(), "d" * 40, "http://127.0.0.1/twilio/incoming", "x"
            )

    def test_writer_uses_hashed_message_reference_filename(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write_interaction_receipt(
                Path(tmp),
                self.event(),
                "e" * 40,
                "https://demo.example/twilio/incoming",
                "<Response />",
            )
            self.assertEqual(path.name, "interaction-012345abcdef.json")
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["source_sha"], "e" * 40)
            self.assertFalse(path.with_suffix(".json.tmp").exists())

    def test_cached_retry_cannot_overwrite_original_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            path = write_interaction_receipt(
                output_dir,
                self.event(),
                "f" * 40,
                "https://demo.example/twilio/incoming",
                "<Response><Message>first response</Message></Response>",
            )
            original = path.read_bytes()
            cached_retry = self.event()
            cached_retry["delivery_status"] = "cached_retry"
            with self.assertRaisesRegex(ValueError, "newly processed deliveries"):
                write_interaction_receipt(
                    output_dir,
                    cached_retry,
                    "f" * 40,
                    "https://demo.example/twilio/incoming",
                    "<Response><Message>cached response</Message></Response>",
                )
            self.assertEqual(path.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
