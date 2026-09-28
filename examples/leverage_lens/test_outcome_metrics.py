import unittest

from examples.leverage_lens.outcome_metrics import (
    AUTHORITY,
    OutcomeMetricsError,
    summarize_outcomes,
)


def row(run_id, **overrides):
    base = {
        "id": run_id,
        "accepted": True,
        "verification_passed": True,
        "session_visibility_loss": False,
        "reusable_artifact": True,
        "external_outcome": False,
        "attempts": 1,
        "human_interventions": 0,
        "duration_s": 60,
    }
    base.update(overrides)
    return base


class OutcomeMetricsTests(unittest.TestCase):
    def test_empty_sample_is_explicit(self):
        result = summarize_outcomes([])
        self.assertEqual(result["sample_size"], 0)
        self.assertEqual(result["metrics"], {})

    def test_core_rates_and_means(self):
        result = summarize_outcomes(
            [
                row("a", attempts=1, duration_s=60),
                row(
                    "b",
                    accepted=False,
                    verification_passed=False,
                    session_visibility_loss=True,
                    reusable_artifact=False,
                    attempts=3,
                    human_interventions=2,
                    duration_s=180,
                ),
            ]
        )
        self.assertEqual(result["authority"], AUTHORITY)
        self.assertEqual(result["metrics"]["accepted_rate"], 0.5)
        self.assertEqual(result["metrics"]["verification_pass_rate"], 0.5)
        self.assertEqual(result["metrics"]["session_visibility_loss_rate"], 0.5)
        self.assertEqual(result["metrics"]["mean_attempts_per_accepted"], 1.0)

    def test_false_success_is_visible(self):
        result = summarize_outcomes(
            [row("bad", accepted=True, verification_passed=False)]
        )
        self.assertEqual(result["metrics"]["false_success_count"], 1)

    def test_duplicate_ids_fail_closed(self):
        with self.assertRaises(OutcomeMetricsError):
            summarize_outcomes([row("x"), row("x")])

    def test_invalid_types_fail_closed(self):
        with self.assertRaises(OutcomeMetricsError):
            summarize_outcomes([row("x", attempts=-1)])
        with self.assertRaises(OutcomeMetricsError):
            summarize_outcomes([row("x", accepted="yes")])

    def test_failed_only_sample_does_not_invent_accepted_means(self):
        result = summarize_outcomes([row("x", accepted=False)])
        self.assertIsNone(result["metrics"]["mean_attempts_per_accepted"])
        self.assertIsNone(
            result["metrics"]["mean_human_interventions_per_accepted"]
        )


if __name__ == "__main__":
    unittest.main()
