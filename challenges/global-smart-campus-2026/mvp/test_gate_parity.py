"""The browser demo (public_demo/public/gate.js) is a port of this engine.

public_demo/parity/gate_expected.json records what the Python reference returns for
every demo scenario and edge case; public_demo/test/gate.test.js holds the browser
port to the same file. If this test fails after an intentional engine change,
regenerate with `node parity/export_fixtures.js && python parity/generate_expected.py`
from public_demo/ and update gate.js until both suites pass.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from engine import analyze_case, load_cases
from live_model import normalize_synthesis

PARITY = Path(__file__).resolve().parents[1] / "public_demo" / "parity"


class BrowserGateParityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cases = {case["id"]: case for case in load_cases()}
        self.fixtures = json.loads((PARITY / "gate_fixtures.json").read_text(encoding="utf-8"))
        self.expected = json.loads((PARITY / "gate_expected.json").read_text(encoding="utf-8"))

    def test_reports_match_recorded_parity_file(self) -> None:
        for case_id, case in self.cases.items():
            with self.subTest(case=case_id):
                self.assertEqual(analyze_case(case), self.expected["reports"][case_id])

    def test_acceptance_layer_matches_recorded_parity_file(self) -> None:
        self.assertEqual(len(self.fixtures), len(self.expected["normalized"]))
        for fixture, want in zip(self.fixtures, self.expected["normalized"]):
            with self.subTest(fixture=fixture["name"], case=fixture["case_id"]):
                result = normalize_synthesis(self.cases[fixture["case_id"]], fixture["payload"])
                self.assertEqual(result, want["result"])


if __name__ == "__main__":
    unittest.main()
