# Agent Reliability Audit — Acceptance Contract

This document defines the bounded acceptance contract for HAL SUPREME's **Agent Reliability Audit** service.

It is intentionally narrower than a production-readiness certification. The audit identifies reproducible failure modes, validates the evidence around them, and leaves a prioritized repair plan. It does not claim formal security assurance, compliance certification, or external customer production deployment.

## Scope

One bounded agent or workflow is selected before work begins. The audit records:

- the requested outcome and material constraints;
- the agent/tool boundaries involved;
- the canonical state that represents success;
- consequential writes and their human-approval gates;
- retry, timeout, cancellation, and idempotency behavior;
- evidence required before the workflow may report success.

The starter engagement is not a broad codebase audit. Additional workflows or implementation work are scoped separately.

## Failure map

The audit distinguishes at least these failure classes:

1. **Interpretation failure** — the system performs a nearby task rather than the requested task.
2. **Tool/contract failure** — the selected tool, schema, arguments, auth boundary, or provider contract is wrong.
3. **Execution failure** — configuration is correct but runtime execution fails or never occurs.
4. **State failure** — a partial or duplicate action leaves canonical state inconsistent.
5. **Evidence failure** — the system reports success without the required observed state.
6. **Recovery failure** — retries widen scope, duplicate side effects, or obscure the original error.
7. **Observability failure** — operators cannot distinguish configured, attempted, observed, validated, and reported states.
8. **Privacy/egress failure** — protected data crosses a boundary not approved for the workflow.

## Reproduction standard

A material finding should include enough evidence to reproduce the behavior from a pinned state where practical:

- repository/ref or deployed build identifier;
- relevant non-secret configuration;
- exact input or synthetic fixture;
- command/tool-call sequence;
- observed result;
- expected result;
- limitations and environment assumptions.

A source-backed hypothesis is not labeled as an executed reproduction.

## Evaluation set

The starter audit targets **5–10 focused cases** for the selected workflow. Cases should include the normal path plus failure conditions that are realistic for that system, such as:

- malformed or incomplete tool arguments;
- denied or stale permissions;
- timeout/service error;
- duplicate/replayed request;
- conflicting evidence;
- missing execution receipt;
- model claim of success after a blocked action.

Where safe and practical, at least one representative broken behavior should be reintroduced or simulated to prove the regression check can fail.

## Reliability controls reviewed

The audit checks whether the workflow needs or correctly implements:

- bounded retries with explicit stop conditions;
- idempotency keys or duplicate-action protection;
- schema/input validation at the correct boundary;
- human approval before consequential writes;
- canonical state transitions;
- evidence-backed completion criteria;
- fail-closed handling for ambiguous authority;
- structured logs/receipts that exclude secrets and private payloads.

## Evidence-of-execution model

HAL keeps these states distinct:

1. configured;
2. authorized;
3. attempted;
4. observed;
5. validated;
6. reported.

A final success statement is unsupported unless the workflow reaches the state required by its contract.

## Acceptance criteria

The audit is complete when the client receives:

- architecture/workflow and failure map;
- reproducible cases for the material findings;
- focused eval/regression set;
- retry/idempotency/validation review;
- evidence and hallucination-control review;
- observability gaps;
- prioritized repair plan;
- explicit limitations and unresolved questions.

If a finding could not be reproduced, the report must say so and label the supporting evidence accordingly.

## Public-safe receipt

For public examples, receipts may include:

- repository/ref and non-secret version data;
- pass/fail counts;
- hashes of patches or test outputs;
- CI links;
- synthetic fixtures;
- explicit limitations.

Public receipts must exclude credentials, OTPs, tax/bank/identity data, private client content, hidden prompts, secret-bearing URLs, and private account state.

## Relationship to other HAL services

Use **MCP / Tool Integration** when the primary problem is a tool/API/MCP contract.

Use **Evidence & Citation Validation Harness** when the primary problem is unsupported claims, citations, conflicts, or evidence rules.

Use **Private / Local AI Architecture Review** when the primary problem is privacy, egress, local/open models, provider abstraction, or offline/failure architecture.

The Agent Reliability Audit may recommend one of those follow-on slices, but it does not presume an implementation engagement.

## Public evidence

- [HAL public engineering portfolio](../PORTFOLIO.md)
- [Claude Code + HAL MCP Fabric](../case-studies/CLAUDE_HAL_MCP_FABRIC_2026-09-24.md)
- [Revenue Truth Control Plane](../case-studies/REVENUE_TRUTH_CONTROL_PLANE_2026-09-24.md)
- [Campus Evidence Desk](../challenges/global-smart-campus-2026/)
- [MCP interoperability acceptance checklist](MCP_INTEROPERABILITY_ACCEPTANCE.md)
- [MCP / Connector Evaluation Rubric](MCP_CONNECTOR_EVALUATION_RUBRIC.md)

## Commercial boundary

Current pricing and engagement terms are maintained in [Work With HAL](WORK_WITH_HAL.md). This acceptance contract describes the engineering deliverable, not a warranty or certification.
