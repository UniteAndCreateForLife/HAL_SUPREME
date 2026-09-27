from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.validate_public_portfolio import PORTFOLIO_PATH, REPO_ROOT, _iter_public_text_files, validate

OFFER_PAGES = ("docs/WORK_WITH_HAL.md", "docs/samples/code-health-check-sample.md")


class PublicPortfolioTests(unittest.TestCase):
    def test_offer_pages_are_scanned(self) -> None:
        scanned = {path.relative_to(REPO_ROOT).as_posix() for path in _iter_public_text_files()}
        for page in OFFER_PAGES:
            self.assertIn(page, scanned)

    def test_offer_page_changes_trigger_the_workflow(self) -> None:
        workflow = (REPO_ROOT / ".github" / "workflows" / "public-portfolio.yml").read_text(encoding="utf-8")
        for trigger in ('"docs/WORK_WITH_HAL.md"', '"docs/samples/**"'):
            self.assertEqual(workflow.count(trigger), 2, f"{trigger} must be in both push and pull_request paths")

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
