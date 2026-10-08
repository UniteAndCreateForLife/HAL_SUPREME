# MCP Interoperability Acceptance Checklist

This checklist turns an MCP integration into a client-observable acceptance contract.

## Discovery and schema
- Client completes initialization and discovers the intended tool.
- Nested objects and arrays remain usable as typed values.
- Required/optional fields and enums survive client consumption.
- Malformed or unknown arguments fail according to the declared contract.
- Validation errors do not leak raw dependency exceptions or secrets.

## Authority
Document read/write capability, resource scope, authentication boundary, human-approval requirements, and failure behavior. Unknown or ambiguous authority should fail closed. A dispatcher or gateway tool should not silently widen the permission identity a host grants.

## Runtime
Exercise the actual client/server path:
- one successful read;
- one write only when write testing is in scope;
- one malformed-input case;
- one expected service failure;
- retry, timeout, cancellation, and idempotency behavior where applicable.

## Evidence of execution
Keep these states distinct:
1. configured;
2. authorized;
3. attempted;
4. observed;
5. validated;
6. reported.

Reject a final success claim unless the required observed state is present.

## Client-observable acceptance
A schema can be valid in isolation and still fail in a real client. Require a round trip: discover -> construct arguments -> server accepts -> result returned -> client consumes result -> edge case behaves as specified.

## Regression quality
Preserve the original failure as a regression case. Where practical, reintroduce a representative defect to prove the test can fail. Record what actually ran.

## Public-safe receipt
Include versions or refs, non-secret schema digests, test commands, pass/fail counts, patch/test-output hashes, and explicit limitations. Exclude credentials, private account state, client data, and secret-bearing URLs.

## HAL evidence
- [Claude / HAL MCP Fabric](../case-studies/CLAUDE_HAL_MCP_FABRIC_2026-09-24.md)
- [Revenue Truth](../case-studies/REVENUE_TRUTH_CONTROL_PLANE_2026-09-24.md)
- [Portfolio](../PORTFOLIO.md)
