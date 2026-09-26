# HAL Campus Evidence Desk — Global Smart Campus 2026

Competition entry for the Global Smart Campus Technology Innovation Challenge 2026 startup stream.

## Public prototype

https://hal-campus-evidence-desk.therealjakobhedrich.workers.dev

The public page runs the deterministic acceptance layer in the browser. Visitors can pick or edit a
model draft (grounded, uncited, invented evidence ID, invented conflict, malformed) and see what the gate
accepts and rejects. `public_demo/public/gate.js` is a port of `mvp/engine.py` and `mvp/live_model.py`;
`public_demo/test/gate.test.js` and `mvp/test_gate_parity.py` hold both implementations to the same
recorded results for 25 drafts and edge cases (`public_demo/parity/`).

Public competition release and recorded demo:
https://github.com/UniteAndCreateForLife/HAL_SUPREME/releases/tag/gsc2026-demo-v1

## What it demonstrates

HAL Campus Evidence Desk is a bounded, evidence-grounded assistant for campus operations and research review. The included MVP uses synthetic data only.

Core controls:
- every material finding/action must cite supplied evidence IDs;
- seeded policy conflicts must be surfaced rather than silently resolved;
- live-model output is filtered by a deterministic acceptance layer;
- unsupported conflict relations are rejected;
- external hosted-model egress fails closed when common direct identifiers are detected;
- privacy-gate evidence records only identifier category/location, never the matched value;
- tenant-scoped authorization rejects cross-tenant actions and tenant-scope switching;
- tenant identifiers are explicitly bounded to 1–64 lowercase alphanumeric/hyphen characters with alphanumeric boundaries;
- role-based access restricts review closure to the `reviewer` role in the reference workflow;
- per-report audit receipts are SHA-256 bound to canonical report content;
- review events are chained by SHA-256 so mutation, deletion/reordering, broken linkage, invalid receipts, or unauthorized close-role changes fail verification;
- recommendations remain advisory and reversible;
- the human-review gate stays `PENDING_HUMAN_REVIEW` by default.

See [`PRIVACY_THREAT_MODEL.md`](PRIVACY_THREAT_MODEL.md) for trust boundaries, the current direct-identifier egress gate, tenant authorization boundary, explicit limitations, and production-hardening requirements.

## Run locally

```powershell
cd challenges/global-smart-campus-2026/mvp
python -m unittest -v
python app.py
```

## Validation scope

The current unit suite contains **33 tests** covering deterministic grounding, privacy egress, audit integrity, role authorization, tenant isolation, tenant-ID boundary validation, and parity with the browser gate; the browser gate has 6 more tests under `node --test`. The repository CI runs the acceptance workflow on Linux x64, Linux ARM64, Windows x64, and macOS ARM64. Live NVIDIA NIM evidence is retained in `mvp/LIVE_VALIDATION_RECEIPT.json`; the public demo intentionally disables external model calls to prevent uncontrolled compute use.

Submission materials in this directory are sanitized and contain no portal password, API key, phone number, or legal-declaration acceptance.

Competition deadline: 5 October 2026. Final presentations: 27 October 2026.

## Tamper-evident review audit chain

`mvp/audit_chain.py` links each privacy-minimized review event to the prior event hash and the existing canonical report receipt. Audit events retain only the tenant scope, case identifier, report hash, role, event type, bounded note, sequence, and chain hashes; reviewer identity and evidence text are deliberately excluded. The verifier rejects mutated events, broken ordering/linkage, unsupported roles/event types, invalid report receipts, cross-tenant actions, tenant-scope changes, and analyst/auditor attempts to close a review.

## Reproducible deterministic benchmark

```powershell
cd challenges/global-smart-campus-2026/mvp
python benchmark_deterministic.py --iterations 10000
```

The committed `mvp/BENCHMARK_RECEIPT.json` records source hashes, latency percentiles, throughput, acceptance failures, and whether any external model or paid compute was used. The 2026-09-23 reference run processed 30,000 reports with zero acceptance-invariant failures.

## One-command judge verification

```powershell
cd challenges/global-smart-campus-2026
python judge_verify.py --output JUDGE_VERIFICATION_RECEIPT.json
```

The verifier is standard-library-only. It checks required submission artifacts and prior validation receipts, reruns deterministic unit/benchmark gates, validates the public Worker syntax when Node.js is present, records source hashes, and fails closed if any acceptance invariant is broken. It does not call an external model, use real student/employee data, or require paid compute.

## Security non-claims

The tenant/RBAC layer is an application-level competition reference control. It is not a substitute for institutional SSO, authoritative role mapping, storage/query-level tenant partitioning, key management, or a formal security/privacy review. The MVP does not claim FERPA, HIPAA, GDPR, SOC 2, ISO 27001, or other regulatory/security certification.
