from __future__ import annotations

import unittest

from services.twilio_searchlight_demo.judge_packet import (
    build_judge_packet,
    render_markdown,
    validate_rehearsal,
)


def passing_receipt(source_sha: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "source_sha": source_sha,
        "passed": True,
        "checks": {"signed_path": True, "rejected_path": True},
        "boundaries": {
            "live_twilio_account_verified": False,
            "external_twilio_api_call": False,
            "money_spent": False,
            "application_submitted": False,
            "honoree_selected": False,
            "credits_awarded": False,
            "payment_received": False,
        },
        "forwarded_payload": {
            "channel": "twilio_sms",
            "message_sid": "SMTEST",
            "body": "bounded request",
        },
    }


class TwilioSearchlightJudgePacketTests(unittest.TestCase):
    def test_packet_maps_technical_evidence_without_crossing_live_gate(self) -> None:
        sha = "a" * 40
        packet = build_judge_packet(passing_receipt(sha), sha)
        self.assertTrue(packet["technical_rehearsal_ready"])
        self.assertFalse(packet["live_working_demo_verified"])
        self.assertFalse(packet["application_ready"])
        self.assertEqual(packet["submission_state"], "not_submitted")
        self.assertEqual(packet["award_state"], "not_awarded")
        self.assertEqual(packet["payment_state"], "not_paid")
        self.assertEqual(
            packet["judge_criteria"]["technical_impact"]["status"],
            "technical_evidence_present",
        )

    def test_source_sha_mismatch_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "source SHA"):
            validate_rehearsal(passing_receipt("a" * 40), "b" * 40)

    def test_failing_rehearsal_is_rejected(self) -> None:
        sha = "c" * 40
        receipt = passing_receipt(sha)
        receipt["passed"] = False
        with self.assertRaisesRegex(ValueError, "not passing"):
            build_judge_packet(receipt, sha)

    def test_rehearsal_cannot_self_promote_submission_or_award(self) -> None:
        sha = "d" * 40
        receipt = passing_receipt(sha)
        receipt["boundaries"]["application_submitted"] = True
        with self.assertRaisesRegex(ValueError, "application_submitted"):
            build_judge_packet(receipt, sha)

    def test_non_minimized_payload_is_rejected(self) -> None:
        sha = "e" * 40
        receipt = passing_receipt(sha)
        receipt["forwarded_payload"]["from"] = "+15555555555"
        with self.assertRaisesRegex(ValueError, "not minimized"):
            build_judge_packet(receipt, sha)

    def test_markdown_states_live_demo_boundary(self) -> None:
        sha = "f" * 40
        text = render_markdown(build_judge_packet(passing_receipt(sha), sha))
        self.assertIn("not** a live Twilio account demo", text)
        self.assertIn("Live working demo verified: `false`", text)
        self.assertIn("One story → one persona → one outcome", text)


if __name__ == "__main__":
    unittest.main()
