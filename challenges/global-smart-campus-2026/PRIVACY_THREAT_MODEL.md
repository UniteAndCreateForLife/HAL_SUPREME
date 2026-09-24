# HAL Campus Evidence Desk — Privacy Threat Model

## Scope

This competition MVP is intentionally bounded to synthetic/public test evidence. The threat model focuses on preventing accidental disclosure when future campus evidence is connected to external model providers, preserving tenant boundaries, and keeping model-assisted review subordinate to authorized human action.

## Trust boundaries

1. **Local evidence boundary** — raw campus records, uploaded evidence, and deterministic validation should remain inside the operator-controlled environment unless explicitly approved for external processing.
2. **External model boundary** — hosted inference is treated as a separate trust domain. Evidence is not eligible for egress merely because an API credential is configured.
3. **Tenant authorization boundary** — the reference access-control layer binds actions to a validated tenant ID and role. Cross-tenant access and tenant-scope switching fail closed before review events are appended.
4. **Public demo boundary** — the Cloudflare-hosted public demo is safety-mode only and does not invoke live external inference.
5. **Human decision boundary** — model output is advisory. The final review state remains `PENDING_HUMAN_REVIEW` until an authorized human acts; only the `reviewer` role may close a review in the reference workflow.

## Egress control

Before a case can be sent to NVIDIA NIM, `live_model.py` performs a fail-closed direct-identifier scan over the question and evidence text. The initial detector blocks common email addresses, US Social Security numbers, phone numbers, and explicitly labeled student/employee/person/user identifiers.

The detector returns only identifier **categories and locations**, never the matched secret or personal value. A positive match raises `LiveModelError` before API-key lookup or network request construction, so blocked content does not cross the external-model boundary.

This is a defense-in-depth gate, not a claim of complete de-identification. Institution-specific identifiers, free-form names, addresses, biometrics, health information, and other sensitive classes require local policy-aware preprocessing before production deployment.

## Tenant isolation and authorization controls

`mvp/access_control.py` validates non-secret tenant scopes and uses a fail-closed role/action matrix. `mvp/audit_chain.py` binds each review event to the same tenant scope as the chain and rejects cross-tenant writes, scope changes, unknown roles, unauthorized close actions, invalid report receipts, and malformed tenant identifiers.

The competition implementation demonstrates an application-layer tenant boundary, not production institutional identity assurance. Production deployment still requires institution-managed authentication/SSO, authoritative role mapping, storage- and query-level tenant partitioning, key separation where required, and security review of every connector.

## Grounding and decision controls

The deterministic acceptance layer remains authoritative after any permitted model call:

- findings and actions without supplied evidence IDs are rejected;
- invalid citations are rejected;
- unsupported conflict relations are rejected;
- source evidence is not mutated by model output;
- recommendations remain reversible and advisory;
- a human-review gate is mandatory.

## Audit integrity

Each deterministic report can be bound to a canonical SHA-256 receipt. Privacy-minimized review events are linked to that report receipt and to the prior event hash. Mutation, deletion/reordering, broken linkage, invalid receipts, tenant-boundary violations, and unauthorized close-role attempts fail verification.

Audit events intentionally exclude evidence text and reviewer identity in the competition reference implementation; they retain only the bounded fields needed to verify review state and chain integrity.

## Verification

The unit suite currently contains **22 tests** covering deterministic grounding, privacy egress, audit integrity, role authorization, and tenant isolation. Adversarial cases prove that:

- the three canonical synthetic demo cases pass the privacy gate;
- email and phone identifiers are detected without echoing their values;
- SSNs and explicitly labeled identifiers are blocked;
- blocked cases fail before external inference;
- cross-tenant review actions are rejected;
- an existing audit chain cannot switch tenant scope;
- malformed tenant identifiers are rejected;
- only an authorized reviewer can close a review;
- mutation and broken hash linkage fail audit verification.

The public CI executes the acceptance workflow on standard GitHub-hosted Linux x64, Linux ARM64, Windows x64, and macOS ARM64 runners.

## Production hardening still required

A production campus deployment should add institution-specific DLP and data-classification policy, institutional SSO and authoritative role mapping, storage/query-level tenant partitioning, encryption/key management, retention/deletion controls, comprehensive access logging, incident response, connector security review, backup/recovery controls, and a formal privacy/legal review appropriate to the institution and jurisdiction. This MVP does not claim FERPA, HIPAA, GDPR, SOC 2, ISO 27001, or other regulatory/security certification.
