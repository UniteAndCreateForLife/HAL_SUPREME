# HAL SUPREME — Public Engineering Portfolio

**Maintainer:** [UniteAndCreateForLife](https://github.com/UniteAndCreateForLife)
**Updated:** 2026-09-24
**Focus:** durable AI systems, MCP integrations, multimodal production, evidence gates, privacy, and reproducible demos

HAL SUPREME is an engineering program for building AI-assisted systems that retain durable intent, use replaceable model and media workers, and promote work through evidence. This portfolio links every material claim to public source, tests, or a machine-readable receipt.

## Selected work

| Project | Observable result | Public evidence |
|---|---|---|
| **HAL Campus Evidence Desk** | Synthetic-data campus operations and research-review prototype with evidence citations, deterministic acceptance, privacy egress checks, tenant-scoped RBAC, and a tamper-evident review chain. The current public suite contains 30 tests. A committed benchmark processed 30,000 reports with zero acceptance-invariant failures and no paid compute. | [Project](challenges/global-smart-campus-2026/README.md) · [Judge receipt](challenges/global-smart-campus-2026/JUDGE_VERIFICATION_RECEIPT.json) · [Benchmark](challenges/global-smart-campus-2026/mvp/BENCHMARK_RECEIPT.json) · [Public demo](https://hal-campus-evidence-desk.therealjakobhedrich.workers.dev) |
| **Bounded Desktop Automation + Upwork MCP** | Added a durable GitHub-to-local fallback that runs only read-only diagnostics, keeps model output local, and posts sanitized status receipts. Two recurring Windows tasks completed with exit code zero. The revenue radar recovered from a transient connection reset and passed 111 tests. Claude Code and Codex completed OAuth to the official Upwork MCP, followed by one authenticated read-only tool proof with no account data published. | [Case study](case-studies/BOUNDED_DESKTOP_AUTOMATION_AND_UPWORK_MCP_2026-09-24.md) · [Machine receipt](evidence/portfolio/bounded_desktop_automation_upwork_mcp_2026-09-24.json) · [Public relay evidence](https://github.com/UniteAndCreateForLife/HAL_SUPREME/issues/35) |
| **Claude Code + HAL MCP Fabric** | Added Claude Code as an authenticated, replaceable HAL engineering worker without creating a second task or execution authority. Three project MCP servers connected; an authenticated proof called three read-only HAL tools and verified `ok: true` for every result. The surface contains 11 bounded bridge tools, 5 gateway tools, and a 125-method Livepeer catalog. | [Case study](case-studies/CLAUDE_HAL_MCP_FABRIC_2026-09-24.md) · [Machine receipt](evidence/portfolio/claude_hal_mcp_fabric_2026-09-24.json) |
| **ChatGPT + OpenCode + Livepeer Creative MCP** | Connected ChatGPT, OpenCode, and HAL’s media workflow to Livepeer as a replaceable creative worker. OpenCode 1.18.18 reported the remote server connected. A fresh read-only inventory of that server on 2026-09-24 found 125 MCP methods and 209 available capabilities: 175 AI capabilities and 34 production tools. Execution remains gated by explicit cost and action review. | [Case study](case-studies/LIVEPEER_CHATGPT_MCP_2026-09-24.md) · [Machine receipt](evidence/portfolio/livepeer_chatgpt_mcp_2026-09-24.json) · [Plugin source](plugins/livepeer-creative-mcp/) · [Client](integrations/livepeer_creative/client.py) · [Runbook](docs/LIVEPEER_CREATIVE_MCP.md) |
| **Revenue Truth Control Plane** | An eleven-stage revenue and payout projection that prevents prepared work, submissions, merges, awards, and payment from collapsing into one status. The public module keeps advertised and verified paid values separate, exposes human gates, and passes six focused invariants. | [Case study](case-studies/REVENUE_TRUTH_CONTROL_PLANE_2026-09-24.md) · [Machine receipt](evidence/portfolio/revenue_truth_control_plane_2026-09-24.json) · [Source and tests](examples/revenue_truth/) |
| **HAL public-interest engineering package** | A separate provenance-controlled Apache-2.0 repository with scope, budget, security, privacy, evidence, and release-readiness materials. | [HAL_OPEN_PUBLIC_INTEREST](https://github.com/UniteAndCreateForLife/HAL_OPEN_PUBLIC_INTEREST) |
| **HAL community and peer gateway** | Public onboarding material, an agent card, MCP setup, peer-join guidance, and a containerized model-gateway example. | [hal-supreme-community](https://github.com/UniteAndCreateForLife/hal-supreme-community) |

## Engineering capabilities demonstrated

- **Agent and workflow architecture:** durable tasks, bounded workers, canonical state ownership, idempotent work orders, and human approval gates.
- **MCP and provider integration:** Streamable HTTP clients, runtime schema discovery, secret-safe authentication, capability inventory, cost controls, and replaceable provider adapters.
- **Multi-assistant engineering:** ChatGPT, OpenCode, and Claude Code connected through bounded, evidence-producing tool surfaces without duplicating canonical work state.
- **Multimodal production:** image, video, audio, 3D, assembly, quality control, provenance, and platform export workflows.
- **Evidence and security:** deterministic acceptance, SHA-256 receipts, privacy minimization, tamper detection, RBAC, tenant isolation, fail-closed routing, and adversarial tests.
- **Revenue operations:** evidence-bound opportunity stages, payout readiness projections, terms freshness, exact-SHA evidence, idempotent status reporting, and explicit human action queues.
- **Delivery:** Python services and CLIs, Cloudflare Workers, Docker, GitHub Actions, multi-platform CI, operator runbooks, and reproducible demonstrations.

## Evidence standard

“Verified” in this portfolio means the referenced source and its test or receipt are public. Provider catalogs and runtime observations are dated snapshots because remote services can change. Private operational code, credentials, personal data, high-entropy connector paths, balances, and account state are excluded.

The machine-readable index is [`portfolio/portfolio.json`](portfolio/portfolio.json). Run the public evidence gate with:

```bash
python scripts/validate_public_portfolio.py
python -m unittest -v tests.test_public_portfolio
```

## Collaboration

This work is suitable for conversations with infrastructure providers, model and media platforms, research partners, grant programs, accelerators, clients, and investors looking for implementation evidence rather than concept-only claims.

- [Contributing](CONTRIBUTING.md) — focused public contributions and evidence standards.
- [Community roadmap](docs/COMMUNITY_ROADMAP.md) — current interoperability, evaluation, local-AI, provenance, multimodal, and agent-safety themes.
- [Work With HAL](docs/WORK_WITH_HAL.md) — bounded paid engineering, research, infrastructure, and integration collaboration.

The clearest technical starting points remain the case studies above and their linked receipts.
