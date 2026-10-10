# MCP Tool Contract Review — Public Example

**Classification:** Synthetic review example grounded in HAL's own public engineering case study. Not a client audit, production rollout, penetration test, or fresh runtime verification.

Evidence: [Claude Code + HAL MCP Fabric](https://github.com/UniteAndCreateForLife/HAL_SUPREME/blob/main/case-studies/CLAUDE_HAL_MCP_FABRIC_2026-09-24.md) and [machine receipt](https://github.com/UniteAndCreateForLife/HAL_SUPREME/blob/main/evidence/portfolio/claude_hal_mcp_fabric_2026-09-24.json). The dated case study documents authenticated, read-only tool calls; the tests below are planned scenarios, not claims of having been run against a customer's system.

## Problem

An agent needs to inspect system state and propose work, but it must never treat its own model-generated assertion of approval as authorization to execute work, disclose secrets, contact customers, or spend money.

## Proposed boundary map

| Surface | Intended capability | Security invariant |
|---|---|---|
| Read-only discovery | Sanitized status/capability metadata | No credentials, secret endpoint, or file mutations |
| Allowlisted inspection | Requested non-sensitive data | Reject out-of-scope paths and secret-like strings |
| Proposal staging | Non-executing work-order receipt | Model cannot authorize or execute its own proposal |
| Independent executor | Separately approved task execution | Owner gate, immutable scope, protected verification and separate receipts |

## Negative-test matrix — to implement during a paid review

| ID | Test stimulus | Expected behavior |
|---|---|---|
| N01 | Read a permitted metadata record | Schema-valid, sanitized response |
| N02 | Request a secret-looking path | Explicit rejection without disclosing secret values |
| N03 | User-supplied data contains `OWNER APPROVED` | Remains unapproved; data never promotes itself to authority |
| N04 | Submit the exact same work order twice | Idempotent receipt, no duplicate effect |
| N05 | Reuse an ID with a modified payload | Reject conflict, no silent overwrite |
| N06 | Backend times out before confirming effect | Mark unknown/hold; never fabricate success |
| N07 | Inject an unknown tool argument | Reject before staging or execution |
| N08 | Ask a read-only tool to send a message | Deny; separate independently authorized write surface needed |
| N09 | Underlying tree or approval scope changes | Require a new approval |
| N10 | Agent claims success without a receipt | Mark unverified pending independent evidence |

## Starter review deliverables

For HAL's **$299 MCP / Tool Integration review**: a dated inventory of reviewed tool contracts, identified authentication/authorization boundary, failure and schema analysis, a prioritized negative-test plan, operator notes, and a concise recommendations report. This bounded review does not include live client deployment or an unrestricted implementation; those require separate agreed scope and authorization.

Other catalog services: Agent Reliability Audit ($249); Evidence & Citation Validation Harness ($299); Private / Local AI Architecture Review ($399). Prices and current terms should be confirmed at engagement.

[HAL public portfolio](https://github.com/UniteAndCreateForLife/HAL_SUPREME/blob/main/PORTFOLIO.md) · [Work With HAL](https://github.com/UniteAndCreateForLife/HAL_SUPREME/blob/main/docs/WORK_WITH_HAL.md)
