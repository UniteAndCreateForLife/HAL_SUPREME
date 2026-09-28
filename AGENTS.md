# HAL SUPREME agent instructions

This repository is the curated public HAL SUPREME engineering surface.

## General rules

- Read `README.md`, `CONTRIBUTING.md`, and the relevant project documentation before changing behavior.
- Prefer narrow, testable changes over speculative rewrites.
- Do not publish secrets, private endpoints, credentials, personal data, local paths, hidden prompts, chain-of-thought, private runtime context, model weights, or private receipts.
- Keep canonical task/workflow authority in HAL. External models and frameworks are replaceable workers.
- Do not weaken privacy, provenance, security, human-approval, or evidence gates to make an integration easier.
- Distinguish configured, connected, tested, submitted, completed, quality-passed, and published states.
- Add or update focused tests for behavior changes.
- Run the relevant tests before claiming success.
- Public claims require source, tests, CI, reproducible commands, or machine-readable receipts.

## Agent World priority

When working on `examples/agent_world_arena/`, `plugins/agent-world-mcp/`, Agent World tests, or related docs, first read:

- `docs/AGENT_WORLD_PLATFORM.md`
- `docs/AGENT_WORLD_MCP.md`
- `docs/AGENT_WORLD_INTEROP_ROADMAP.md`
- `docs/MUSE_AGENT_WORLD_PROMPT.md`
- `docs/META_MUSE_AGENT_WORLD_SETUP.md`

Core invariant:

**Models propose bounded actions; the arena owns reality.**

Preserve these properties:

1. World/episode state is authoritative outside model providers.
2. Provider/framework credentials never enter observations, scenarios, scores, replay, or public evidence.
3. Network response order must not decide a simulation tick.
4. Participant communication during scored runs is mediated and recordable.
5. Provider-to-slot assignment and evaluation must be reproducible.
6. Local/open-weight and hosted providers use the same external contracts.
7. Godot will become physics/visual authority; provider logic stays outside scene state.
8. MCP is for bounded tools/resources, A2A for coarse-grained remote collaboration, and the Agent World action protocol for deterministic simulation ticks.
9. Ordinary participants must not silently gain episode-admin or tick-commit authority.
10. Integration status must match evidence: config is not a live proof.

## Muse Code

Muse Code is a first-class engineering worker, not a second authority.

For Agent World work:

- use the `hal-agent-world` MCP server when available;
- verify the live inventory with `/mcp`;
- keep the MCP server in `required` mode for proof runs so a missing server fails loudly;
- use `muse exec --json` for bounded automated smoke tests;
- cap automated work with `--max-model-steps`;
- preserve session/tool evidence needed for review;
- never add Meta credentials to repository files or replay artifacts.

## Completion receipt

At the end of a substantial slice, report:

1. files changed;
2. tests/commands run;
3. exact pass/fail results;
4. security/fairness findings;
5. what is genuinely demonstrated;
6. what remains unproven;
7. next highest-leverage slice.
