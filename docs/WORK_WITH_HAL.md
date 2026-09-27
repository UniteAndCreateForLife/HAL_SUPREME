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

## Fixed-price offer: Code Health Check

**A written audit of one repository, delivered privately within 2 business days.** For teams that want to know what is broken or risky before it bites.

What HAL checks:
- GitHub Actions security:
  - breakage from GitHub's 2026 `pull_request_target` changes ([prt-check](https://github.com/UniteAndCreateForLife/prt-check));
  - script injection from issue or pull request text in `run:` steps;
  - workflows that never limit their token;
  - third-party actions pinned to a tag.
- Dependencies: pinned versions with published advisories in the [OSV database](https://osv.dev) (Python requirements, npm lockfiles).
- Committed secrets, reported by file, line and kind, never the value.
- Database rules in Supabase / Lovable Cloud migrations: rules that let the public key (or any signed-in user) read or change data, and tables without row level security.
- Python bugs that lint can prove, such as undefined names.
- Hygiene: tests, CI, license, security policy, dependency updates.

What you receive:
- the report: every finding, where it is, how to fix it, and a "fix first" list ([sample](samples/code-health-check-sample.md));
- each high and medium finding checked for false positives before delivery;
- a fixed quote for anything you want fixed through [Verified fix](#fixed-price-offer-verified-fix).

Price:
- **$99** for the first 3 clients, in exchange for an honest public review; **$249** after that.
- Invoiced after delivery. If the report has no high or medium finding, you owe nothing.

How it works: open a [Code Health Check request](https://github.com/UniteAndCreateForLife/HAL_SUPREME/issues/new?template=code-health-check-request.yml). The report is delivered in a private GitHub repository shared only with your account, never in the public issue.

Limits:
- one repository per request; public repositories only for now;
- automated checks plus review. This is not a penetration test or a compliance audit.

## Fixed-price offer: Lovable app database lockdown

**For apps built on Lovable Cloud or Supabase.** These apps send a public key to every browser, so the database's row level security rules are all that stands between that key and your data. Open rules are common: in 2025, [CVE-2025-48757](https://mattpalmer.io/posts/2025/05/CVE-2025-48757/) exposed data in 170+ Lovable apps this way. Our own Lovable Challenge app shipped with the same problem, and this is how we fixed it.

How it works:
1. HAL reads your repository's database migrations (through Lovable's GitHub sync) and lists every rule that lets the public key, or any signed-in user, read or change data, plus tables with row level security off.
2. The fix scopes each rule to the row's owner, or moves reads and writes into server functions and gives the public key no access.
3. The change arrives as a pull request that you review and can revert.
4. With your consent, HAL proves it against your own app: the same request with your public key, before (data) and after (permission denied).

Price:
- **$79** for the first 3 clients, in exchange for an honest public review; **$149** after that.
- You pay only after you have seen the before/after proof.

Limits:
- Lovable Cloud or Supabase apps with GitHub sync;
- your sign-in flow is not changed;
- a focused fix, not a penetration test.

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
