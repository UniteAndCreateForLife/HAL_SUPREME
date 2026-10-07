# Agent Task Startup Acceptance

This checklist supports HAL SUPREME's existing **Agent Reliability Audit** and **Private / Local AI Architecture Review** offers. It is not a new service.

## Goal

Prove that an accepted work request became a real, durable, controllable task before reporting that execution has started.

## Evidence sequence

request accepted -> task ID allocated -> state persisted -> executor provisioned -> execution started -> task discoverable -> result validated -> terminal state recorded

## Minimum acceptance contract

1. Every accepted work request receives one canonical task identifier.
2. Request acceptance, task registration, executor provisioning, and execution start are separate states.
3. Startup has a bounded timeout and an explicit failed or blocked state.
4. A UI must not show a healthy running task when task registration or executor startup failed.
5. Durable tasks remain discoverable after client refresh or restart when persistence is part of the product contract.
6. Task listing and direct task reads reconcile to the same canonical identity and ownership rules.
7. Running work has an explicit control path for status and cancellation.
8. External effects are attributed to the canonical task and validated before success is reported.
9. Client retries do not create duplicate tasks when the first request may already have been accepted.
10. Recovery after restart reconciles queued, running, cancelled, failed, and completed work instead of silently hiding or duplicating it.
11. Receipts distinguish request ID, task ID, worker/executor ID, startup stage, terminal reason, and downstream validation where practical.
12. Regression tests cover registration failure, executor-start failure, restart during startup, cancellation during startup, missing task metadata, and duplicate retries.

## Public HAL evidence

- [HAL public portfolio](../../PORTFOLIO.md)
- [Revenue Truth Control Plane](../../case-studies/REVENUE_TRUTH_CONTROL_PLANE_2026-09-24.md)
- [Claude Code + HAL MCP Fabric](../../case-studies/CLAUDE_HAL_MCP_FABRIC_2026-09-24.md)
- [MCP Tool Exposure Acceptance](MCP_TOOL_EXPOSURE_ACCEPTANCE.md)

## Claim boundary

HAL's public evidence is primarily self-operated engineering and reproducible public proof. This checklist is an acceptance/testing artifact, not a claim of third-party production ownership.
