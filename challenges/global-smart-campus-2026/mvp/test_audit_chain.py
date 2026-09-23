import copy
import unittest

from audit_chain import append_event, verify_chain
from engine import audit_bundle, load_cases


class AuditChainTests(unittest.TestCase):
    def setUp(self):
        self.bundle = audit_bundle(load_cases()[0])

    def test_valid_chain_verifies(self):
        chain = []
        append_event(
            chain,
            report=self.bundle["report"],
            receipt=self.bundle["receipt"],
            event_type="REVIEW_OPENED",
            actor_role="analyst",
        )
        append_event(
            chain,
            report=self.bundle["report"],
            receipt=self.bundle["receipt"],
            event_type="REVIEW_APPROVED",
            actor_role="reviewer",
            note="Synthetic case accepted after evidence review.",
        )
        self.assertTrue(verify_chain(chain))
        self.assertEqual(chain[1]["previous_event_sha256"], chain[0]["event_sha256"])
        self.assertEqual(chain[1]["report_sha256"], self.bundle["receipt"]["report_sha256"])

    def test_tampering_breaks_chain(self):
        chain = []
        append_event(
            chain,
            report=self.bundle["report"],
            receipt=self.bundle["receipt"],
            event_type="REVIEW_OPENED",
            actor_role="analyst",
        )
        changed = copy.deepcopy(chain)
        changed[0]["event_type"] = "REVIEW_APPROVED"
        self.assertFalse(verify_chain(changed))

    def test_only_reviewer_can_close_review(self):
        with self.assertRaises(PermissionError):
            append_event(
                [],
                report=self.bundle["report"],
                receipt=self.bundle["receipt"],
                event_type="REVIEW_REJECTED",
                actor_role="analyst",
            )

    def test_invalid_report_receipt_is_rejected(self):
        receipt = copy.deepcopy(self.bundle["receipt"])
        receipt["report_sha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "receipt failed verification"):
            append_event(
                [],
                report=self.bundle["report"],
                receipt=receipt,
                event_type="REVIEW_NOTE",
                actor_role="auditor",
            )

    def test_audit_event_excludes_reviewer_identity_and_evidence_text(self):
        chain = []
        event = append_event(
            chain,
            report=self.bundle["report"],
            receipt=self.bundle["receipt"],
            event_type="REVIEW_NOTE",
            actor_role="auditor",
            note="Receipt structure checked.",
        )
        self.assertNotIn("reviewer_name", event)
        self.assertNotIn("evidence", event)
        serialized = repr(event)
        for item in load_cases()[0]["evidence"]:
            self.assertNotIn(item["text"], serialized)


if __name__ == "__main__":
    unittest.main(verbosity=2)
