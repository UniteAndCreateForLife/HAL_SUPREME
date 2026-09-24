import unittest

from examples.revenue_truth.revenue_projection import build_revenue_projection, infer_stage


class RevenueProjectionTests(unittest.TestCase):
    def test_prepared_is_not_submitted(self):
        self.assertEqual(
            infer_stage({"status": "draft_current_head_green_not_finally_submitted"}),
            "prepared",
        )

    def test_claim_is_submitted_without_sponsor_acceptance(self):
        self.assertEqual(
            infer_stage({"status": "open_claimed_waiting_sponsor_selection"}),
            "submitted",
        )

    def test_merge_does_not_imply_award_or_payment(self):
        self.assertEqual(
            infer_stage({"status": "merged_no_verified_reward", "merged": True}),
            "merged_or_delivery_accepted",
        )

    def test_verified_cash_is_required_for_paid_projection(self):
        self.assertEqual(
            infer_stage({"status": "award_pending", "verified_cash_received_usd": 0}),
            "discovered",
        )
        self.assertEqual(
            infer_stage({"verified_cash_received_usd": 25}),
            "paid_and_reconciled",
        )

    def test_advertised_and_verified_money_stay_separate(self):
        result = build_revenue_projection(
            [],
            [
                {
                    "id": "contract",
                    "title": "Prepared contract",
                    "reward_usd": 6000,
                    "revenue_stage": "prepared",
                    "funding_status": "not verified",
                    "next_human_action": "Approve proposal spend",
                }
            ],
        )
        record = result["records"][0]
        self.assertEqual(record["advertised_value_usd"], 6000)
        self.assertEqual(record["verified_paid_usd"], 0)
        self.assertEqual(result["kpis"]["verified_paid_usd"], 0)
        self.assertEqual(result["columns"]["prepared"], ["contract"])
        self.assertEqual(result["columns"]["submitted"], [])

    def test_pool_status_is_not_recipient_payment(self):
        result = build_revenue_projection(
            [],
            [{"id": "bounty", "payment_status": "PAID", "reward_usd": 250}],
        )
        record = result["records"][0]
        self.assertEqual(
            record["funding_status"],
            "Bounty pool: PAID; recipient payment unverified",
        )
        self.assertEqual(record["verified_paid_usd"], 0)
        self.assertEqual(record["stage"], "discovered")


if __name__ == "__main__":
    unittest.main()
