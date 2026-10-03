# Boring AI Partner Evaluation — HAL SUPREME

Date: 2026-10-02

Sources:
- https://boringaico.com/partners
- https://boringaico.com/
- https://boringaico.com/trust

Boring AI's current founding-partner program is aimed at automation consultants, agencies, and freelancers. Its public product materials emphasize supervised agents, approval before irreversible actions, reviewable run traces, scoped tool access, remote MCP/OpenAPI integration, BYOK model choice, and founding-partner credits while public pricing is not yet live.

## HAL service fit

- Agent Reliability Audit: failure map, retries, uncertain-write handling, regression checks, receipts.
- MCP / Tool Integration: bounded schemas, auth boundary, read/write separation, approval gates.
- Evidence & Citation Validation Harness: explicit completion evidence and unsupported-success rejection.
- Private / Local AI Architecture Review: provider/egress mapping, BYOK boundaries, failure behavior, portability notes.

## Proposed synthetic proof

1. One non-sensitive trigger starts a supervised run.
2. One approved source is read.
3. One bounded tool is called.
4. One consequential action requires human approval.
5. One induced failure produces an observable failure state.
6. A repeated run does not create duplicate external effects.
7. Final completion is supported by a machine-readable receipt.

## Questions before commitment

- Can public open-source HAL evidence qualify for founding-partner access?
- Can the initial proof run entirely on founding-partner credits?
- Are there client-volume, insurance, certification, incorporation, or revenue requirements?
- What reference rights are expected?
- What commercial terms apply after public pricing launches?

## Claim boundary

This document is an evaluation plan only. It does not claim active Boring AI partner status, a customer production deployment, a signed commercial agreement, or a paid engagement.
