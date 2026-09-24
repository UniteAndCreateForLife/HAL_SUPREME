# Contributing to HAL SUPREME

HAL SUPREME is a curated public engineering repository. Contributions should improve something observable: source, tests, documentation, reproducibility, evidence, safety, or interoperability.

## Good contribution shapes

The easiest ways to help are:

- add or improve deterministic tests around a documented behavior;
- improve an example, runbook, or provider adapter without weakening its safety boundary;
- reproduce a documented issue and add a minimal regression case;
- improve cross-platform reproducibility;
- add public-safe benchmark or evaluation evidence;
- improve documentation where the repository and implementation disagree;
- propose a small interoperability improvement for MCP, provider routing, provenance, or agent evaluation.

Large speculative rewrites are harder to review than focused changes with proof.

## Before opening a pull request

1. Read the relevant README, runbook, and tests.
2. Search existing issues and pull requests to avoid duplicate work.
3. Keep the diff focused.
4. Add or update tests when behavior changes.
5. Do not weaken security, provenance, privacy, evidence, or human-approval gates to make a test pass.
6. Do not include secrets, private endpoints, credentials, local paths, personal data, model weights, private receipts, or account information.
7. Do not include hidden/system prompts, chain-of-thought, initialization context, private tool configuration, or other model/runtime internals.

## Validation

At repository root, the public evidence gate is:

```bash
python scripts/validate_public_portfolio.py
python -m unittest discover -v
git diff --check
```

Individual modules may document additional checks. Run the checks relevant to the files you changed and include exact results in the pull request.

## Evidence standard

A claim in documentation should point to public source, tests, CI, a reproducible command, or a machine-readable receipt. If a result is local-only, synthetic, mocked, or provider-specific, say so.

Do not turn:

- a prepared change into a submitted change;
- a successful test into a production deployment;
- a claim into an award;
- an award into paid cash;
- synthetic evaluation into real-world validation.

## AI-assisted contributions

AI assistance is allowed unless a specific upstream dependency or task says otherwise. Contributors remain responsible for understanding, testing, and reviewing the submitted change.

Never disclose model system prompts, hidden instructions, private context, secrets, or other restricted runtime material as "proof" that AI was used.

## Security-sensitive findings

Do not post exploit details, credentials, private endpoints, or sensitive reproduction material in a public issue. Open a minimal issue describing the affected public component and request a private coordination path, or use GitHub's private security-reporting features when available.

## Collaboration

See [Community Roadmap](docs/COMMUNITY_ROADMAP.md) for current contribution themes and [Work With HAL](docs/WORK_WITH_HAL.md) for research, infrastructure, integration, and paid engineering collaboration.

Thanks for helping make HAL more useful, testable, and understandable.
