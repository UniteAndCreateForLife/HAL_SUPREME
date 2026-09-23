from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from services.twilio_searchlight_demo.rehearsal import run_rehearsal, write_receipt


class TwilioSearchlightRehearsalTests(unittest.TestCase):
    def test_rehearsal_proves_signed_and_rejected_paths(self) -> None:
        receipt = run_rehearsal(source_sha="a" * 40)
        self.assertTrue(receipt["passed"])
        self.assertTrue(all(receipt["checks"].values()))
        self.assertEqual(receipt["valid_request"]["http_status"], 200)
        self.assertEqual(receipt["invalid_signature"]["http_status"], 403)
        self.assertEqual(receipt["valid_request"]["hal_call_count"], 1)
        self.assertEqual(
            receipt["invalid_signature"]["hal_call_count_after_attempt"], 1
        )
        self.assertEqual(
            receipt["request_envelope"]["unsupported_content_type_http_status"], 415
        )
        self.assertEqual(
            receipt["request_envelope"]["oversized_request_http_status"], 413
        )
        self.assertEqual(
            receipt["request_envelope"]["hal_call_count_after_rejections"], 1
        )
        self.assertFalse(receipt["boundaries"]["live_twilio_account_verified"])
        self.assertFalse(receipt["boundaries"]["external_twilio_api_call"])
        self.assertEqual(
            set(receipt["forwarded_payload"]),
            {"channel", "message_sid", "body"},
        )

    def test_receipt_writer_uses_json_file(self) -> None:
        receipt = run_rehearsal(source_sha="b" * 40)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "receipt.json"
            write_receipt(output, receipt)
            self.assertTrue(output.exists())
            text = output.read_text(encoding="utf-8")
            self.assertIn('"passed": true', text)
            self.assertIn(
                '"source_sha": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"', text
            )


if __name__ == "__main__":
    unittest.main()
