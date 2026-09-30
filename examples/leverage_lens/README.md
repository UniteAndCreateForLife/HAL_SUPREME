# HAL Leverage Lens

A deterministic, read-only ranking projection for proposed HAL work.

It does **not** create tasks, release WorkGraph items, mutate canonical state, spend money, deploy, merge, or publish. Its output is explicitly `DERIVED_NON_AUTHORITATIVE`.

## Why it exists

HAL already has WorkGraph, acceptance receipts, revenue truth, provider health, and several lane-specific dashboards. The leverage lens adds one shared question before work starts:

> Which unblocked task most improves the whole system, with evidence, at acceptable effort and risk?

The lens intentionally rewards system impact, dependency unblocking, compounding value, strategy alignment, evidence, monetization, reuse, and urgency. Effort and risk reduce the score.

It also emits a bounded **focus set**. By default only the three highest-ranked unblocked items are placed in focus; remaining unblocked items are explicitly deferred, and blocked items are kept separate. This is a projection only: it does not pause, release, cancel, or mutate any WorkGraph task.

Unsupported confidence is capped:
- `proof > 2` requires evidence references.
- `strategy_alignment > 2` requires strategy references.
- Human- or dependency-blocked work is always labeled `BLOCKED`, regardless of score.

## Input

Ratings are 0-5. Effort is 1-5.

```json
[
  {
    "id": "session-lifecycle",
    "title": "Repair agent session lifecycle",
    "impact": 5,
    "unblock": 5,
    "compounding": 5,
    "strategy_alignment": 5,
    "proof": 4,
    "monetization": 3,
    "reuse": 5,
    "urgency": 4,
    "effort": 3,
    "risk": 3,
    "evidence": ["failing-job-receipt"],
    "strategy_refs": ["canonical-plan"],
    "acceptance": ["bounded reproduction", "focused tests", "global gate"]
  }
]
```

## Run

```bash
python -m examples.leverage_lens.leverage_lens tasks.json --wip-limit 3
python -m unittest -v examples.leverage_lens.test_leverage_lens
python -m py_compile examples/leverage_lens/leverage_lens.py
```

Use the score to structure a review, not to replace judgment. Keep multiple outcome metrics; do not turn the number itself into the goal.

## WIP rule

The focus set exists to resist plan proliferation. A high-scoring task can still remain deferred when the bounded WIP limit is full. Promotion into actual execution remains a human/WorkGraph decision.

## Active-plan inventory

Use `plan_inventory.py` to measure plan-document sprawl without editing anything:

```bash
python -m examples.leverage_lens.plan_inventory docs/exec-plans/active --wip-limit 5 --stale-days 21
```

It reports active-plan count, missing Status fields, missing WorkGraph linkage, age/staleness, and derived warnings. It never archives, renames, edits, or releases a plan/task.

## Outcome feedback

`outcome_metrics.py` closes the loop after work runs. It reports accepted rate, verification pass rate, session-visibility-loss rate, reusable-artifact rate, external-outcome rate, attempts/human-interventions/time per accepted run, and false-success count. The leverage score is an intake aid; these observed outcomes determine whether the system is actually improving.
