import copy
import json
import unittest
from pathlib import Path

from scripts.validate_mcp_conformance import REQUIRED_IDS, validate_record


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "mcp_conformance" / "livepeer_creative_public.json"


class McpProviderConformanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_public_fixture_is_valid(self):
        self.assertEqual([], validate_record(self.record))

    def test_fixture_contains_every_required_control_once(self):
        ids = [control["id"] for control in self.record["controls"]]
        self.assertEqual(REQUIRED_IDS, set(ids))
        self.assertEqual(len(ids), len(set(ids)))

    def test_verified_or_documented_controls_require_evidence(self):
        mutated = copy.deepcopy(self.record)
        target = next(
            control for control in mutated["controls"]
            if control["state"] in {"verified", "documented"}
        )
        target["evidence"] = []
        errors = validate_record(mutated)
        self.assertTrue(
            any("requires public evidence" in error for error in errors),
            errors,
        )

    def test_missing_control_fails_closed(self):
        mutated = copy.deepcopy(self.record)
        mutated["controls"] = [
            control for control in mutated["controls"] if control["id"] != "H5"
        ]
        errors = validate_record(mutated)
        self.assertTrue(any("missing controls" in error for error in errors), errors)

    def test_unknown_control_fails_closed(self):
        mutated = copy.deepcopy(self.record)
        mutated["controls"].append(
            {
                "id": "X1",
                "state": "not_observed",
                "finding": "Synthetic mutation used only by this test.",
                "evidence": [],
            }
        )
        errors = validate_record(mutated)
        self.assertTrue(any("unknown controls" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
