from __future__ import annotations

import unittest

from services.twilio_searchlight_demo.submission_gate import (
    build_submission_readiness,
    validate_interaction_receipt,
)


def judge_packet(source_sha: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "source_sha": source_sha,
        "technical_rehearsal_ready": True,
        "boundaries": {
            "live_twilio_account_verified": False,
            "external_twilio_api_call": False,
            "money_spent": False,
            "application_submitted": False,
            "honoree_selected": False,
            "credits_awarded": False,
            "payment_received": False,
        },
    }


def interaction_receipt(source_sha: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "source_sha": source_sha,
        "interaction": {
            "status": "ok",
            "signature_validation": "twilio_sdk",
            "delivery_status": "new",
            "message_ref": "012345abcdef",
            "decision_id": "decision-live-1",
            "webhook_url_sha256": "a" * 64,
            "twiml_sha256": "b" * 64,
        },
        "privacy": {
            "phone_number_recorded": False,
            "message_body_recorded": False,
            "auth_token_recorded": False,
            "webhook_url_recorded": False,
        },
        "boundaries": {
            "live_twilio_account_verified": False,
            "application_submitted": False,
            "honoree_selected": False,
            "credits_awarded": False,
            "payment_received": False,
            "money_spent": False,
        },
    }


class TwilioSearchlightSubmissionGateTests(unittest.TestCase):
    def test_missing_live_receipt_fails_closed_without_error(self) -> None:
        sha = "1" * 40
        readiness = build_submission_readiness(judge_packet(sha), sha)
        self.assertFalse(readiness["genuine_signed_twilio_interaction_verified"])
        self.assertFalse(readiness["machine_evidence_ready"])
        self.assertFalse(readiness["application_ready"])
        self.assertEqual(readiness["submission_state"], "not_submitted")
        self.assertIn(
            "genuine_signed_twilio_interaction_receipt_missing",
            readiness["blockers"],
        )

    def test_live_receipt_advances_machine_evidence_but_not_human_gate(self) -> None:
        sha = "2" * 40
        readiness = build_submission_readiness(
            judge_packet(sha), sha, interaction_receipt(sha)
        )
        self.assertTrue(readiness["genuine_signed_twilio_interaction_verified"])
        self.assertTrue(readiness["machine_evidence_ready"])
        self.assertFalse(readiness["human_application_attestations_complete"])
        self.assertFalse(readiness["application_ready"])
        self.assertEqual(readiness["submission_state"], "not_submitted")
        self.assertEqual(
            readiness["blockers"], ["human_application_attestations_pending"]
        )

    def test_cached_retry_receipt_is_rejected(self) -> None:
        sha = "3" * 40
        receipt = interaction_receipt(sha)
        receipt["interaction"]["delivery_status"] = "cached_retry"
        with self.assertRaisesRegex(ValueError, "newly processed"):
            validate_interaction_receipt(receipt, sha)

    def test_source_mismatch_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "source SHA"):
            build_submission_readiness(judge_packet("4" * 40), "5" * 40)

    def test_privacy_boundary_violation_is_rejected(self) -> None:
        sha = "6" * 40
        receipt = interaction_receipt(sha)
        receipt["privacy"]["message_body_recorded"] = True
        with self.assertRaisesRegex(ValueError, "privacy boundary"):
            validate_interaction_receipt(receipt, sha)

    def test_receipt_cannot_claim_submission_or_award(self) -> None:
        sha = "7" * 40
        receipt = interaction_receipt(sha)
        receipt["boundaries"]["application_submitted"] = True
        with self.assertRaisesRegex(ValueError, "application_submitted"):
            validate_interaction_receipt(receipt, sha)


if __name__ == "__main__":
    unittest.main()
