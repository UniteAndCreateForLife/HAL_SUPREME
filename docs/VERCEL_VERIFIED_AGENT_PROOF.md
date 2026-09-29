# Vercel Verified Agent Operator — Proof Slice

**Purpose:** produce one narrow, accelerator-ready Vercel demonstration that proves HAL's durable/evidence-bound agent contract on Vercel's current Agent Stack.

## User story

A developer submits a bounded engineering task. HAL creates a durable work order, chooses a model through Vercel AI Gateway, generates a proposed change, verifies it in Vercel Sandbox, pauses before any protected action, and returns an evidence receipt that distinguishes proposal, verification, approval, and completion.

## Proposed architecture

```text
Browser / API
    |
    v
Next.js task endpoint
    |
    v
WorkflowAgent / Vercel Workflow
    |----> AI Gateway ----> model A
    |                 \----> model B fallback
    |
    |----> Vercel Sandbox ----> isolated command/test execution
    |
    |----> Approval gate ----> human decision
    |
    v
Evidence receipt + run status + observability
```

## HAL invariants carried into the demo

1. Model output is a proposal, never completion evidence.
2. Canonical work state is durable and separate from any individual model session.
3. A protected action cannot execute without an explicit approval state.
4. Verification runs in an isolated execution surface.
5. Retry/resume must not duplicate a completed side effect.
6. Provider fallback must not weaken acceptance criteria.
7. Public receipts exclude secrets, credentials, private paths, prompt internals, and personal data.
8. A run cannot claim success unless its required verification evidence exists.

## Minimum vertical slice

### Input
- task ID;
- repository or synthetic workspace reference;
- bounded task description;
- allowed verification command;
- explicit protected-action policy.

### Agent phase
- call model through AI Gateway;
- record model/provider attribution exposed by supported telemetry;
- return structured proposal;
- if the provider fails, exercise configured fallback without changing task acceptance.

### Sandbox phase
- create ephemeral Vercel Sandbox;
- materialize only the bounded synthetic/example workspace;
- apply proposed change inside the sandbox;
- run the allowed verification command;
- capture exit status and sanitized output digest;
- destroy/expire the sandbox according to platform lifecycle.

### Workflow phase
- persist state between proposal, sandbox, and approval steps;
- inject one interruption and prove resume from the durable checkpoint;
- make side-effecting steps idempotent or uniquely keyed by work-order ID.

### Human approval phase
- request approval only after verification passes;
- reject or leave pending if approval is denied/absent;
- never represent `verified` as `approved`.

### Receipt phase
Emit JSON comparable to:

```json
{
  "work_order_id": "vo-...",
  "status": "verified_pending_approval",
  "model_route": {
    "gateway": "vercel-ai-gateway",
    "requested_model": "...",
    "provider": "...",
    "fallback_used": false
  },
  "sandbox": {
    "verified": true,
    "command": "npm test",
    "exit_code": 0,
    "output_sha256": "..."
  },
  "workflow": {
    "resumed_after_injected_interruption": true,
    "duplicate_side_effects": 0
  },
  "approval": {
    "required": true,
    "granted": false
  }
}
```

## Acceptance criteria

The proof is complete only when all of the following are demonstrated with captured receipts:

- one successful end-to-end run;
- one primary-model failure followed by valid AI Gateway fallback;
- one sandbox verification failure correctly blocking completion;
- one workflow interruption followed by correct resume;
- one protected action remaining pending until human approval;
- one denied approval that does not execute the protected action;
- no secret values or private local paths in logs/receipts;
- deterministic mapping from work-order ID to final receipt;
- a public demo page that clearly distinguishes requested, proposed, verified, approved, and completed states.

## Benchmark set

Use a synthetic/example repository only. Include at least:

1. small deterministic code repair;
2. failing-test repair;
3. malicious/instruction-smuggling task that attempts to obtain secrets or hidden context;
4. task that triggers provider fallback;
5. task that intentionally fails sandbox verification;
6. task that requires approval and is denied.

## Measurement

Capture:

- end-to-end latency;
- model/provider route;
- token/model cost when available;
- sandbox startup + verification latency;
- retries;
- resume count;
- approval wait state;
- final receipt status.

The benchmark should report counts and timings without claiming production reliability from a small sample.

## Implementation boundaries

- No production HAL secrets or local-machine state.
- No automatic GitHub merge, deployment, purchase, email, or account mutation in the public demo.
- No hidden prompt/session-context publication.
- No claim that Vercel Sandbox replaces HAL's entire local verification fabric.
- No multi-cloud rewrite. This is one Vercel-native execution adapter and product proof.

## Current Vercel primitives to target

- AI SDK 7 / `WorkflowAgent`
- Vercel AI Gateway
- Vercel Sandbox SDK
- Vercel Workflow SDK
- Vercel deployment previews / CI/CD
- Vercel Observability

Official references:
- https://vercel.com/ai-accelerator
- https://vercel.com/docs/ai-sdk
- https://vercel.com/docs/ai-gateway
- https://vercel.com/docs/sandbox
- https://vercel.com/workflows
- https://vercel.com/kb/guide/what-is-workflowagent

## Deliverables

- `examples/vercel-verified-agent/` source;
- focused tests;
- machine-readable example receipts;
- `case-studies/VERCEL_VERIFIED_AGENT_OPERATOR_2026.md`;
- short demo video;
- public deployment URL;
- updated portfolio entry only after the evidence exists.

## Promotion gate

Do not add the proof to `PORTFOLIO.md` as completed until the source, tests, deployment, and receipts are all real and reviewable.
