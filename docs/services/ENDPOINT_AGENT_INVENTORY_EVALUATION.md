# Endpoint Agent Inventory Evaluation

This public-safe HAL SUPREME method supports the existing **Private / Local AI Architecture Review** and **Agent Reliability Audit** offers.

It is intended for read-only agent/MCP inventory products and local-first architecture reviews. It is not a penetration test, compliance certification, or customer-production claim.

## Evidence states

configured -> authorized -> attempted -> observed -> validated -> reported

## Bounded evaluation

Use one explicitly selected host or sandbox and synthetic/non-sensitive test material.

1. Inventory installed or configured agent surfaces that the scanner claims to detect, including supported MCP servers, agent runtimes, local models, and skill/configuration surfaces.
2. Compare the product inventory against an independent HAL-prepared inventory for the same host.
3. Record missing, duplicate, stale, or ambiguous entries rather than normalizing them away.
4. Verify reported capability boundaries such as shell access, filesystem scope, network egress, and tool exposure using public-safe metadata only.
5. Make one controlled configuration change and confirm the next scan reflects the new state.
6. Remove or revoke one test capability and confirm the reported state changes accordingly.
7. Verify the product does not claim access to content or secrets that were not actually observed.
8. Preserve machine-readable receipts so another reviewer can reproduce the comparison.

## Minimal regression pack

A useful first pass is 5-10 cases:

- known-present agent runtime;
- known-absent runtime;
- known-present MCP server;
- intentionally stale configuration entry;
- changed tool/capability declaration;
- removed capability;
- ambiguous or unsupported detector case;
- one local-model entry if supported;
- one explicit unknown case.

## Receipt fields

At minimum record:

- case_id
- host_or_sandbox_id
- detector_version
- expected_state
- observed_state
- source_or_manifest
- scan_timestamp
- validation_result
- notes

## Acceptance

A finding is not accepted merely because a scanner emitted it. HAL treats a finding as validated only when the observed evidence supports it and the result can be reproduced independently.

## Claim boundary

This method documents engineering evaluation of inventory/evidence behavior on a bounded environment. It does not establish fleet-wide coverage, breach detection, regulatory compliance, or third-party production deployment.
