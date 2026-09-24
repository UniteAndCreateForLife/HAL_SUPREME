# HAL Campus Evidence Desk — Jury Evidence Matrix

This matrix maps the official Global Smart Campus 2026 startup judging framework to evidence already demonstrated by the current MVP. It intentionally avoids unsupported customer, pilot, revenue, compliance, or deployment claims.

| Jury criterion | Weight | Current evidence | Demonstrated status | Next proof if shortlisted |
|---|---:|---|---|---|
| Problem relevance and user need | 20% | Campus staff must reconcile policies, requests, operational notes, research records, and security constraints while retaining traceability. Three synthetic cases exercise policy conflict, research access, and facilities-energy review. | Demonstrated through working scenarios and application packet. | Validate reviewer workflow with a bounded institutional or public-data pilot. |
| Innovation and differentiation | 20% | Evidence IDs and citations are first-class; live model output is subordinate to deterministic citation/conflict acceptance; unsupported conflict relations are rejected; recommendations cannot self-approve. | Implemented in MVP. | Compare review quality/time against a conventional chatbot baseline. |
| Feasibility and product readiness | 20% | Functional local MVP; public Cloudflare safety-mode demo; 30-test regression suite after privacy, audit-chain, tenant-isolation, and tenant-ID-boundary hardening; 3 canonical cases; Linux x64 + Linux arm64 + Windows x64 + macOS arm64 CI; bounded live NVIDIA NIM validation; deterministic acceptance benchmark processed 30,000 reports with zero invariant failures. | Working and reproducible. | Add real SSO identity binding, retention controls, tenant provisioning, and one approved connector. |
| Impact and scalability | 20% | One provenance contract can support policy, research, IT/security, facilities, and sustainability workflows; provider-agnostic inference and modular evidence connectors avoid single-provider lock-in. Deterministic processing sustained 3,752.93 reports/second on the local benchmark host, showing the non-model acceptance layer is not a throughput bottleneck at MVP scale. | Architecture and synthetic throughput demonstrated; institutional impact not yet claimed. | Measure review-time reduction, citation validity, false-conflict rate, and reviewer usability in pilot. |
| Technology, security and responsible use | 10% | Synthetic public data only; deterministic acceptance; mandatory `PENDING_HUMAN_REVIEW`; public external inference disabled; CSP/XFO/nosniff/referrer/permissions headers; non-read API methods rejected; `/api/audit` emits deterministic SHA-256 receipts; hosted-model egress fails closed on common direct identifiers before API-key lookup/network request; review events are SHA-256 chained to the canonical report receipt; review-close operations require the `reviewer` role; review events are bound to a validated tenant scope and cross-tenant review actions fail closed; tenant identifiers are constrained to 1–64 lowercase alphanumeric/hyphen characters with alphanumeric boundaries. | Privacy gate, tamper-evident audit chain, role authorization, tenant-isolation controls, and tenant-ID boundary handling are implemented with adversarial regression cases; reviewer identity and evidence text are excluded from audit-chain events; production privacy threat model documented without compliance overclaim. | Add institution-approved DLP taxonomy, real SSO/RBAC identity binding, retention, tenant provisioning, key management, centralized audit export, and formal privacy/legal review before real data. |
| Presentation and jury response | 10% | Public demo, proposal PDF, pitch PDF, recorded demo, public sanitized source, validation receipts and reproducible judge-evidence endpoint. | Submission package ready apart from applicant-controlled portal facts and declaration. | Use live scenario walkthrough plus architecture/safety Q&A. |

## Reproducible acceptance facts

- Regression suite after privacy + audit-chain + tenant-isolation + tenant-ID-boundary hardening: **30 tests**; the branch is designed for the same four standard CI platforms used by the accepted workflow.
- Tenant isolation: `mvp/access_control.py` validates tenant scopes and fails closed on cross-tenant access; audit-chain tests reject cross-tenant review actions, tenant-scope switching, and malformed tenant identifiers. Dedicated access-control tests also verify 1-character, 2-character, and 64-character valid scopes; overlength, uppercase, slash-containing, and hyphen-bounded invalid scopes; unknown-role fail-closed behavior; and reviewer/auditor/analyst permission boundaries.
- Privacy egress gate: canonical synthetic cases pass; common email/phone/SSN/labeled identifiers are blocked before external inference; matched identifier values are not retained in gate evidence.
- Tamper-evident audit controls: `/api/audit?id=<case>` binds each deterministic report to a canonical SHA-256 receipt, while `mvp/audit_chain.py` links privacy-minimized review events to that receipt and the prior event hash; mutation, broken ordering/linkage, invalid receipts, unauthorized close-role attempts, and tenant-boundary violations fail verification.
- Canonical synthetic cases: **3/3 passed**.
- Citation validity in canonical deterministic cases: **100%**.
- Unsupported material claims accepted: **0**.
- Live validation: **3/3 cases completed without provider error**; all accepted items evidence-grounded; live conflict relations matched seeded truth.
- Live validation token budget: **1,409 total tokens**.
- Human review state: **PENDING_HUMAN_REVIEW**.
- Deterministic benchmark: **30,000 reports**, **0 acceptance invariant failures**, **3,752.93 reports/second**, p95 **0.3482 ms/report** on Windows 11 / Python 3.12.10.
- Benchmark provenance: `mvp/BENCHMARK_RECEIPT.json` records source SHA-256 values for `engine.py` and `cases.json`; benchmark used **0 external model calls** and **no paid compute**.
- One-command judge verifier: `python judge_verify.py --output JUDGE_VERIFICATION_RECEIPT.json`; local verdict `HAL_JUDGE_VERIFY_OK`, with the same verifier enforced by four-platform CI.
- Public demo: https://hal-campus-evidence-desk.therealjakobhedrich.workers.dev
- Public source: https://github.com/UniteAndCreateForLife/HAL_SUPREME/tree/main/challenges/global-smart-campus-2026
- Privacy model: `PRIVACY_THREAT_MODEL.md` documents trust boundaries, egress controls, explicit limits, and production hardening.

## Explicit non-claims

No university customer, institutional pilot, campus-product revenue, FERPA certification, HIPAA certification, GDPR certification, security certification, learning-outcome result, or high-impact automated decision capability is claimed. The tenant boundary is an MVP control, not production institutional identity federation or a completed multi-tenant security assessment. The MVP deliberately excludes admissions, grading, employment, disciplinary, medical, and other high-impact individual decisions.
