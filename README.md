# HAL SUPREME

Canonical, curated source repository for HAL SUPREME.

HAL SUPREME is organized as a durable multimodal agent and production system. Stable control-plane state remains separate from replaceable AI workers and render backends.

## Public engineering portfolio

Start with the [HAL SUPREME public portfolio](PORTFOLIO.md) for a concise, evidence-linked view of completed work, current capabilities, and collaboration opportunities. The [public work log](docs/PUBLIC_WORK_LOG.md) records dated, reviewable milestones. The [publication policy](docs/PUBLIC_WORK_POLICY.md) defines how private HAL work becomes a safe public case study without publishing secrets, personal data, private endpoints, or unsupported claims.

## Get involved

- **Use or evaluate HAL:** start with the [public portfolio](PORTFOLIO.md) and its linked demos, tests, and receipts.
- **Contribute:** read [CONTRIBUTING.md](CONTRIBUTING.md) and the [community roadmap](docs/COMMUNITY_ROADMAP.md).
- **Research or interoperate:** open a focused collaboration issue for agent evaluation, MCP interoperability, provenance, local/private AI, or multimodal systems.
- **Hire / partner with HAL:** see [Work With HAL](docs/WORK_WITH_HAL.md) for bounded engineering engagement shapes and public proof.
- **Private details:** use the contact path at https://halsupreme.com rather than posting confidential information in GitHub.

HAL values narrow, testable work over generic integration requests or inflated activity.

## Architectural invariants
- Work is committed only after verification.
- Character/family identity is persistent and backend-independent.
- Authorized voice identity fails closed; generic TTS must never impersonate an enrolled human.
- Render providers are replaceable workers, never authorities over identity or release state.
- Every production stage is checkpointable and resumable.
- Delivered video must contain legitimate temporal motion; still-frame cheats fail QC.
- Artifacts carry provenance from inputs through verification and release.
- Secrets, model weights, caches, generated media, local databases and machine-specific state do not belong in Git.

## Production graph
INGEST → VOICE → SEGMENT → DEPTH → WORLD → COMPOSITE → RELIGHT → AUDIO_SPACE → GRADE → QC → MASTER

## Repository map
Only directories that exist in this repository are listed.

- case-studies/ — dated, evidence-linked write-ups of completed work
- challenges/ — challenge entries, including `global-smart-campus-2026/` (Campus Evidence Desk)
- evidence/ — machine-readable receipts backing the portfolio
- portfolio/ — structured portfolio index (`portfolio.json`)
- examples/ — self-contained modules: `revenue_truth/`, `cloudflare-edge-hardening-v1/`
- renderers/ — replaceable render adapters and routing (ComfyUI, LTX, remote workers)
- services/ — service entrypoints (`compute_router/`)
- integrations/ — external adapters (`livepeer_creative/`)
- plugins/ — inspectable plugin sources (`livepeer-creative-mcp/`)
- provenance/ — artifact/operation receipts
- qc/ — acceptance gates (motion QC)
- schemas/ — versioned contracts
- configs/ — safe configuration templates
- scripts/ — operator/developer tools, including the public-portfolio validator
- tests/ — contract and routing tests
- docs/ — architecture, runbooks, public work log and policy
- .github/ — CI workflows

This repository starts clean by design. Existing HAL code is migrated only after review, rather than bulk-importing historical filesystem debris.


## Livepeer Agent Creative MCP

HAL can use Livepeer Agent's creative MCP as a replaceable remote media worker for image, video, audio, multi-scene projects and finishing. ChatGPT and OpenCode can discover the provider's current tool schemas at runtime rather than pinning stale signatures. Provider mutations remain subject to explicit action and cost review.

Start with:

```bash
python scripts/livepeer_creative.py doctor
python scripts/livepeer_creative.py tools
```

See `docs/LIVEPEER_CREATIVE_MCP.md` for the authentication, OpenCode connection, spend-control, provenance and production runbook. The inspectable ChatGPT plugin source is in [`plugins/livepeer-creative-mcp/`](plugins/livepeer-creative-mcp/).

## Revenue truth control plane

The public [`examples/revenue_truth/`](examples/revenue_truth/) module projects
opportunity records through eleven evidence stages while keeping advertised
value separate from verified payment. Its focused tests protect the boundaries
between preparation, submission, acceptance, award, and settlement. See the
[case study](case-studies/REVENUE_TRUTH_CONTROL_PLANE_2026-09-24.md) and
[machine receipt](evidence/portfolio/revenue_truth_control_plane_2026-09-24.json).

## License

HAL SUPREME is licensed under the [Apache License 2.0](LICENSE).
