"""Tests for the Evidence Gate. Run from the repository root:

    python -m unittest -v examples.evidence_gate.test_evidence_gate
"""
from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

from examples.evidence_gate import evidence_gate as g

EVIDENCE = ["E1", "E2", "E3"]
CAMPUS = Path(__file__).resolve().parents[2] / "challenges" / "global-smart-campus-2026"


def reasons(result):
    return [(row["section"], row["index"], row["reason"]) for row in result.rejected]


class Grounding(unittest.TestCase):
    def test_a_grounded_draft_passes_whole(self):
        draft = {
            "findings": [{"text": "Memo A requires chair approval.", "citations": ["E1"]}],
            "actions": [{"text": "Pause approval until the memos agree.", "citations": ["E1", "E2"]}],
            "conflicts": [{"detail": "The memos prescribe different approval paths.", "evidence": ["E1", "E2"]}],
        }
        result = g.check(draft, EVIDENCE, conflicts=[["E1", "E2"]])
        self.assertTrue(result.ok)
        self.assertEqual(result.accepted["findings"], draft["findings"])
        self.assertEqual(result.accepted["actions"], draft["actions"])
        self.assertEqual(result.accepted["conflicts"], draft["conflicts"])
        self.assertEqual(result.missed_conflicts, [])

    def test_an_item_without_citations_is_rejected(self):
        draft = {"findings": [{"text": "No source.", "citations": []}, {"text": "No field at all."},
                              {"text": "Blank ids.", "citations": [" ", ""]}]}
        result = g.check(draft, EVIDENCE)
        self.assertEqual(reasons(result), [("findings", i, g.NO_CITATION) for i in range(3)])
        self.assertEqual(result.accepted["findings"], [])

    def test_one_unknown_id_rejects_the_whole_item(self):
        result = g.check({"actions": [{"text": "Approve it.", "citations": ["E1", "E9"]}]}, EVIDENCE)
        self.assertEqual(result.rejected, [{"section": "actions", "index": 0, "reason": g.UNKNOWN_EVIDENCE,
                                            "invalid_citations": ["E9"]}])
        self.assertEqual(result.to_dict()["invalid_citations"], ["E9"])

    def test_duplicates_are_merged_and_an_invented_id_cannot_hide_past_the_cap(self):
        repeated = g.check({"findings": [{"text": "t", "citations": ["E1", "E2", "E3", "E1", "E2", "E3", "E1"]}]}, EVIDENCE)
        self.assertTrue(repeated.ok)
        self.assertEqual(repeated.accepted["findings"][0]["citations"], ["E1", "E2", "E3"])

        evidence = [f"E{i}" for i in range(1, 8)]
        seventh_invented = g.check({"findings": [{"text": "t", "citations": evidence[:6] + ["E99"]}]}, evidence)
        self.assertEqual(reasons(seventh_invented), [("findings", 0, g.TOO_MANY_CITATIONS)])
        within_cap = g.check({"findings": [{"text": "t", "citations": evidence[:5] + ["E99"]}]}, evidence)
        self.assertEqual(reasons(within_cap), [("findings", 0, g.UNKNOWN_EVIDENCE)])

    def test_citations_that_are_not_strings_or_not_a_list_are_rejected(self):
        draft = {"findings": [{"text": "a", "citations": [1, "E1"]}, {"text": "b", "citations": [True]},
                              {"text": "c", "citations": [None]}, {"text": "d", "citations": "E1"}]}
        result = g.check(draft, EVIDENCE)
        self.assertEqual([row["reason"] for row in result.rejected],
                         [g.UNKNOWN_EVIDENCE, g.UNKNOWN_EVIDENCE, g.UNKNOWN_EVIDENCE, g.NO_CITATION])

    def test_text_is_cleaned_but_other_languages_are_kept(self):
        hidden = "Approve​ now‮\U000E0041\U000E0042\x07   please\t\n"
        result = g.check({"findings": [{"text": hidden, "citations": ["E1"]},
                                       {"text": "Zulassung: Genehmigung des Lehrstuhls nötig — 承認", "citations": ["E1"]},
                                       {"text": "​‍\x00 \t", "citations": ["E1"]},
                                       {"text": "x" * 700, "citations": ["E1"]}]}, EVIDENCE)
        texts = [item["text"] for item in result.accepted["findings"]]
        self.assertEqual(texts[0], "Approve now please")
        self.assertEqual(texts[1], "Zulassung: Genehmigung des Lehrstuhls nötig — 承認")
        self.assertEqual(len(texts[2]), 600)
        self.assertEqual(reasons(result), [("findings", 2, g.EMPTY_TEXT)])

    def test_only_checked_fields_are_passed_on(self):
        row = {"text": "t", "citations": ["E1"], "confidence": 0.99, "tool_call": {"name": "send_email"}}
        result = g.check({"findings": [row]}, EVIDENCE)
        self.assertEqual(result.accepted["findings"], [{"text": "t", "citations": ["E1"]}])


class Structure(unittest.TestCase):
    def test_bad_shapes_are_rejected_and_missing_sections_are_fine(self):
        self.assertEqual(reasons(g.check(["not", "a", "dict"], EVIDENCE)), [("draft", 0, g.NOT_AN_OBJECT)])
        self.assertEqual(reasons(g.check({"actions": {"text": "t"}}, EVIDENCE)), [("actions", 0, g.NOT_A_LIST)])
        self.assertEqual(reasons(g.check({"findings": ["just a string"]}, EVIDENCE)), [("findings", 0, g.NOT_AN_OBJECT)])
        empty = g.check({}, EVIDENCE)
        self.assertTrue(empty.ok)
        self.assertEqual(empty.accepted, {"findings": [], "actions": [], "conflicts": []})

    def test_rows_over_the_limit_are_rejected_not_dropped(self):
        draft = {"findings": [{"text": f"f{i}", "citations": ["E1"]} for i in range(5)]}
        result = g.check(draft, EVIDENCE, limits={"findings": 3})
        self.assertEqual(len(result.accepted["findings"]), 3)
        self.assertEqual(reasons(result), [("findings", 3, g.OVER_LIMIT), ("findings", 4, g.OVER_LIMIT)])

    def test_evidence_can_be_ids_or_objects_and_must_have_ids(self):
        objects = [{"id": "E1", "text": "memo"}, {"id": " E2 "}]
        self.assertTrue(g.check({"findings": [{"text": "t", "citations": ["E2"]}]}, objects).ok)
        with self.assertRaises(ValueError):
            g.check({}, [{"text": "no id"}])
        with self.assertRaises(ValueError):
            g.check({}, ["E1", " "])

    def test_the_same_input_gives_the_same_json(self):
        draft = {"findings": [{"text": "t", "citations": ["E2", "E1"]}], "conflicts": [{"detail": "d", "evidence": ["E2", "E1"]}]}
        first = json.dumps(g.check(draft, EVIDENCE, conflicts=[("E1", "E2")]).to_dict(), sort_keys=True)
        second = json.dumps(g.check(draft, EVIDENCE, conflicts=[("E1", "E2")]).to_dict(), sort_keys=True)
        self.assertEqual(first, second)


class Conflicts(unittest.TestCase):
    def conflict(self, *ids, detail="They disagree."):
        return {"conflicts": [{"detail": detail, "evidence": list(ids)}]}

    def test_only_declared_pairs_survive_in_either_order(self):
        result = g.check(self.conflict("E2", "E1"), EVIDENCE, conflicts=[["E1", "E2"]])
        self.assertEqual(result.accepted["conflicts"], [{"detail": "They disagree.", "evidence": ["E1", "E2"]}])
        other = g.check(self.conflict("E1", "E3"), EVIDENCE, conflicts=[["E1", "E2"]])
        self.assertEqual(reasons(other), [("conflicts", 0, g.UNSUPPORTED_CONFLICT)])
        self.assertEqual(other.missed_conflicts, [["E1", "E2"]])

    def test_without_declared_pairs_every_conflict_is_rejected(self):
        result = g.check(self.conflict("E1", "E2"), EVIDENCE)
        self.assertEqual(reasons(result), [("conflicts", 0, g.UNSUPPORTED_CONFLICT)])

    def test_repeated_ids_count_once(self):
        result = g.check(self.conflict("E1", "E1", "E2"), EVIDENCE, conflicts=[["E1", "E2"]])
        self.assertTrue(result.ok)
        self.assertEqual(result.accepted["conflicts"][0]["evidence"], ["E1", "E2"])
        self.assertEqual(result.missed_conflicts, [])

    def test_a_conflict_needs_exactly_two_known_ids(self):
        self.assertEqual(reasons(g.check(self.conflict("E1"), EVIDENCE, conflicts=[["E1", "E2"]])),
                         [("conflicts", 0, g.CONFLICT_NEEDS_TWO_IDS)])
        self.assertEqual(reasons(g.check(self.conflict("E1", "E2", "E3"), EVIDENCE, conflicts=[["E1", "E2"]])),
                         [("conflicts", 0, g.CONFLICT_NEEDS_TWO_IDS)])
        self.assertEqual(reasons(g.check(self.conflict("E1", "E7"), EVIDENCE, conflicts=[["E1", "E2"]])),
                         [("conflicts", 0, g.UNKNOWN_EVIDENCE)])
        self.assertEqual(reasons(g.check(self.conflict("E1", "E2", detail=" "), EVIDENCE, conflicts=[["E1", "E2"]])),
                         [("conflicts", 0, g.EMPTY_TEXT)])

    def test_declared_pairs_must_name_two_supplied_ids(self):
        for bad in (["E1"], ["E1", "E1"], ["E1", "E9"], "E1E2", ["E1", "E2", "E3"]):
            with self.subTest(rule=bad), self.assertRaises(ValueError):
                g.check({}, EVIDENCE, conflicts=[bad])


class CommandLine(unittest.TestCase):
    def run_cli(self, draft, *args):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "draft.json"
            path.write_text(json.dumps(draft), encoding="utf-8")
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = g.main([str(path), *args])
        return code, out.getvalue(), err.getvalue()

    def test_exit_codes(self):
        good = {"findings": [{"text": "t", "citations": ["E1"]}]}
        code, out, _ = self.run_cli(good, "--evidence", "E1", "E2")
        self.assertEqual(code, g.EXIT_OK)
        self.assertTrue(json.loads(out)["ok"])

        code, out, _ = self.run_cli({"conflicts": [{"detail": "d", "evidence": ["E1", "E2"]}]}, "--evidence", "E1", "E2")
        self.assertEqual(code, g.EXIT_REJECTED)
        code, out, _ = self.run_cli({"conflicts": [{"detail": "d", "evidence": ["E1", "E2"]}]},
                                    "--evidence", "E1", "E2", "--conflict", "E1,E2")
        self.assertEqual(code, g.EXIT_OK)

        code, _, err = self.run_cli(good, "--evidence", "E1", "--conflict", "E1,E9")
        self.assertEqual(code, g.EXIT_USAGE)
        self.assertIn("not supplied", err)


@unittest.skipUnless((CAMPUS / "mvp" / "live_model.py").is_file(), "Campus Evidence Desk sources not present")
class CampusCompatibility(unittest.TestCase):
    """Same accept/reject decisions as the Campus Evidence Desk gate on its 25 recorded drafts."""

    LIMITS = {"findings": 8, "actions": 6, "conflicts": 4}

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(CAMPUS / "mvp"))
        try:
            from engine import load_cases
            from live_model import normalize_synthesis
        finally:
            sys.path.remove(str(CAMPUS / "mvp"))
        cls.normalize_synthesis = staticmethod(normalize_synthesis)
        cls.cases = {case["id"]: case for case in load_cases()}
        cls.fixtures = json.loads((CAMPUS / "public_demo" / "parity" / "gate_fixtures.json").read_text(encoding="utf-8"))

    def test_same_items_accepted_on_every_recorded_draft(self):
        self.assertEqual(len(self.fixtures), 25)
        for fixture in self.fixtures:
            case = self.cases[fixture["case_id"]]
            with self.subTest(fixture=fixture["name"], case=case["id"]):
                campus = self.normalize_synthesis(case, fixture["payload"])
                ours = g.check(fixture["payload"], case["evidence"], conflicts=case.get("expected_conflicts"),
                               limits=self.LIMITS).accepted
                for section, ids_key in (("findings", "citations"), ("actions", "citations"), ("conflicts", "evidence")):
                    self.assertEqual([sorted(set(row[ids_key])) for row in ours[section]],
                                     [sorted(set(row[ids_key])) for row in campus[section]], section)
                    if fixture["name"] not in {"unicode_whitespace", "emoji_and_control"}:
                        text_key = "detail" if section == "conflicts" else "text"
                        self.assertEqual([row[text_key] for row in ours[section]],
                                         [row[text_key] for row in campus[section]], section)

    def test_rows_the_campus_gate_ignored_are_reported_here(self):
        by_name = {(f["name"], f["case_id"]): f for f in self.fixtures}
        limits = by_name[("limits", "research-access")]
        result = g.check(limits["payload"], self.cases["research-access"]["evidence"], limits=self.LIMITS)
        self.assertEqual([r["reason"] for r in result.rejected], [g.OVER_LIMIT] * 4)
        malformed = by_name[("scenario:malformed", "policy-conflict")]
        result = g.check(malformed["payload"], self.cases["policy-conflict"]["evidence"], limits=self.LIMITS)
        self.assertIn(("actions", 0, g.NOT_A_LIST), reasons(result))


if __name__ == "__main__":
    unittest.main()
