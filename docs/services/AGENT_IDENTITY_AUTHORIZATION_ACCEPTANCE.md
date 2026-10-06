# Agent Identity & Authorization Acceptance

This checklist supports HAL SUPREME's existing **Agent Reliability Audit**, **MCP / Tool Integration**, **Evidence & Citation Validation Harness**, and **Private / Local AI Architecture Review** offers.

It is for systems where an AI agent authenticates to an application using OIDC, an agent-specific identity provider, or a provider-issued mailbox/account. It does **not** treat authentication as authorization and does not imply third-party production deployment.

## Core boundary

Keep these separate:

1. **Agent identity** — which agent signed in.
2. **Human owner identity** — which human or organization is accountable for the agent.
3. **Application account** — the tenant/workspace the agent belongs to.
4. **Tool authority** — what the agent may read or change.
5. **Approval authority** — which consequential actions require a fresh human decision.
6. **Business truth** — the authoritative downstream state after an action.

A successful OIDC sign-in proves identity according to the issuer's contract. It does not prove that a later write was authorized, executed once, or completed downstream.

## Minimum acceptance set

### Identity continuity
- Prefer an issuer-scoped stable subject identifier for account linkage rather than mutable display names or email addresses.
- Record how agent email/address changes affect the application account.
- Verify that two agents owned by the same human remain distinct agent principals.
- Verify that ownership metadata cannot silently merge independent agents.

### Owner attribution
- Record whether owner identity is mandatory, optional, or scope-gated.
- Treat owner claims as attribution unless the application explicitly defines a separate authorization policy.
- Do not infer approval for high-risk actions from owner attribution alone.

### Session and revocation
- Revoke one agent and verify the effect on new sign-ins.
- Verify the documented behavior for existing sessions and refresh tokens.
- Record revocation latency and whether the application has any back-channel or polling mechanism.
- Confirm that revoking one agent does not revoke unrelated agents owned by the same human unless policy says so.

### Tool authorization
- Map each agent-visible tool to an explicit read/write scope.
- Default consequential writes to deny or approval-required.
- Bind an approval to the exact action, target, parameters, requester, correlation ID, and freshness window.
- Re-check authorization after retry, reconnect, or model-worker replacement.

### Credential placement
- Keep client secrets, API keys, refresh tokens, session cookies, and mailbox credentials outside prompts and model-visible logs.
- Never expose an inbox credential merely because an agent's email address is visible.
- Verify that downstream applications receive only the OIDC claims/scopes they requested.

### Non-browser and automation flows
- Document whether browser OIDC, device authorization, token exchange, service credentials, or another supported flow is used.
- Do not invent a headless workaround that bypasses provider policy.
- For MCP/CLI runtimes, prove that the supported flow still binds the resulting principal to the same agent identity and owner relationship.

### Failure and retry behavior
- Test expired tokens, revoked sessions, issuer mismatch, missing owner claims, and insufficient scopes.
- Test duplicate/replayed requests separately from authentication.
- If an external action returns an ambiguous result, inspect authoritative downstream state before retrying.

### Provider/model replacement
- Swap the model worker while keeping the same trusted identity/authorization layer.
- Verify that the new worker does not gain broader scopes, credentials, or durable memory access.
- Record any model-specific session state as transient implementation detail, not canonical identity.

## Evidence contract

```text
configured
-> authenticated
-> authorized
-> attempted
-> observed
-> downstream-validated
-> reported
```

For each consequential action, preserve:
- issuer and stable subject identifier;
- agent/account correlation ID;
- owner-attribution status;
- requested scopes/capabilities;
- approval receipt when required;
- tool/API result;
- independent downstream validation result;
- retry/duplicate disposition;
- untested boundaries.

## Public HAL evidence

- [HAL SUPREME public engineering portfolio](../../PORTFOLIO.md)
- [Claude Code + HAL MCP Fabric](../../case-studies/CLAUDE_HAL_MCP_FABRIC_2026-09-24.md)
- [MCP scoped-capability evaluation](MCP_SCOPED_CAPABILITY_EVALUATION.md)
- [Evaluation pack / regression harness](EVALUATION_PACK_REGRESSION_HARNESS.md)
- [Secure agent mentoring checklist](SECURE_AGENT_MENTORING_CHECKLIST.md)
- [Work With HAL](../WORK_WITH_HAL.md)

## Claim boundary

HAL's strongest public evidence is self-operated engineering work. This checklist does not claim production deployment for a third-party customer, identity-provider certification, regulatory compliance, or that authentication alone makes an autonomous action safe.
