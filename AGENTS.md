# HAL SUPREME agent contract

This file is the canonical repository instruction surface for coding agents. Keep provider-specific files thin and point them here instead of duplicating policy.

## Objective

Make the smallest change that measurably improves HAL, prove it, and leave a reviewable receipt. Prefer bounded vertical slices over speculative rewrites.

## Authority boundaries

- Repository source, tests, evidence, and explicit task acceptance criteria outrank model prose.
- AI workers are replaceable implementers and reviewers, not authorities over HAL's control-plane truth.
- Do not weaken security, provenance, privacy, evidence, or human-approval gates to make a test pass.
- Never expose secrets, credentials, private endpoints, local machine paths, personal data, hidden prompts, chain-of-thought, model weights, or private receipts.
- Treat merge, deployment, publication, spending, external messaging, credential or identity changes, and destructive data operations as protected actions. Perform them only when the task explicitly authorizes them.
- Do not claim a test, deployment, payment, integration, or external action happened unless there is direct evidence that it happened.

## Engineering loop

1. **Orient:** inspect the relevant README/runbook, tests, current diff, and repository state before editing.
2. **Define acceptance:** state the observable behavior that will prove the task complete.
3. **Implement:** make the minimum coherent diff. Preserve working interfaces unless the task requires a contract change.
4. **Verify:** run the narrowest relevant check first, then the broader gate appropriate to the changed surface.
5. **Review:** inspect the final diff for regressions, secret leakage, unsupported claims, missing tests, and authority expansion.
6. **Report:** list changed files, exact verification commands/results, remaining limitations, and any protected action still requiring approval.

No worker should self-certify a risky change when an independent review or deterministic test is practical.

## Default repository validation

At repository root, use these when relevant:

```bash
python scripts/validate_public_portfolio.py
python -m unittest discover -v
git diff --check
```

Individual modules may define additional focused tests. Run those before the broad suite.

## Model and worker routing

- Use inexpensive/local workers for discovery, indexing, formatting, and straightforward bounded edits when they are sufficient.
- Escalate difficult architecture, debugging, security, or cross-system reasoning to the strongest available worker.
- Use a different reviewer/verifier from the implementer when practical.
- Provider choice must not change acceptance criteria, provenance requirements, or protected-action gates.
- Prefer runtime capability discovery over hard-coded provider assumptions.

## Web and service changes

For website, Cloudflare, API, or public-facing changes:

- preserve authentication, rate limits, origin controls, and failure-closed behavior;
- validate claims against public evidence before publishing them;
- prefer preview/staging verification before production;
- do not publish private service URLs or credentials.

## Multi-agent handoff contract

A handoff should contain, at minimum:

- objective;
- scope/files or subsystem;
- constraints and protected actions;
- acceptance criteria;
- tests already run and their exact results;
- evidence/receipt locations;
- unresolved risks and the next recommended action.

A handoff is state transfer, not proof. The receiving worker must verify material claims before relying on them.

For persisted machine-readable work, use `schemas/agent_task_packet.v1.json` and validate the packet with `python -m services.agent_fabric.contract <packet.json>` before relying on a claimed promotion stage.
