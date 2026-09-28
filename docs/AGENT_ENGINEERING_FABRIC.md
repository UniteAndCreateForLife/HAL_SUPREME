# HAL unified agent engineering fabric

## Goal

HAL should get stronger when a worker changes, not fragment into separate Claude, Codex, OpenCode, Jules, or local-model workflows. The target is a provider-neutral engineering fabric with one task contract, deterministic verification, independent review, and evidence-backed promotion.

"Claude/Codex-level" reliability is a target for the workflow, not a claim that every HAL worker matches any particular model.

## Control-plane model

```text
intent / issue
    |
    v
task packet + acceptance criteria
    |
    +--> planner / explorer
    |
    +--> implementer
    |
    +--> reviewer
    |
    +--> verifier
    |
    v
evidence receipt
    |
    v
human/protected-action gate
    |
    v
merge / deploy / publish
```

Workers may be OpenCode, Claude Code, Codex, Jules, local models, or future providers. None owns canonical state.

## Shared instruction surfaces

- `AGENTS.md`: canonical repository contract for OpenCode, Codex-style agents, and any worker that can read project instructions.
- `CLAUDE.md`: compatibility shim that directs Claude Code to the canonical contract.
- `.opencode/agents/`: bounded specialist roles.
- `.opencode/commands/`: repeatable plan, fix, review, and verify entry points.
- module runbooks/tests: subsystem-specific truth.

Keep the root contract short enough to remain useful in every session. Put subsystem detail next to the subsystem.

## Task packet

Every substantial engineering task should be representable as:

```json
{
  "objective": "observable outcome",
  "scope": ["repository-relative paths or subsystem"],
  "constraints": ["security, privacy, compatibility, cost"],
  "protected_actions": ["merge", "deploy", "publish", "spend", "message"],
  "acceptance": ["deterministic condition"],
  "verification": ["focused command", "broader command"],
  "evidence": ["receipt or artifact path"],
  "status": "planned | implementing | blocked | verified | promoted"
}
```

The packet is intentionally model-neutral so HAL can route it without rewriting the task for each provider.

## Promotion gates

A change moves forward only when its evidence matches the gate:

1. **Planned:** objective and acceptance are explicit.
2. **Implemented:** diff exists; no completion claim yet.
3. **Focused verified:** changed behavior has a deterministic check.
4. **Regression verified:** broader relevant suite passes.
5. **Reviewed:** independent review is clean or findings are resolved.
6. **Promotion-ready:** receipts identify exact revision and verification.
7. **Promoted:** an explicitly authorized merge/deploy/publish action actually occurred.

Never collapse "implemented" into "verified" or "verified" into "deployed."

## Routing policy

Use the cheapest worker that can satisfy the acceptance criteria without weakening proof:

- discovery/indexing/formatting: local or inexpensive workers;
- bounded implementation: capable coding worker with repository tools;
- difficult architecture/debugging/security: strongest available reasoning worker;
- verification: deterministic tools first;
- review: independent model/agent when practical.

Provider health, cost, latency, and capability may influence routing. They do not influence truth.

## OpenCode workflow

Project commands provide a consistent operator surface:

- `/hal-plan <task>`
- `/hal-fix <task>`
- `/hal-review [focus]`
- `/hal-verify [scope]`

The reviewer cannot edit or execute shell commands. The verifier cannot edit and can run only bounded repository inspection/test commands declared in its permissions.

## Compounding loop

Every completed work order should feed the same after-action cycle:

1. compare outcome with acceptance criteria;
2. record failures, friction, and manual steps;
3. convert recurring failures into tests, policies, or reusable tooling;
4. route reusable components back into HAL;
5. publish only sanitized, evidence-backed lessons;
6. update task routing based on observed worker performance.

The purpose is not maximum agent activity. It is increasing verified output per unit of human attention, compute, and risk.
