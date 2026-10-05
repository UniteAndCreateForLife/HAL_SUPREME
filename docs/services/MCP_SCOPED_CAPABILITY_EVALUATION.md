# MCP Scoped Capability Evaluation

A bounded HAL SUPREME evaluation method for MCP servers and agent-control layers that expose files, APIs, tools, or other external capabilities to AI agents.

This is an engineering evaluation method, not a compliance certification or penetration test.

## Evidence states

HAL separates:

```
configured -> authorized -> attempted -> observed -> validated -> reported
```

A configured tool is not automatically authorized. An authorized action is not proof that it was attempted. A successful tool response is not proof that the downstream result occurred. Reporting comes only after validation.

## Bounded evaluation scope

Choose one small capability surface and keep the authority map explicit.

A useful starter evaluation includes:

- one local-model or local-agent worker;
- one hosted-model worker;
- one read-only capability;
- one consequential/write capability when supported;
- one human approval boundary;
- one revocation path;
- one denied request;
- one transport/provider failure;
- one duplicate/retry case;
- one tenant, workspace, folder, or account-isolation check where the product has tenancy.

## Capability contract

For each tool or capability, record:

- tool name and schema;
- read/write/consequential risk class;
- required identity;
- granted scope;
- credential source and storage boundary;
- approval requirement;
- retry/idempotency behavior;
- timeout behavior;
- observable downstream effect;
- evidence available after execution.

Credentials and secrets are never part of the prompt/evaluation fixture.

## Core checks

### 1. Scope and negative access

Verify that a worker can access only the resources explicitly granted to it.

Include at least one negative test for an ungranted tenant, folder, namespace, account, or capability.

### 2. Approval binding

For consequential actions, approval should be tied to the exact operation and important arguments.

Changing the target, amount, recipient, path, or other material argument after approval should require a new decision.

### 3. Revocation

Revoke the capability or credential and repeat the previously successful request.

Acceptance requires fail-closed behavior and no stale cached payload that bypasses the new authority state.

### 4. Retry and duplicate safety

Inject a timeout or ambiguous result.

Check whether retry can duplicate an external effect. If the operation is not naturally idempotent, require an idempotency key, duplicate-suppression rule, or explicit human recovery path.

### 5. Failure routing

A governed tool failure must not silently cause the agent to route around the control boundary using a less-governed alternate tool.

Record the failure, permitted fallback behavior, and whether human intervention is required.

### 6. Outcome validation

Validate the external result independently where possible.

Examples:

- file exists at the expected path and version;
- API mutation is visible in a later read;
- message appears in the expected thread;
- record contains the intended value;
- receipt hash matches the evaluated request/result pair.

## Machine receipt

Each case should produce a small machine-readable receipt containing:

- case ID;
- capability/tool;
- actor/worker;
- configured scope;
- authorization decision;
- request fingerprint;
- attempt timestamp;
- observed tool result;
- downstream validation result;
- failure/retry path, if any;
- final pass/fail;
- evidence references.

## Regression pack

Keep 5–20 representative cases that can be replayed after:

- MCP/server upgrades;
- model/provider changes;
- policy changes;
- credential changes;
- agent-orchestrator updates.

The regression pack should include both successful and denied cases.

## Public claim boundary

A passing bounded evaluation means the tested cases satisfied their stated acceptance conditions in the tested environment.

It does not establish:

- regulatory compliance;
- general security certification;
- correctness for untested tools or tenants;
- customer production deployment;
- zero-risk operation.

## Related HAL evidence

- [HAL SUPREME Portfolio](../../PORTFOLIO.md)
- [Claude Code + HAL MCP Fabric](../case-studies/CLAUDE_HAL_MCP_FABRIC_2026-09-24.md)
- [Evaluation Pack & Regression Harness](./EVALUATION_PACK_REGRESSION_HARNESS.md)
