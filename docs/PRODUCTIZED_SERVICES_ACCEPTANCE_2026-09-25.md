# HAL SUPREME — Productized Service Acceptance Criteria

**Prepared:** September 25, 2026  
**Scope:** Public-safe, evidence-backed first milestones for commercial engineering work.

This document defines how HAL SUPREME scopes the four existing productized services described in the public repository. It intentionally does not claim customer production deployments or capabilities that are not supported by public evidence.

## Common first-milestone contract

A bounded first milestone should identify:

1. the exact workflow, failure mode, or integration boundary;
2. the systems, tools, data classes, and side effects in scope;
3. the authorization boundary, including any human approval gate;
4. the success and failure cases that will be reproduced;
5. the evidence and handoff artifacts that let another operator verify the result.

The preferred output is a reviewable artifact—not a vague consulting recommendation: a failure map, tested integration slice, evaluation harness, or architecture/runbook package.

## 1. Agent Reliability Audit

Use when an existing AI-agent workflow works but is unreliable, difficult to debug, unsafe to retry, or prone to unsupported outputs.

### Typical deliverables
- architecture and failure map;
- reproducible failure cases;
- compact evaluation/regression set;
- retry, idempotency, and validation review;
- evidence and hallucination controls;
- observability recommendations;
- prioritized repair plan.

### Acceptance criteria
- named failures are reproduced from known inputs;
- expected and observed behavior are recorded;
- retry and idempotency risks are classified;
- regression checks are rerunnable;
- unresolved risks are explicit rather than hidden behind a pass/fail summary.

### Example bounded milestone
Audit one agent workflow end to end, reproduce its three highest-impact failure modes, and leave a compact regression set plus a repair plan ranked by severity and implementation effort.

## 2. MCP / Tool Integration

Use when Claude, Codex, agents, or internal workflows need tool access without creating an unrestricted execution surface.

### Typical deliverables
- MCP or tool contract;
- authentication and authorization boundary;
- request/response schemas;
- timeout, retry, and failure semantics;
- deterministic integration tests;
- human approval gates for protected actions;
- provider-neutral operating notes.

### Acceptance criteria
- the exposed tool surface is enumerated;
- read-only, draft-only, approval-gated, and disallowed actions are explicit;
- representative success and failure paths are tested;
- ambiguous authority fails closed;
- protected writes cannot bypass the intended approval boundary.

## 3. Evidence & Citation Validation Harness

Use when an AI workflow must distinguish source evidence from model inference.

### Acceptance criteria
- supported and unsupported outputs are distinguishable by deterministic checks;
- citations resolve to the evidence used for each claim;
- missing or conflicting evidence produces an explicit uncertainty or failure state;
- evaluation cases are rerunnable;
- receipts preserve enough provenance to audit the decision path.

## 4. Private / Local AI Architecture Review

Use when a workflow needs local/open models, bounded cloud fallback, provider independence, or explicit privacy/egress controls.

### Acceptance criteria
- data classes and egress paths are explicit;
- routing decisions are reviewable;
- provider failure does not silently change privacy or authority behavior;
- degraded modes are defined;
- operator intervention and recovery paths are documented.

## Public evidence

- https://github.com/UniteAndCreateForLife/HAL_SUPREME/blob/main/PORTFOLIO.md
- https://github.com/UniteAndCreateForLife/HAL_SUPREME/tree/main/challenges/global-smart-campus-2026
- https://github.com/UniteAndCreateForLife/HAL_SUPREME/tree/main/examples/revenue_truth
- https://github.com/UniteAndCreateForLife/HAL_SUPREME/blob/main/case-studies/CLAUDE_HAL_MCP_FABRIC_2026-09-24.md

## Evidence and non-claims

These service definitions do **not** claim customer production deployment where none is public; universal experience across every framework; compliance certification; production RAG, PostgreSQL, React, or unrelated technologies unless independently evidenced; or guaranteed business, bounty, contract, grant, or investment outcomes.
