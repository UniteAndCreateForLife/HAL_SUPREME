import copy
import unittest

from engine import analyze_case, audit_bundle, load_cases, verify_audit_receipt
from live_model import (
    LiveModelError,
    assert_external_safe,
    find_direct_identifiers,
    normalize_synthesis,
)


class CampusEvidenceDeskTests(unittest.TestCase):
    def setUp(self):
        self.cases = load_cases()
        self.reports = [analyze_case(case) for case in self.cases]

    def test_all_claims_have_valid_citations(self):
        for report in self.reports:
            self.assertEqual(report["validation"]["citation_validity"], 1.0)
            self.assertEqual(report["validation"]["invalid_citations"], [])
            self.assertEqual(report["validation"]["uncited_items"], [])

    def test_seeded_conflicts_are_detected(self):
        for report in self.reports:
            self.assertTrue(report["validation"]["conflict_detection"])

    def test_no_unsupported_material_claims(self):
        for report in self.reports:
            self.assertEqual(report["validation"]["unsupported_material_claims"], 0)

    def test_human_review_is_mandatory(self):
        for report in self.reports:
            self.assertTrue(report["review_gate"]["required"])
            self.assertEqual(report["review_gate"]["status"], "PENDING_HUMAN_REVIEW")

    def test_demo_has_three_distinct_cases(self):
        self.assertEqual(
            {case["id"] for case in self.cases},
            {"policy-conflict", "research-access", "energy-anomaly"},
        )

    def test_model_acceptance_rejects_invalid_or_uncited_items(self):
        case = self.cases[0]
        payload = {
            "summary": "Synthetic model draft",
            "findings": [
                {"text": "Training is complete.", "citations": ["E3"]},
                {"text": "Invented fact.", "citations": ["E99"]},
                {"text": "Uncited fact.", "citations": []},
            ],
            "actions": [{"text": "Escalate conflict.", "citations": ["E1", "E2"]}],
            "conflicts": [{"detail": "Policies conflict.", "evidence": ["E1", "E2"]}],
            "uncertainty": "No other records supplied.",
        }
        result = normalize_synthesis(case, payload)
        self.assertEqual(result["acceptance"]["accepted_items"], 3)
        self.assertEqual(result["acceptance"]["rejected_items"], 2)
        self.assertEqual(result["acceptance"]["invalid_citations"], ["E99"])
        self.assertEqual(len(result["findings"]), 1)

    def test_model_acceptance_rejects_false_conflict_relations(self):
        case = self.cases[1]
        payload = {
            "findings": [{"text": "Approval is missing.", "citations": ["E4"]}],
            "actions": [{"text": "Obtain owner approval.", "citations": ["E2", "E4"]}],
            "conflicts": [{"detail": "These records conflict.", "evidence": ["E2", "E4"]}],
            "uncertainty": "Synthetic evidence only.",
        }
        result = normalize_synthesis(case, payload)
        self.assertEqual(result["conflicts"], [])
        self.assertEqual(result["acceptance"]["unsupported_conflict_relations_rejected"], 1)
        self.assertTrue(result["acceptance"]["model_conflict_detection"])

    def test_model_acceptance_never_mutates_case_evidence(self):
        case = self.cases[1]
        before = [dict(item) for item in case["evidence"]]
        normalize_synthesis(case, {"findings": [], "actions": [], "conflicts": []})
        self.assertEqual(case["evidence"], before)

    def test_audit_receipt_verifies_untampered_report(self):
        for case in self.cases:
            bundle = audit_bundle(case)
            self.assertTrue(verify_audit_receipt(bundle["report"], bundle["receipt"]))
            self.assertEqual(bundle["receipt"]["human_review_status"], "PENDING_HUMAN_REVIEW")
            self.assertEqual(bundle["receipt"]["unsupported_material_claims"], 0)

    def test_audit_receipt_detects_tampering(self):
        bundle = audit_bundle(self.cases[0])
        changed = copy.deepcopy(bundle["report"])
        changed["actions"][0]["text"] += " altered"
        self.assertFalse(verify_audit_receipt(changed, bundle["receipt"]))

    def test_audit_receipt_is_cross_runtime_stable(self):
        bundle = audit_bundle(self.cases[0])
        self.assertEqual(bundle["receipt"]["report_sha256"], "e2bd909a7687b21d7d8204eb4a5417d703717a04f4c110f52b2eb9409948d884")

    def test_canonical_demo_inputs_clear_external_privacy_gate(self):
        for case in self.cases:
            self.assertEqual(find_direct_identifiers(case), [])
            assert_external_safe(case)

    def test_external_privacy_gate_blocks_direct_identifiers_without_echoing_values(self):
        case = copy.deepcopy(self.cases[1])
        case["evidence"].append(
            {
                "id": "E5",
                "type": "unsafe_test_record",
                "text": "Student email alice@example.edu and phone 312-555-0198 must not leave the local trust boundary.",
            }
        )
        hits = find_direct_identifiers(case)
        self.assertEqual({hit["kind"] for hit in hits}, {"email", "phone"})
        serialized = repr(hits)
        self.assertNotIn("alice@example.edu", serialized)
        self.assertNotIn("312-555-0198", serialized)
        with self.assertRaisesRegex(LiveModelError, r"external_model_blocked_direct_identifier:email,phone"):
            assert_external_safe(case)

    def test_external_privacy_gate_blocks_ssn_and_labeled_ids(self):
        case = copy.deepcopy(self.cases[0])
        case["question"] = "Review student ID: CAMPUS-4488 and SSN 123-45-6789."
        hits = find_direct_identifiers(case)
        self.assertEqual({hit["kind"] for hit in hits}, {"labeled_identifier", "us_ssn"})
        with self.assertRaises(LiveModelError):
            assert_external_safe(case)


if __name__ == "__main__":
    unittest.main(verbosity=2)
