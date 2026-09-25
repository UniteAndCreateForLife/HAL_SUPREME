import unittest
from services.revenue_os import (
    EvidenceGateProjection, MoneyState, Opportunity, PayoutType,
    ProviderRouter, RevenueRecord, Route, WorkState, build_receipt, score, verify_receipt,
)


class RevenueScoringTests(unittest.TestCase):
    def test_contract_beats_equal_competition(self):
        common = dict(
            id="x", title="x", source="test", url="https://example.com", payout_amount=1500,
            eligibility_verified=True, submission_route_verified=True, payout_route_verified=True,
            contention=2, fit=5, hal_reuse=5, effort_hours=20, evidence_quality=4,
        )
        contract = Opportunity(**common, payout_type=PayoutType.CONTRACT)
        contest = Opportunity(**common, payout_type=PayoutType.COMPETITIVE)
        self.assertGreater(score(contract).total, score(contest).total)

    def test_unverified_submission_route_is_penalized(self):
        verified = Opportunity(
            id="a", title="a", source="test", url="x", payout_amount=500,
            payout_type=PayoutType.FIXED, eligibility_verified=True,
            submission_route_verified=True, payout_route_verified=True,
        )
        unverified = Opportunity(id="b", title="b", source="test", url="x", payout_amount=500, payout_type=PayoutType.FIXED)
        self.assertGreater(score(verified).total, score(unverified).total)


class EvidenceGateTests(unittest.TestCase):
    def test_submission_ready_requires_independent_evidence(self):
        gate = EvidenceGateProjection(state=WorkState.REVIEWING)
        ok, missing = gate.can_transition(WorkState.SUBMISSION_READY)
        self.assertFalse(ok)
        self.assertIn("tested_sha_verified", missing)
        for item in ("independent_review_pass", "security_review_pass", "tested_sha_verified", "evidence_receipt"):
            gate.mark(item)
        self.assertTrue(gate.can_transition(WorkState.SUBMISSION_READY)[0])


class ProviderRouterTests(unittest.TestCase):
    def test_router_rejects_not_ready_route(self):
        router = ProviderRouter([
            Route("remote", "great", "coder", benchmark_score=99, latency_seconds=1, zero_spend_ready=False),
            Route("local", "fallback", "coder", benchmark_score=60, latency_seconds=2, cost_class="local"),
        ])
        self.assertEqual(router.choose("coder").model, "fallback")

    def test_circuit_breaker_falls_back(self):
        bad = Route("free", "bad", "coder", benchmark_score=99, latency_seconds=1)
        for _ in range(3):
            bad.breaker.failure()
        router = ProviderRouter([bad, Route("local", "fallback", "coder", benchmark_score=50, latency_seconds=2)])
        self.assertEqual(router.choose("coder").model, "fallback")


class ReceiptAndMoneyTests(unittest.TestCase):
    def test_receipt_detects_tamper(self):
        receipt = build_receipt(kind="test", source_sha="abc", evidence={"tests": 7})
        self.assertTrue(verify_receipt(receipt))
        receipt["evidence"]["tests"] = 8
        self.assertFalse(verify_receipt(receipt))

    def test_paid_requires_receipt(self):
        rec = RevenueRecord("x", 100)
        with self.assertRaises(ValueError):
            rec.mark_paid(100, "")
        rec.mark_paid(100, "receipt://payment/1")
        self.assertEqual(rec.state, MoneyState.PAID)
        self.assertEqual(rec.paid_amount, 100)


if __name__ == "__main__":
    unittest.main()
