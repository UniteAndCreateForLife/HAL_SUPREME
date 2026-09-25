from __future__ import annotations

import unittest
from unittest.mock import patch

from services.twilio_searchlight_demo.prewarm import run_prewarm


class TwilioPrewarmTests(unittest.TestCase):
    def test_prewarm_uses_long_local_budget_without_changing_webhook_default(
        self,
    ) -> None:
        with patch(
            "services.twilio_searchlight_demo.prewarm.call_operator_conversation",
            return_value={
                "reply": "READY",
                "decision_id": "op_prewarm_1",
                "model": "qwen2.5:7b",
            },
        ) as call:
            result = run_prewarm(
                "http://127.0.0.1:8766/operator/commands",
                45.0,
                "6b76a9926c29c36a537873486e1a2b3d8dfe988c",
            )

        self.assertTrue(result["ready"])
        self.assertEqual(result["decision_id"], "op_prewarm_1")
        self.assertEqual(result["model"], "qwen2.5:7b")
        self.assertEqual(
            result["scope"],
            "local canonical HAL prewarm only; not a live Twilio interaction",
        )
        call.assert_called_once_with(
            "http://127.0.0.1:8766/operator/commands",
            "HAL_SEARCHLIGHT_LOCAL_PREWARM",
            "Return a short readiness acknowledgement.",
            45.0,
            160,
            max_wait_seconds=45.0,
        )

    def test_prewarm_rejects_unbound_source_sha(self) -> None:
        with self.assertRaisesRegex(ValueError, "source SHA"):
            run_prewarm("http://127.0.0.1:8766/operator/commands", source_sha="abc")


if __name__ == "__main__":
    unittest.main()
