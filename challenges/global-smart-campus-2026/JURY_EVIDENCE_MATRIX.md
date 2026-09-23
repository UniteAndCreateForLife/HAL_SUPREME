# HAL Campus Evidence Desk — Jury Evidence Matrix

This matrix maps the official Global Smart Campus 2026 startup judging framework to evidence already demonstrated by the current MVP. It intentionally avoids unsupported customer, pilot, revenue, compliance, or deployment claims.

| Jury criterion | Weight | Current evidence | Demonstrated status | Next proof if shortlisted |
|---|---:|---|---|---|
| Problem relevance and user need | 20% | Campus staff must reconcile policies, requests, operational notes, research records, and security constraints while retaining traceability. Three synthetic cases exercise policy conflict, research access, and facilities-energy review. | Demonstrated through working scenarios and application packet. | Validate reviewer workflow with a bounded institutional or public-data pilot. |
| Innovation and differentiation | 20% | Evidence IDs and citations are first-class; live model output is subordinate to deterministic citation/conflict acceptance; unsupported conflict relations are rejected; recommendations cannot self-approve. | Implemented in MVP. | Compare review quality/time against a conventional chatbot baseline. |
| Feasibility and product readiness | 20% | Functional local MVP; public Cloudflare safety-mode demo; 8/8 regression tests; 3/3 canonical cases; Linux + Windows CI passed; bounded live NVIDIA NIM validation completed; deterministic acceptance benchmark processed 30,000 reports with zero invariant failures. | Working and reproducible. | Add SSO/RBAC, tenant isolation, audit export, retention controls, and one approved connector. |
| Impact and scalability | 20% | One provenance contract can support policy, research, IT/security, facilities, and sustainability workflows; provider-agnostic inference and modular evidence connectors avoid single-provider lock-in. Deterministic processing sustained 5,051.74 reports/second on the local benchmark host, showing the non-model acceptance layer is not a throughput bottleneck at MVP scale. | Architecture and synthetic throughput demonstrated; institutional impact not yet claimed. | Measure review-time reduction, citation validity, false-conflict rate, and reviewer usability in pilot. |
| Technology, security and responsible use | 10% | Synthetic public data only; deterministic acceptance; mandatory PENDING_HUMAN_REVIEW gate; public external inference disabled; CSP/XFO/nosniff/referrer/permissions headers; non-read API methods rejected. | Verified on deployed demo. | Add institution-approved identity, authorization, retention and audit controls before real data. |
| Presentation and jury response | 10% | Public demo, proposal PDF, pitch PDF, recorded demo, public sanitized source, validation receipts and reproducible judge-evidence endpoint. | Submission package ready apart from applicant-controlled portal facts and declaration. | Use live scenario walkthrough plus architecture/safety Q&A. |

## Reproducible acceptance facts

- Local regression: **8/8 passed**.
- Canonical synthetic cases: **3/3 passed**.
- Citation validity in canonical deterministic cases: **100%**.
- Unsupported material claims accepted: **0**.
- Live validation: **3/3 cases completed without provider error**; all accepted items evidence-grounded; live conflict relations matched seeded truth.
- Live validation token budget: **1,409 total tokens**.
- Human review state: **PENDING_HUMAN_REVIEW**.
- Deterministic benchmark: **30,000 reports**, **0 acceptance invariant failures**, **5,051.74 reports/second**, p95 **0.2728 ms/report** on Windows 11 / Python 3.12.10.
- Benchmark provenance: `mvp/BENCHMARK_RECEIPT.json` records source SHA-256 values for `engine.py` and `cases.json`; benchmark used **0 external model calls** and **no paid compute**.
- Public demo: https://hal-campus-evidence-desk.therealjakobhedrich.workers.dev
- Public source: https://github.com/UniteAndCreateForLife/HAL_SUPREME/tree/main/challenges/global-smart-campus-2026

## Explicit non-claims

No university customer, institutional pilot, campus-product revenue, FERPA certification, security certification, learning-outcome result, or high-impact automated decision capability is claimed. The MVP deliberately excludes admissions, grading, employment, disciplinary, medical, and other high-impact individual decisions.
