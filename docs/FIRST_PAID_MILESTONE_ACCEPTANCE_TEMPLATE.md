# HAL SUPREME — First Paid Milestone Acceptance Template

Use this template to convert a client inquiry into a bounded, inspectable first engagement.

## Select one primary offer

- **Agent Reliability Audit** — failure map, reproducible cases, eval/regression set, retries/idempotency/validation, evidence and hallucination controls, observability plan.
- **MCP / Tool Integration Pilot** — bounded tool contract, auth/authority boundary, schema and failure handling, representative tests, human approval gates, provider-neutral operating notes.
- **Evidence & Citation Validation Harness** — evidence contract, citation checks, unsupported-claim rejection, uncertainty/conflict handling, machine-readable receipts, reproducible evals.
- **Private / Local AI Architecture Review** — local-first routing, privacy/egress policy, provider abstraction, failure behavior, validation checklist, and runbook.

Use a secondary offer only when it directly supports the same bounded objective.

## 1. Problem statement

**Client problem:** one concrete agent, tool, evidence-validation, or architecture problem.

**Observed failure / uncertainty:** state what is directly supported by evidence and what is not yet proven.

**First-milestone objective:** one independently inspectable end state.

## 2. Scope boundary

Included:
- one named workflow, tool boundary, evidence use case, or architecture slice;
- agreed synthetic, sandbox, public, or client-approved test data;
- agreed repositories/endpoints/documents;
- bounded regression/evaluation set;
- non-secret receipts and handoff notes.

Excluded unless explicitly added:
- production rollout;
- credential migration;
- broad application rebuilds;
- unrelated frontend/backend work;
- 24/7 operations;
- unbounded debugging across unrelated systems.

## 3. Evidence-state contract

Keep these states distinct:

1. configured;
2. authorized;
3. attempted;
4. observed;
5. validated;
6. reported.

A success message alone is not completion. The agreed post-condition must be independently observable.

## 4. Acceptance criteria

### Functional
- the named workflow reaches the agreed post-condition;
- representative success and failure cases are exercised;
- invalid or unauthorized actions fail closed;
- retries do not create duplicate consequential writes when idempotency is required.

### Reliability
- false-success behavior is tested when applicable;
- timeout, provider failure, stale state, and partial-completion behavior are documented when relevant;
- a deterministic or bounded evaluation method is supplied.

### Evidence
- claims map to artifacts, tests, sources, or receipts;
- unsupported claims remain marked unsupported;
- uncertainty and source conflicts are preserved.

### Handoff
- deliverables and limitations are documented;
- secrets are excluded from receipts;
- follow-on work is separated from first-milestone completion.

## 5. Completion receipt

Record:
- engagement identifier;
- service selected;
- scope version;
- tests/evals run;
- pass/fail/blocked results;
- assumptions;
- limitations;
- artifacts delivered;
- follow-on recommendations.

Never include credentials, OTPs, private client data, hidden prompts, or sensitive internal material.

## 6. Change control

If requested work expands:

1. record the requested change;
2. state its effect on acceptance criteria;
3. move it into a revised or new milestone;
4. do not silently absorb unrelated scope.

## 7. Commercial pattern

Prefer a small fixed-price diagnostic/audit milestone or a tightly bounded hourly milestone with a written hour cap before a larger implementation.

Published starting points:
- Agent Reliability Audit — starting at $600;
- MCP / Tool Integration Pilot — starting at $900;
- Evidence & Citation Validation Harness — starting at $800;
- Private / Local AI Architecture Review — starting at $600.

HAL SUPREME public evidence is self-operated unless a separate case study explicitly establishes an external deployment.
