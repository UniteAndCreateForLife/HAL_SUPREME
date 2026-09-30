# Private / Local AI Architecture Review — Acceptance Checklist

This checklist defines the bounded deliverable for HAL SUPREME's Private / Local AI Architecture Review.

## Review boundary
Select one workflow and document:
- which model/tool steps run locally;
- which steps may use hosted providers;
- what data classes may leave the local boundary;
- where provider abstraction occurs;
- how the workflow behaves when the preferred route is unavailable;
- what an operator must verify before changing routes.

The starter review is architecture and validation work. It is not a formal certification or a full production migration.

## Routing acceptance
For each route, record:
- purpose;
- local or hosted execution;
- allowed data class;
- permitted provider/endpoint;
- expected fallback;
- operator approval when the fallback changes data exposure;
- observable evidence showing which route actually ran.

A fallback must not silently violate the original privacy or provider-independence requirement.

## Failure cases
Exercise or explicitly design for:
- local model unavailable;
- hosted provider unavailable;
- network unavailable;
- selected model cannot satisfy the requested task;
- fallback would change data exposure;
- model returns a plausible answer without completing the required tool action.

## Deliverables
The client receives:
- local/cloud routing map;
- privacy and egress policy;
- provider/model abstraction notes;
- failure and fallback behavior;
- validation checklist;
- operating runbook;
- prioritized implementation recommendations;
- explicit limitations.

## Public evidence
- [HAL public engineering portfolio](../PORTFOLIO.md)
- [Claude Code + HAL MCP Fabric](../case-studies/CLAUDE_HAL_MCP_FABRIC_2026-09-24.md)
- [Agent Reliability Audit acceptance contract](AGENT_RELIABILITY_AUDIT_ACCEPTANCE.md)
- [MCP Interoperability Acceptance Checklist](MCP_INTEROPERABILITY_ACCEPTANCE.md)

Current pricing and engagement terms are maintained in [Work With HAL](WORK_WITH_HAL.md).
