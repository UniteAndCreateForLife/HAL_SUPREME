"""Adversarial evidence and citation tests for the Evidence Gate (issue #40).

Run with:
    python -m unittest -v examples.evidence_gate.test_adversarial_fixture
"""
from __future__ import annotations

import unittest

from examples.evidence_gate import evidence_gate as g

CASE_A = [
    {"id": "A1", "text": "Lab access requires written approval from the faculty advisor."},
    {"id": "A2", "text": "Lab access is granted automatically upon student registration."},
    {"id": "A3", "text": "The annual department conference will take place in October."},
]
CASE_A_CONFLICTS = [["A1", "A2"]]
CASE_B = [
    {"id": "B1", "text": "Building safety inspections are conducted every spring."},
]


def reasons(result: g.GateResult) -> list[tuple[str, int, str]]:
    return [(row["section"], row["index"], row["reason"]) for row in result.rejected]


class AdversarialCitations(unittest.TestCase):
    def test_finding_without_citation_is_rejected(self):
        draft = {
            "findings": [
                {"text": "A finding with empty citations list.", "citations": []},
                {"text": "A finding with no citations key."},
            ]
        }
        result = g.check(draft, CASE_A)
        self.assertFalse(result.ok)
        self.assertEqual(reasons(result), [("findings", 0, g.NO_CITATION), ("findings", 1, g.NO_CITATION)])
        self.assertEqual(result.accepted["findings"], [])

    def test_unknown_evidence_id_is_rejected(self):
        draft = {"findings": [{"text": "Finding citing unknown evidence.", "citations": ["A9"]}]}
        result = g.check(draft, CASE_A)
        self.assertFalse(result.ok)
        self.assertEqual(
            result.rejected,
            [{"section": "findings", "index": 0, "reason": g.UNKNOWN_EVIDENCE, "invalid_citations": ["A9"]}],
        )
        self.assertEqual(result.to_dict()["invalid_citations"], ["A9"])
        self.assertEqual(result.accepted["findings"], [])

    def test_evidence_from_another_case_is_rejected(self):
        draft = {"actions": [{"text": "Action citing evidence from case B.", "citations": ["B1"]}]}
        result_a = g.check(draft, CASE_A)
        self.assertFalse(result_a.ok)
        self.assertEqual(
            result_a.rejected,
            [{"section": "actions", "index": 0, "reason": g.UNKNOWN_EVIDENCE, "invalid_citations": ["B1"]}],
        )
        self.assertEqual(result_a.accepted["actions"], [])

        result_b = g.check(draft, CASE_B)
        self.assertTrue(result_b.ok)
        self.assertEqual(result_b.accepted["actions"], [{"text": "Action citing evidence from case B.", "citations": ["B1"]}])

    def test_real_citation_cannot_vouch_for_an_invented_one(self):
        draft = {"findings": [{"text": "Finding citing valid and invalid evidence.", "citations": ["A1", "A9"]}]}
        result = g.check(draft, CASE_A)
        self.assertFalse(result.ok)
        self.assertEqual(
            result.rejected,
            [{"section": "findings", "index": 0, "reason": g.UNKNOWN_EVIDENCE, "invalid_citations": ["A9"]}],
        )
        self.assertEqual(result.accepted["findings"], [])


class AdversarialConflicts(unittest.TestCase):
    def test_declared_contradiction_is_accepted(self):
        draft = {"conflicts": [{"detail": "A1 and A2 state contradictory access policies.", "evidence": ["A1", "A2"]}]}
        result = g.check(draft, CASE_A, conflicts=CASE_A_CONFLICTS)
        self.assertTrue(result.ok)
        self.assertEqual(
            result.accepted["conflicts"],
            [{"detail": "A1 and A2 state contradictory access policies.", "evidence": ["A1", "A2"]}],
        )
        self.assertEqual(result.missed_conflicts, [])

    def test_undeclared_contradiction_is_rejected(self):
        draft_a1_a2 = {"conflicts": [{"detail": "A1 and A2 contradict each other.", "evidence": ["A1", "A2"]}]}
        result_no_rules = g.check(draft_a1_a2, CASE_A)
        self.assertFalse(result_no_rules.ok)
        self.assertEqual(reasons(result_no_rules), [("conflicts", 0, g.UNSUPPORTED_CONFLICT)])

        draft_a1_a3 = {"conflicts": [{"detail": "A1 and A3 contradict each other.", "evidence": ["A1", "A3"]}]}
        result_with_rules = g.check(draft_a1_a3, CASE_A, conflicts=CASE_A_CONFLICTS)
        self.assertFalse(result_with_rules.ok)
        self.assertEqual(reasons(result_with_rules), [("conflicts", 0, g.UNSUPPORTED_CONFLICT)])
        self.assertEqual(result_with_rules.missed_conflicts, [["A1", "A2"]])

    def test_conflict_naming_one_id_is_rejected(self):
        draft = {
            "conflicts": [
                {"detail": "Conflict citing a single evidence ID.", "evidence": ["A1"]},
                {"detail": "Conflict citing duplicated evidence IDs.", "evidence": ["A1", "A1"]},
            ]
        }
        result = g.check(draft, CASE_A, conflicts=CASE_A_CONFLICTS)
        self.assertFalse(result.ok)
        self.assertEqual(
            reasons(result),
            [("conflicts", 0, g.CONFLICT_NEEDS_TWO_IDS), ("conflicts", 1, g.CONFLICT_NEEDS_TWO_IDS)],
        )
        self.assertEqual(result.accepted["conflicts"], [])


class AcceptedButUnverified(unittest.TestCase):
    """The gate checks grounding (valid citations and declared conflicts), not meaning, so a person still reviews accepted items."""

    def test_grounded_finding_and_action_are_accepted(self):
        draft = {
            "findings": [{"text": "Lab access requires written advisor approval.", "citations": ["A1"]}],
            "actions": [
                {
                    "text": "Require students to submit advisor approval before granting lab access.",
                    "citations": ["A1", "A2"],
                }
            ],
        }
        result = g.check(draft, CASE_A, conflicts=CASE_A_CONFLICTS)
        self.assertTrue(result.ok)
        self.assertEqual(result.accepted["findings"], draft["findings"])
        self.assertEqual(result.accepted["actions"], draft["actions"])

    def test_supplied_but_irrelevant_citation_is_accepted(self):
        draft = {"findings": [{"text": "Lab access requires advisor approval.", "citations": ["A3"]}]}
        # The gate checks grounding, not semantic relevance, so it cannot tell citation A3 (about the October conference) is irrelevant.
        result = g.check(draft, CASE_A)
        self.assertTrue(result.ok)
        self.assertEqual(result.accepted["findings"], draft["findings"])

    def test_recommendation_phrased_as_fact_is_accepted(self):
        draft = {"actions": [{"text": "After-hours lab access is suspended.", "citations": ["A1", "A2"]}]}
        # The gate checks citation validity and structure rather than semantic tone or truth, so recommendations phrased as observed facts are accepted.
        result = g.check(draft, CASE_A, conflicts=CASE_A_CONFLICTS)
        self.assertTrue(result.ok)
        self.assertEqual(result.accepted["actions"], draft["actions"])


class MixedDraft(unittest.TestCase):
    def test_no_adversarial_item_is_accepted(self):
        draft = {
            "findings": [
                {"text": "Advisor approval is required.", "citations": ["A1"]},
                {"text": "Finding with empty citation list.", "citations": []},
                {"text": "Finding with no citation key."},
                {"text": "Finding citing unknown evidence A9.", "citations": ["A9"]},
                {"text": "Finding citing evidence B1 from another case.", "citations": ["B1"]},
                {"text": "Finding citing real A1 and invented A9.", "citations": ["A1", "A9"]},
            ],
            "actions": [
                {"text": "Pause approval until conflict is resolved.", "citations": ["A1", "A2"]},
            ],
            "conflicts": [
                {"detail": "A1 and A2 contradict each other.", "evidence": ["A1", "A2"]},
                {"detail": "Undeclared conflict between A1 and A3.", "evidence": ["A1", "A3"]},
                {"detail": "Conflict naming only one ID.", "evidence": ["A1"]},
            ],
        }
        result = g.check(draft, CASE_A, conflicts=CASE_A_CONFLICTS)
        self.assertFalse(result.ok)
        self.assertEqual(
            reasons(result),
            [
                ("findings", 1, g.NO_CITATION),
                ("findings", 2, g.NO_CITATION),
                ("findings", 3, g.UNKNOWN_EVIDENCE),
                ("findings", 4, g.UNKNOWN_EVIDENCE),
                ("findings", 5, g.UNKNOWN_EVIDENCE),
                ("conflicts", 1, g.UNSUPPORTED_CONFLICT),
                ("conflicts", 2, g.CONFLICT_NEEDS_TWO_IDS),
            ],
        )
        self.assertEqual(
            result.accepted,
            {
                "findings": [{"text": "Advisor approval is required.", "citations": ["A1"]}],
                "actions": [{"text": "Pause approval until conflict is resolved.", "citations": ["A1", "A2"]}],
                "conflicts": [{"detail": "A1 and A2 contradict each other.", "evidence": ["A1", "A2"]}],
            },
        )


if __name__ == "__main__":
    unittest.main()
