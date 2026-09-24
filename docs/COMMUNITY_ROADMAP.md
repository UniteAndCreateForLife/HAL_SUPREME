# HAL SUPREME Community Roadmap

HAL SUPREME is trying to become useful infrastructure and a useful body of engineering evidence, not just a large codebase. Community work is organized around problems that other AI builders can reuse.

## Current public themes

### 1. Agent reliability and evaluation

Help make tool-using agents easier to test and trust.

Useful contributions include:
- deterministic failure fixtures;
- retry and idempotency tests;
- evidence/citation validation;
- tool-call validation;
- human-approval boundaries;
- observability and replay;
- provider-failure handling;
- benchmark methodology.

### 2. MCP and tool interoperability

HAL treats providers and tools as replaceable workers.

Useful contributions include:
- MCP compatibility tests;
- schema-discovery improvements;
- safer authentication examples;
- adapter conformance tests;
- capability inventories;
- provider-neutral examples.

### 3. Local and private AI

HAL should work when cloud access is unavailable, undesirable, or too expensive.

Useful contributions include:
- local-model compatibility notes;
- bounded local inference examples;
- reproducible hardware benchmarks;
- privacy-preserving routing patterns;
- offline evaluation fixtures.

### 4. Evidence, provenance, and auditability

AI output should be distinguishable from verified evidence.

Useful contributions include:
- provenance schemas;
- tamper-evident receipts;
- citation/evidence checks;
- reproducible benchmark receipts;
- public-safe case-study tooling;
- adversarial tests for provenance failures.

### 5. Multimodal production

HAL also explores image, audio, video, 3D, and embodied interfaces.

Useful contributions include:
- replaceable render adapters;
- motion/quality-control tests;
- asset provenance;
- reproducible media pipelines;
- evaluation methods that reject still-frame or fake-motion shortcuts.

### 6. Agent and bounty safety

AI agents increasingly operate on public issues, bounty systems, and external instructions. Those surfaces can contain prompt-injection or credential-exfiltration traps.

Current work includes request-intent detection, public-source reputation checks, cross-repository competition analysis, and fail-closed opportunity screening.

## Contribution ladder

A contribution does not need to be large.

**First contribution**
- fix a reproducible documentation mismatch;
- add a test for an existing documented behavior;
- improve a public example;
- make a validation command work on another operating system.

**Intermediate**
- repair a bounded bug with regression coverage;
- add a provider adapter or conformance check;
- improve evaluation or evidence tooling.

**Advanced**
- improve canonical WorkGraph/Supervisor integration without creating duplicate authorities;
- add safe agent-execution controls;
- build reusable evaluation or provenance infrastructure.

## What we will not optimize for

- inflated commit counts;
- duplicate frameworks for the same authority;
- generic "AI integration" patches that already work through a standard interface;
- unverified performance claims;
- public disclosure of secrets, hidden prompts, or private operational state.

## How to start

1. Read [CONTRIBUTING.md](../CONTRIBUTING.md).
2. Review the [public portfolio](../PORTFOLIO.md).
3. Pick a narrowly testable problem.
4. Open an issue describing the observable failure or proposed acceptance criteria before a large implementation.

If you maintain a related AI-agent, MCP, local-model, evaluation, provenance, or multimodal project, cross-project interoperability work is especially welcome.
