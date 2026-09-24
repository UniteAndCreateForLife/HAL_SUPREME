from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.validate_public_portfolio import PORTFOLIO_PATH, validate


class PublicPortfolioTests(unittest.TestCase):
    def test_public_portfolio_passes_evidence_and_secret_gate(self) -> None:
        self.assertEqual(validate(), [])

    def test_portfolio_has_unique_evidence_backed_projects(self) -> None:
        payload = json.loads(PORTFOLIO_PATH.read_text(encoding="utf-8"))
        projects = payload["projects"]
        ids = [project["id"] for project in projects]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(len(projects), 2)
        for project in projects:
            self.assertTrue(project["evidence"])
            for relative in project["evidence"]:
                self.assertTrue(Path(PORTFOLIO_PATH.parents[1], relative).is_file())


if __name__ == "__main__":
    unittest.main()
