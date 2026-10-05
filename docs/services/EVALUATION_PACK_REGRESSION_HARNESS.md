# Evaluation Pack & Regression Harness

HAL SUPREME offers a bounded evaluation-harness implementation for AI agents and LLM workflows.

## Evidence model

`configured -> authorized -> attempted -> observed -> validated -> reported`

A model or tool saying "done" is not accepted as proof that the target outcome happened.

## Starter scope

For one bounded workflow:

- define the task contract and acceptance criteria;
- create 5–20 representative evaluation cases;
- record source evidence / ground truth for each case;
- define deterministic checks where possible;
- define rubric-based checks only where deterministic checks are insufficient;
- reject unsupported claims and malformed structured output;
- track retries, timeouts, duplicate execution, and provider/tool failures;
- record machine-readable receipts for each run;
- produce a regression set and a prioritized repair plan.

## Evaluation-pack pattern

Each pack can contain:

- data room / input bundle;
- task prompt;
- ground truth;
- scoring rubric;
- deterministic filters;
- model run output;
- score and pass/fail decision;
- evidence receipt.

Packs that fail quality filters are rebuilt or rejected rather than silently accepted.

## Public evidence

- [HAL SUPREME Portfolio](../../PORTFOLIO.md)
- [Claude Code + HAL MCP Fabric](../../case-studies/CLAUDE_HAL_MCP_FABRIC_2026-09-24.md)
- [Revenue Truth Control Plane](../../examples/revenue_truth/)
- [Campus Evidence Desk](../../challenges/global-smart-campus-2026/)

## Claim boundary

This offer is an engineering evaluation method. It does not imply third-party customer production deployment, domain certification, penetration testing, or guaranteed business outcomes.
