# Secure Agent Mentoring Checklist

This checklist is a public-safe delivery companion for HAL SUPREME's existing **Agent Reliability Audit**, **MCP / Tool Contract Review**, **Evidence Contract Audit**, and **Private / Local AI Architecture Review**. It is not a new service tier and does not imply third-party production deployment.

## Goal

Help an operator learn to build and maintain a local-first or hybrid AI agent without making the model the owner of credentials, durable memory, permissions, or external business state.

## Session sequence

### 1. Authority and state
- identify the trusted control plane;
- separate transient model context from durable task/memory state;
- inventory credentials, tools, read/write capabilities, and approval boundaries;
- define which state survives model/provider replacement.

### 2. Tool contracts
For each API/MCP tool, record:
- purpose and authoritative downstream system;
- input/output schema;
- authentication boundary;
- read/write side effects;
- retry/idempotency behavior;
- protected actions and required human approval;
- independent validation method.

### 3. Memory and privacy
- classify data before persistence;
- keep secrets and unnecessary private data out of durable memory;
- document cloud egress;
- distinguish user-approved durable memory from ephemeral conversation context;
- test export/deletion/rollback paths where supported.

### 4. Failure behavior
Exercise at least:
- malformed input;
- expired/insufficient authorization;
- provider timeout or 5xx;
- rate limiting/backpressure;
- duplicate/retry;
- ambiguous completion;
- revoked permission;
- model/provider replacement.

A model success message is not evidence that an external action completed.

### 5. Human approval
Approval should bind to:
- action type;
- target/resource;
- material parameters;
- requester/agent identity;
- approval/correlation ID;
- expiry/freshness.

A materially changed retry requires a new approval.

### 6. Evidence and observability
Use the evidence sequence:

`configured -> authorized -> attempted -> observed -> validated -> reported`

For consequential actions, record an independent downstream check. Keep credentials and private payloads out of logs and public receipts.

### 7. Provider replacement
Run the same bounded regression set with:
- the primary hosted model;
- one alternate hosted or local model.

Changing the model worker must not silently broaden authority or alter canonical memory ownership.

### 8. Handoff
The operator should leave with:
- architecture diagram;
- tool/authority matrix;
- 5–10 deterministic regression cases;
- failure/approval runbook;
- provider-replacement test;
- privacy/egress notes;
- known untested boundaries.

## Public HAL evidence

- [HAL public engineering portfolio](../../PORTFOLIO.md)
- [Claude Code + HAL MCP Fabric](../../case-studies/CLAUDE_HAL_MCP_FABRIC_2026-09-24.md)
- [Campus Evidence Desk](../../challenges/global-smart-campus-2026/)
- [Revenue Truth Control Plane](../../examples/revenue_truth/)
- [Work With HAL](../WORK_WITH_HAL.md)

## Claim boundary

HAL's strongest public evidence is self-operated engineering work. This checklist does not imply a customer production deployment, penetration test, compliance certification, or guaranteed security outcome.
