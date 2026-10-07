# MCP Tool Exposure Acceptance

This checklist supports HAL SUPREME's existing **MCP / Tool Integration** and **Agent Reliability Audit** offers. It is not a new service.

## Goal

Do not treat an MCP server as usable merely because transport initialization succeeded. A client should separately prove configuration, connection, protocol initialization, tool discovery, tool registration, model exposure, invocation, and downstream effect.

## Evidence sequence

configured -> authenticated -> initialized -> tools discovered -> tools registered -> model exposed -> invoked -> downstream validated -> reported

## Minimum acceptance contract

1. Configuration is parsed and the intended transport, endpoint, and authentication material are present.
2. initialize succeeds and the negotiated protocol version is recorded.
3. tools/list succeeds independently and returns the expected tool names and schemas.
4. The client records tool-registration success or a specific registration/schema failure after discovery.
5. A generic READY / connected state must not imply that discovered tools are callable.
6. The model-visible tool set is checked explicitly and compared with tools/list.
7. At least one read-only tool is invoked end to end before enabling consequential write tools.
8. Tool invocation results are distinguished from authoritative downstream state.
9. Authentication success, protocol readiness, schema registration, model exposure, invocation, and downstream validation have separate receipts.
10. If a server is initialized but tools are not exposed, the client reports that as a degraded/error state rather than a healthy state.
11. Regression tests cover zero tools, one valid tool, malformed schema, duplicate names, unsupported schema features, partial registration, and transport reconnect.
12. Streamable HTTP tests verify session handling and tool exposure after initialization, not only endpoint reachability.
13. Provider/model replacement must not silently change which MCP tools are authorized or visible.
14. Consequential tools remain gated by the same permission and human-approval rules after reconnect or tool re-registration.

## Diagnostic matrix

| Layer | Proof | Failure example |
|---|---|---|
| Config | parsed config | wrong URL/header |
| Transport | connection established | network/TLS failure |
| Protocol | initialize response | incompatible version |
| Discovery | tools/list output | endpoint returns no tools |
| Registration | schemas accepted | unsupported/invalid schema |
| Exposure | model sees tool definitions | ready server, zero callable tools |
| Invocation | tool call succeeds | tool dispatcher failure |
| Validation | external state confirmed | success text without state change |

## Public reference

OpenAI Codex issue #49758 documents a Streamable HTTP MCP case where the server reaches a reported ready state and independently returns 22 tools from tools/list, but those tools are not exposed to the model-visible callable tool set:

https://github.com/openai/codex/issues/49758

HAL source-reviewed the public report on 2026-10-07. No upstream fix, independent runtime reproduction, customer deployment, or protocol certification is claimed.

## Public HAL evidence

- [HAL public portfolio](../../PORTFOLIO.md)
- [Claude Code + HAL MCP Fabric case study](../../case-studies/CLAUDE_HAL_MCP_FABRIC_2026-09-24.md)
- [AI Patch Review Acceptance](AI_PATCH_REVIEW_ACCEPTANCE.md)

## Claim boundary

HAL's public evidence is primarily self-operated engineering and reproducible public proof. This checklist is an acceptance/testing artifact, not a claim of third-party production ownership.
