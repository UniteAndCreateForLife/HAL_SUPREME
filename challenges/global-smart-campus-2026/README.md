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
- recommendations remain advisory and reversible;
- the human-review gate stays `PENDING_HUMAN_REVIEW` by default.

## Run locally

```powershell
cd challenges/global-smart-campus-2026/mvp
python -m unittest -v
python app.py
```

## Validation scope

The repository CI runs the deterministic acceptance tests on Linux x64, Linux arm64, Windows x64, and macOS arm64 without requiring provider credentials. Live NVIDIA NIM evidence is retained in `mvp/LIVE_VALIDATION_RECEIPT.json`; the public demo intentionally disables external model calls to prevent uncontrolled compute use.

Submission materials in this directory are sanitized and contain no portal password, API key, phone number, or legal-declaration acceptance.

Competition deadline: 5 October 2026. Final presentations: 27 October 2026.

## Reproducible deterministic benchmark

```powershell
cd challenges/global-smart-campus-2026/mvp
python benchmark_deterministic.py --iterations 10000
```

The committed `mvp/BENCHMARK_RECEIPT.json` records source hashes, latency percentiles, throughput, acceptance failures, and whether any external model or paid compute was used. The 2026-09-23 reference run processed 30,000 reports with zero acceptance-invariant failures.
