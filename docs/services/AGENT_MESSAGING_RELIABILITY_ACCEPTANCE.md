# Agent Messaging Reliability Acceptance

This is a reusable acceptance standard for HAL SUPREME work involving MCP/A2A-style agent messaging. It supports the existing **Agent Reliability Audit** and **MCP / Tool Integration** offers; it is not a new service category.

## Scope

Use synthetic or public-safe data unless a client explicitly authorizes otherwise.

A bounded evaluation should exercise:

1. one local-model worker and one hosted-model worker;
2. direct message delivery with a correlation ID;
3. one channel/group message;
4. observable delivery/read state where the transport exposes it;
5. temporary receiver unavailability;
6. a duplicate logical request;
7. worker/model replacement while preserving agent identity;
8. credential or authorization revocation;
9. independent recipient-side validation.

## Evidence contract

configured -> authorized -> attempted -> observed -> validated -> reported

An agent's own statement that a message was delivered or acted on is not sufficient evidence for a consequential result.

## Reliability checks

- Preserve a stable correlation/request ID where supported.
- Distinguish transport retry from business-level idempotency.
- Do not treat an automatic retry as exactly-once execution.
- Record ordering guarantees only when the transport actually exposes them.
- After ambiguous delivery, inspect recipient/downstream state before replaying a side effect.
- Verify that replacing a model worker does not silently expand authority.
- Verify that revocation closes the old worker's access on the next governed request.
- Keep message content, credentials and private data out of public receipts.

## Minimum regression set

- successful direct message;
- successful group/channel message;
- receiver temporarily unavailable;
- duplicate logical request;
- revoked credential;
- unauthorized target;
- malformed envelope/payload;
- model-worker replacement;
- ambiguous transport result followed by downstream validation.

## Review output

A completed review should include:

- bounded messaging/tool contract;
- identity and credential boundary;
- retry/idempotency behavior;
- failure map;
- reproducible regression cases;
- validation receipts;
- provider-neutral operating notes;
- open risks and next actions.

## Public HAL evidence

- https://github.com/UniteAndCreateForLife/HAL_SUPREME/blob/main/PORTFOLIO.md
- https://github.com/UniteAndCreateForLife/HAL_SUPREME/blob/main/case-studies/CLAUDE_HAL_MCP_FABRIC_2026-09-24.md
- https://github.com/UniteAndCreateForLife/HAL_SUPREME/blob/main/docs/services/MCP_SCOPED_CAPABILITY_EVALUATION.md
- https://github.com/UniteAndCreateForLife/HAL_SUPREME/blob/main/docs/services/EVALUATION_PACK_REGRESSION_HARNESS.md

## Claim boundary

HAL's strongest public evidence is self-operated engineering work. This checklist does not imply third-party customer production deployment, exactly-once delivery, security certification, or regulatory compliance.
