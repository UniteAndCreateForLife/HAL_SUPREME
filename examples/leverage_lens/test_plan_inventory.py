import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from examples.leverage_lens.plan_inventory import (
    AUTHORITY,
    PlanInventoryError,
    inspect_plan,
    scan_plans,
)


class PlanInventoryTests(unittest.TestCase):
    def test_extracts_plan_metadata(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "plan.md"
            path.write_text(
                "# Test Plan\n\n**Owner:** HAL\n**Status:** active\n**Canonical WorkGraph task:** task_123\n",
                encoding="utf-8",
            )
            item = inspect_plan(
                path, now=datetime.now(timezone.utc)
            )
            self.assertEqual(item["title"], "Test Plan")
            self.assertEqual(item["status"], "active")
            self.assertEqual(item["owner"], "HAL")
            self.assertEqual(item["workgraph"], "task_123")

    def test_scan_reports_wip_and_missing_links(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "a.md").write_text("# A\nStatus: active\n", encoding="utf-8")
            (root / "b.md").write_text("# B\n", encoding="utf-8")
            result = scan_plans(root, wip_limit=1, stale_days=9999)
            self.assertEqual(result["authority"], AUTHORITY)
            self.assertEqual(result["counts"]["plans"], 2)
            self.assertTrue(result["warnings"])
            self.assertEqual(result["counts"]["missing_status"], 1)
            self.assertEqual(result["counts"]["missing_workgraph_link"], 2)

    def test_stale_plan_is_reported_from_mtime(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "old.md"
            path.write_text("# Old\nStatus: active\n", encoding="utf-8")
            os.utime(path, (0, 0))
            now = datetime(2026, 9, 27, tzinfo=timezone.utc)
            result = scan_plans(root, stale_days=21, now=now)
            self.assertEqual(result["counts"]["stale"], 1)
            self.assertEqual(result["stale"], [path.as_posix()])
            self.assertFalse(result["policy"]["mtime_is_plan_age"])
            self.assertEqual(result["plans"][0]["age_basis"], "filesystem_mtime")

    def test_invalid_policy_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(PlanInventoryError):
                scan_plans(Path(td), wip_limit=0)
            with self.assertRaises(PlanInventoryError):
                scan_plans(Path(td), stale_days=-1)


if __name__ == "__main__":
    unittest.main()
