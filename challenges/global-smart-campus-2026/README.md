# HAL Campus Evidence Desk — Global Smart Campus 2026

Competition entry for the Global Smart Campus Technology Innovation Challenge 2026 startup stream.

## Public prototype

https://hal-campus-evidence-desk.therealjakobhedrich.workers.dev

## What it demonstrates

HAL Campus Evidence Desk is a bounded, evidence-grounded assistant for campus operations and research review. The included MVP uses synthetic data only.

Core controls:
- every material finding/action must cite supplied evidence IDs;
- seeded policy conflicts must be surfaced rather than silently resolved;
- live-model output is filtered by a deterministic acceptance layer;
- unsupported conflict relations are rejected;
- external hosted-model egress fails closed when common direct identifiers are detected;
- privacy-gate evidence records only identifier category/location, never the matched value;
- recommendations remain advisory and reversible;
- the human-review gate stays `PENDING_HUMAN_REVIEW` by default.

See [`PRIVACY_THREAT_MODEL.md`](PRIVACY_THREAT_MODEL.md) for trust boundaries, the current direct-identifier egress gate, explicit limitations, and production-hardening requirements.

## Run locally

```powershell
cd challenges/global-smart-campus-2026/mvp
python -m unittest -v
python app.py
```

## Validation scope

The repository CI runs the deterministic acceptance and privacy-gate tests on Linux x64, Linux arm64, Windows x64, and macOS arm64. Live NVIDIA NIM evidence is retained in `mvp/LIVE_VALIDATION_RECEIPT.json`; the public demo intentionally disables external model calls to prevent uncontrolled compute use.

Submission materials in this directory are sanitized and contain no portal password, API key, phone number, or legal-declaration acceptance.

Competition deadline: 5 October 2026. Final presentations: 27 October 2026.

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
