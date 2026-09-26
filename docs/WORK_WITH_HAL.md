# Work With HAL

HAL SUPREME is available for bounded engineering collaborations where the deliverable can be tested and reviewed.

This page is intentionally specific about what is demonstrated publicly and avoids claiming customer deployments or capabilities that are not evidenced in the repository.

## Fixed-price offer: Verified fix

**You pay only if you merge.** For maintainers and small teams with one well-scoped GitHub issue: a bug, a missing test, or a small feature.

How it works:
1. You open a [Verified fix request](https://github.com/UniteAndCreateForLife/HAL_SUPREME/issues/new?template=verified-fix-request.yml) for an issue in a public repository. Scope and price are confirmed in that issue before any work starts.
2. HAL's coding agent writes a plan. You approve it before any code is written.
3. The agent implements the change and runs your tests.
4. HAL applies the patch to a clean checkout and runs the tests again in an isolated sandbox with no network access. The result is a verification receipt with SHA-256 digests of the patch and of the test output.
5. A pull request is opened only after HAL's operator approves it. It credits the AI agent and cites the receipt. You review it, and you pay only if you merge.

Price:
- **$79** per merged pull request for the first 3 clients, in exchange for an honest public review; **$149** after that.
- **$199** to move a workflow off `pull_request_target`. From November 2, 2026, GitHub blocks that trigger by default on public repositories that have no Actions policy allowing it ([GitHub changelog](https://github.blog/changelog/2026-09-17-workflow-execution-protections-in-github-actions-generally-available/)). If a workflow must keep the trigger, you get a short written review instead; changing the policy stays your decision.
- **Merged or free:** if the pull request isn't merged within 14 days, you owe nothing. After a merge, you are invoiced.

What you receive:
- the approved plan and the pull request;
- a regression test that fails when the fix is reverted;
- a test log from a clean checkout, the verification receipt, and your CI result;
- an AI-assistance disclosure;
- one round of revisions.

Limits:
- one issue per request, in a public repository (for a private repository, ask first through https://halsupreme.com);
- Python or JavaScript/TypeScript;
- at most about 300 changed lines across 5 files;
- tests that run offline in 10 minutes or less and need no secrets;
- no authentication, payment, or database-migration changes;
- not for repositories whose contribution rules forbid AI-assisted changes.

Turnaround: a plan within 24 hours, then the pull request within 3 business days after you approve the plan.

The coding agent is currently [Jules](https://jules.google/docs/faq/), Google's coding agent, so your repository's code is processed under Google's Jules terms.

Why the first three are discounted: so far this pipeline has been used only on HAL's own repositories. These four pull requests were written by Jules, verified independently on a clean checkout, and merged on 2026-09-26:
- [HAL_SUPREME #49](https://github.com/UniteAndCreateForLife/HAL_SUPREME/pull/49): the campus evidence desk counts conflicts with repeated evidence IDs. 7 CI checks passed on 4 platforms.
- [HAL_SUPREME #50](https://github.com/UniteAndCreateForLife/HAL_SUPREME/pull/50): 11 adversarial Evidence Gate tests; they catch 7 of 7 deliberately broken gates. Closes issue #40.
- [HAL_OPEN_PUBLIC_INTEREST #9](https://github.com/UniteAndCreateForLife/HAL_OPEN_PUBLIC_INTEREST/pull/9): a loopback-host security fix. The new test fails against the old code.
- [HAL_OPEN_PUBLIC_INTEREST #10](https://github.com/UniteAndCreateForLife/HAL_OPEN_PUBLIC_INTEREST/pull/10): hash-chain verification for the audit ledger; it catches 8 tampering patterns.

## Strong-fit paid engineering

### Agent reliability audit

For an existing AI-agent system that works but is unreliable.

Typical first deliverable:
- architecture and failure map;
- reproducible failure cases;
- evaluation/regression set;
- retry/idempotency/validation review;
- evidence and hallucination controls;
- observability recommendations;
- prioritized implementation plan.

Relevant public evidence:
- [HAL Campus Evidence Desk](../challenges/global-smart-campus-2026/)
- [Revenue Truth Control Plane](../examples/revenue_truth/)
- [Public portfolio](../PORTFOLIO.md)

### MCP / tool integration

For teams connecting agents to tools, internal services, or replaceable providers.

Typical deliverable:
- tool/MCP contract;
- authorization boundary;
- schema and failure handling;
- deterministic tests;
- human-approval gates for protected actions;
- provider-neutral integration notes.

Relevant public evidence:
- [Claude Code + HAL MCP Fabric case study](../case-studies/CLAUDE_HAL_MCP_FABRIC_2026-09-24.md)
- [Livepeer MCP integration](LIVEPEER_CREATIVE_MCP.md)

### Evidence and citation validation

For AI systems that must separate source evidence from model inference.

Typical deliverable:
- evidence contract;
- citation validation;
- unsupported-claim rejection;
- uncertainty/conflict handling;
- machine-readable receipts;
- reproducible evaluation.

Relevant public evidence:
- [HAL Campus Evidence Desk](../challenges/global-smart-campus-2026/)

### Private/local AI architecture

For workflows that need local/open models, bounded cloud fallback, or provider independence.

Typical deliverable:
- routing architecture;
- privacy/egress policy;
- model/provider abstraction;
- local-first failure behavior;
- validation and operating runbook.

## Research and open-source collaboration

HAL is also interested in non-commercial collaboration around:
- agent evaluation and safety;
- MCP interoperability;
- provenance and reproducibility;
- local/private AI;
- public-interest AI infrastructure;
- multimodal and embodied interfaces.

## What HAL does not claim

The public portfolio does not claim:
- universal production experience across every framework;
- customer deployments that are not public;
- compliance certification;
- guaranteed business outcomes;
- guaranteed bounty, contract, or investment results.

## Starting a conversation

For public technical collaboration, open a focused GitHub issue describing the problem, relevant repository, desired outcome, and whether the work is open-source, research, or commercial.

For private/commercial details, use the contact path on the HAL website rather than posting confidential information in a public issue:

https://halsupreme.com

A strong first engagement is deliberately bounded: one audit, one integration, one evaluation harness, or one reproducible vertical slice with acceptance criteria.
