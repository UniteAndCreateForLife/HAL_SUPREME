---
name: agent-reliability-audit
description: Use this skill when auditing an AI agent, coding agent, or automated workflow for reproducibility, retries, idempotency, hallucinated success, missing validation, weak observability, or unsafe execution boundaries.
version: 0.1.0
---

# Agent Reliability Audit

Audit the system as an engineering process, not as a persuasive demo.

## Workflow

1. Define the observable success condition independently of model narration.
2. Reconstruct inputs, tools, permissions, environment, and expected outputs.
3. Identify failure classes: unsupported success claims; partial completion presented as completion; retry duplication; stale state; non-idempotent mutation; hidden provider failure; environment-sensitive behavior; missing regression coverage.
4. Reduce important failures to reproducible cases.
5. Separate read-only observations from write-shaped actions.
6. Require independent verification after each protected mutation.
7. Produce a failure map, regression set, observability plan, and explicit residual risks.

## Output contract

Return scope reviewed, evidence inspected, reproducible failures, severity and impact, deterministic acceptance criteria, recommended tests, retry/idempotency controls, observability gaps, unresolved risks, and claims that must not be made yet.

Never treat the agent's own statement that work succeeded as sufficient evidence.
