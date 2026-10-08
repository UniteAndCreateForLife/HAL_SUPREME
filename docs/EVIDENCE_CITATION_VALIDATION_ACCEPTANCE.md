# Evidence & Citation Validation Harness — Acceptance Contract

This document defines the bounded acceptance contract for HAL SUPREME's **Evidence & Citation Validation Harness** service.

The service evaluates whether material claims are supported by the evidence attached to them. It does not certify that a source is universally true, replace domain experts, or claim formal compliance assurance.

## Scope

One bounded claim-producing workflow is selected before work begins. The review records:

- the claim types that matter;
- the evidence sources permitted for those claims;
- what counts as sufficient support;
- how conflicts and uncertainty are represented;
- what the system must reject;
- what machine-readable receipt proves the decision.

The starter engagement is not a general fact-check of an entire organization or knowledge base.

## Evidence contract

For each material claim class, define:

- claim identifier or canonical representation;
- source/evidence identifier;
- source timestamp or version where material;
- support relation: supported, unsupported, conflicting, or unresolved;
- minimum evidence required;
- freshness rule where applicable;
- privacy/egress restrictions;
- human-review requirement, if any.

A citation alone is not sufficient. The cited material must actually support the claim being made.

## Required failure cases

The focused evaluation set should include realistic cases such as:

1. citation exists but does not entail the claim;
2. source is missing or inaccessible;
3. source is stale relative to the claim;
4. two sources materially conflict;
5. model adds a stronger conclusion than the evidence supports;
6. execution/result claim is made without an observed receipt;
7. evidence belongs to the wrong tenant/account/resource;
8. private or disallowed evidence is proposed for public output.

## Decision states

Keep these outcomes explicit:

- **supported** — evidence meets the contract;
- **unsupported** — required support is absent;
- **conflicting** — material evidence disagrees;
- **unresolved** — available evidence is insufficient to decide;
- **rejected** — policy or privacy rules prohibit using the evidence/output.

Do not collapse conflicting or unresolved evidence into a confident answer.

## Machine receipt

For each evaluated material claim, a receipt should contain enough non-secret structure to reproduce the decision:

- claim ID;
- evidence/source IDs;
- rule/version used;
- decision;
- reason code;
- validator/test result;
- timestamp/version where useful;
- explicit limitations.

Receipts must exclude credentials, OTPs, tax/bank/identity data, hidden prompts, private client content, and secret-bearing URLs.

## Acceptance criteria

The bounded engagement is complete when the client receives:

- written evidence contract;
- claim/evidence schema;
- focused supported/unsupported/conflict test set;
- unsupported-claim rejection behavior;
- uncertainty/conflict handling rules;
- machine-readable receipt format;
- reproducible validation/evaluation cases;
- known limitations and unresolved questions.

Where practical, at least one intentionally broken example should fail before the final rules are applied.

## Public-safe evidence

Relevant HAL examples include:

- [Campus Evidence Desk](../challenges/global-smart-campus-2026/)
- [Revenue Truth Control Plane](../case-studies/REVENUE_TRUTH_CONTROL_PLANE_2026-09-24.md)
- [Claude Code + HAL MCP Fabric](../case-studies/CLAUDE_HAL_MCP_FABRIC_2026-09-24.md)
- [Agent Reliability Audit acceptance contract](AGENT_RELIABILITY_AUDIT_ACCEPTANCE.md)
- [MCP / Connector Evaluation Rubric](MCP_CONNECTOR_EVALUATION_RUBRIC.md)

## Commercial boundary

Current pricing and engagement terms are maintained in [Work With HAL](WORK_WITH_HAL.md). This document defines the engineering deliverable, not a warranty, certification, or external production-deployment claim.
