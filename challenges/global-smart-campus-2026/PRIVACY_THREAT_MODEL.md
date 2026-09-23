# HAL Campus Evidence Desk — Privacy Threat Model

## Scope

This competition MVP is intentionally bounded to synthetic/public test evidence. The threat model focuses on preventing accidental disclosure when future campus evidence is connected to external model providers.

## Trust boundaries

1. **Local evidence boundary** — raw campus records, uploaded evidence, and deterministic validation should remain inside the operator-controlled environment unless explicitly approved for external processing.
2. **External model boundary** — hosted inference is treated as a separate trust domain. Evidence is not eligible for egress merely because an API credential is configured.
3. **Public demo boundary** — the Cloudflare-hosted public demo is safety-mode only and does not invoke live external inference.
4. **Human decision boundary** — model output is advisory. The final review state remains `PENDING_HUMAN_REVIEW` until an authorized human acts.

## Egress control

Before a case can be sent to NVIDIA NIM, `live_model.py` now performs a fail-closed direct-identifier scan over the question and evidence text. The initial detector blocks common email addresses, US Social Security numbers, phone numbers, and explicitly labeled student/employee/person/user identifiers.

The detector returns only identifier **categories and locations**, never the matched secret or personal value. A positive match raises `LiveModelError` before API-key lookup or network request construction, so blocked content does not cross the external-model boundary.

This is a defense-in-depth gate, not a claim of complete de-identification. Institution-specific identifiers, free-form names, addresses, biometrics, health information, and other sensitive classes require local policy-aware preprocessing before production deployment.

## Grounding and decision controls

The existing deterministic acceptance layer remains authoritative after any permitted model call:

- findings and actions without supplied evidence IDs are rejected;
- invalid citations are rejected;
- unsupported conflict relations are rejected;
- source evidence is not mutated by model output;
- recommendations remain reversible and advisory;
- a human-review gate is mandatory.

## Verification

The unit suite includes adversarial privacy cases proving that:

- the three canonical synthetic demo cases pass the privacy gate;
- email and phone identifiers are detected without echoing their values;
- SSNs and explicitly labeled identifiers are blocked;
- blocked cases fail before external inference.

The public CI executes these checks on standard GitHub-hosted Linux x64, Linux ARM64, Windows x64, and macOS ARM64 runners.

## Production hardening still required

A production campus deployment should add institution-specific DLP rules, data-classification policy, tenant isolation, encryption/key management, retention controls, access logging, incident response, and a formal privacy/legal review appropriate to the institution and jurisdiction. This MVP does not claim FERPA, HIPAA, GDPR, or other regulatory certification.
