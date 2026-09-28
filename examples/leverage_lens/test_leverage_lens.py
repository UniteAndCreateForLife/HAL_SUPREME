import unittest

from examples.leverage_lens.leverage_lens import (
    AUTHORITY,
    LeverageInputError,
    build_projection,
    rank_tasks,
    score_task,
    select_focus,
)


def task(task_id, **overrides):
    base = {
        "id": task_id,
        "title": task_id,
        "impact": 3,
        "unblock": 3,
        "compounding": 3,
        "strategy_alignment": 3,
        "proof": 3,
        "monetization": 2,
        "reuse": 3,
        "urgency": 2,
        "effort": 3,
        "risk": 2,
        "evidence": ["receipt"],
        "strategy_refs": ["canonical-strategy"],
    }
    base.update(overrides)
    return base


class LeverageLensTests(unittest.TestCase):
    def test_unblock_and_compounding_beat_shiny_feature(self):
        infrastructure = task("infra", impact=5, unblock=5, compounding=5, reuse=5, effort=3)
        feature = task("feature", impact=4, unblock=1, compounding=1, reuse=1, monetization=4, effort=2)
        ranked = rank_tasks([feature, infrastructure])
        self.assertEqual(ranked[0]["id"], "infra")

    def test_human_blocked_task_cannot_be_now(self):
        result = score_task(task("blocked", impact=5, unblock=5, compounding=5, human_blocked=True))
        self.assertEqual(result["priority_band"], "BLOCKED")
        self.assertTrue(result["blocked"])

    def test_dependency_blocked_task_cannot_be_now(self):
        result = score_task(task("dep", impact=5, dependency_ready=False))
        self.assertEqual(result["priority_band"], "BLOCKED")

    def test_missing_evidence_caps_proof(self):
        result = score_task(task("proof", proof=5, evidence=[]))
        self.assertEqual(result["effective_ratings"]["proof"], 2)
        self.assertTrue(any("proof capped" in item for item in result["caps"]))

    def test_missing_strategy_reference_caps_alignment(self):
        result = score_task(task("strategy", strategy_alignment=5, strategy_refs=[]))
        self.assertEqual(result["effective_ratings"]["strategy_alignment"], 2)

    def test_effort_and_risk_reduce_score(self):
        low = score_task(task("low", effort=1, risk=0))
        high = score_task(task("high", effort=5, risk=5))
        self.assertGreater(low["leverage_score"], high["leverage_score"])

    def test_missing_optional_inputs_are_conservative(self):
        result = score_task({"id": "minimal"})
        self.assertLess(result["leverage_score"], 20)
        self.assertEqual(result["priority_band"], "LATER")

    def test_invalid_rating_fails_closed(self):
        with self.assertRaises(LeverageInputError):
            score_task(task("bad", impact=6))

    def test_ties_are_stable_by_id(self):
        ranked = rank_tasks([task("b"), task("a")])
        self.assertEqual([row["id"] for row in ranked], ["a", "b"])

    def test_input_is_not_mutated(self):
        original = task("immutable", evidence=[])
        before = dict(original)
        score_task(original)
        self.assertEqual(original, before)

    def test_projection_is_explicitly_derived(self):
        projection = build_projection([task("x")])
        self.assertEqual(projection["authority"], AUTHORITY)
        self.assertEqual(projection["schema"], "hal.leverage_lens.v1")

    def test_focus_set_enforces_wip_limit(self):
        focus = select_focus([task("a"), task("b"), task("c"), task("d")], wip_limit=2)
        self.assertEqual(len(focus["focus"]), 2)
        self.assertEqual(len(focus["deferred"]), 2)
        self.assertTrue(focus["over_capacity"])

    def test_blocked_items_never_consume_focus_capacity(self):
        focus = select_focus(
            [task("blocked", human_blocked=True, impact=5), task("ready")],
            wip_limit=1,
        )
        self.assertEqual([row["id"] for row in focus["focus"]], ["ready"])
        self.assertEqual([row["id"] for row in focus["blocked"]], ["blocked"])

    def test_focus_selection_is_deterministic(self):
        one = select_focus([task("b"), task("a"), task("c")], wip_limit=2)
        two = select_focus([task("c"), task("b"), task("a")], wip_limit=2)
        self.assertEqual(
            [row["id"] for row in one["focus"]],
            [row["id"] for row in two["focus"]],
        )

    def test_invalid_wip_limit_fails_closed(self):
        with self.assertRaises(LeverageInputError):
            select_focus([task("a")], wip_limit=0)


if __name__ == "__main__":
    unittest.main()
