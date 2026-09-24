# Public Work and Portfolio Policy

Public evidence is a normal completion artifact for HAL work that is safe to share. The private HAL worktree remains separate from the curated public repository.

## Publication classes

| Class | Meaning | Destination |
|---|---|---|
| `PRIVATE` | Contains private code, credentials, account state, personal data, protected endpoints, or operational details. | Remains local. |
| `PUBLIC_SUMMARY` | A sanitized case study can describe the problem, implementation, verified result, and limitations. | `case-studies/` plus a receipt in `evidence/portfolio/`. |
| `PUBLIC_ARTIFACT` | Source, tests, demo, and evidence are safe and useful to reproduce publicly. | Curated project path in this repository. |

## Required evidence

Every portfolio entry must include:

- a dated observable result;
- public source, test, demo, or receipt links;
- the exact verification scope;
- limitations and non-claims;
- whether external services, paid compute, real data, or public side effects were used.

Provider catalogs and health observations must be dated. A configured integration is not described as live unless a current call succeeded. A local rehearsal is not described as a production deployment.

## Publication gate

Before merge:

1. remove credentials, tokens, private connector paths, personal data, local absolute paths, balances, and account usage;
2. avoid copying the private HAL repository wholesale;
3. run `python scripts/validate_public_portfolio.py`;
4. run the project’s focused tests;
5. require a clean public diff and passing GitHub Actions;
6. keep spending, account changes, submissions, messages, and release actions under separate explicit approval.

The portfolio records evidence. It does not become a second WorkGraph, EventStore, provider router, or release authority.
