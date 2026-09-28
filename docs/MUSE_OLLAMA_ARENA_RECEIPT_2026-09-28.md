# Muse Ollama arena proof — 2026-09-28

## Evidence class

**External sandbox report, not yet independently audited from HAL SUPREME source.**

This receipt records the Muse/Godot sandbox's reported local-model proof. The
Godot source and evidence directory are not currently present in this HAL
repository, so the result is preserved as external evidence rather than upgraded
to HAL-audited source evidence.

## Demonstrated claim

> A local Ollama model successfully participated in the Godot arena through the
> same provider-neutral external brain contract as the reference worker.

Reported model:

`qwen2.5:0.5b`

Reported headline action:

- tick: 1
- action: `{"kind": "move", "direction": [1.0, 0.0]}`
- result: validated by the arena and dispatched to the agent
- arena-measured latency: 11.3 seconds

This is stronger than an idle-only connectivity proof because the reported
model selected a non-idle action that passed the arena's action validator.

## Reported proof set

The sandbox reported **8/8 local-model proof cases passing**:

1. valid local-model action reaches Godot;
2. prompt-injection content remains data;
3. unsupported action is rejected;
4. Ollama unavailable -> fallback while match survives;
5. model timeout -> fallback while match survives;
6. worker crash -> fallback while match survives;
7. timeout quarantine + reconnect;
8. replay contains provider/request/slot/tick/action/latency/fault/fallback provenance.

Reported additional detail:

- unavailable-provider survival run: 180 ticks;
- worker-crash survival run: 377 ticks;
- quarantine case R9: 7/7 assertions passing consistently.

## Measured local-model latency

Reported CPU latency for `qwen2.5:0.5b`:

- approximately 2.6 seconds for a simpler request;
- approximately 11 seconds for the full game prompt.

The proof therefore used:

- 25-second model decision interval;
- 20-second model deadline.

This is an evidence-based correction to the earlier provisional 1–5 second
model-agent budget. The arena should keep a separate realtime-code profile for
millisecond workers and a slower model-agent profile for local/hosted LLMs.

## Reported evidence location

`~/workspace/skate_game/evidence/ollama_proof_2026-09-28/`

Reported contents:

- 60-second filmed match;
- five replay JSONL files;
- `REPORT.md` separating demonstrated claims from unproven claims.

## Security/fairness boundary

Reported:

- the model worker uses the same external brain contract as the reference worker;
- unsupported action kinds remain arena-rejected;
- provider unavailability, timeout, and crash do not kill the match;
- replay includes model/fault/fallback provenance;
- local models remain first-class participants.

Prompt-injection integration testing was constrained by local-model latency.
Worker-side validation was reported as passing at unit-test level; therefore the
full live-model injection path should not be promoted beyond that evidence.

## Realtime bridge suite status

The local-model proof does **not** imply that the realtime-code bridge suite is
fully accepted.

The same sandbox subsequently reported R1-R8 timing/flakiness:

- R1 baseline: 651 transport faults under the current accounting model and a
  reconnect timing failure;
- R3 corrupt worker: 702 non-malformed faults, indicating likely over-counting;
- R7 worker swap: only one worker reliably binds; clean post-swap ticks are not
  consistently restored;
- R9 quarantine: stable and consistently green.

Debug-relaxed thresholds are explicitly rejected as a final acceptance strategy.

## Reconciliation

The correct interpretation is:

- **model-agent provider-neutrality proof: demonstrated externally;**
- **realtime-code transport acceptance: pending stabilization.**

The next hardening target is strict request-level fault accounting plus an
explicit slot-connection lifecycle that removes reconnect and worker-swap races.

HAL's reference semantics for that work are now in:

- `examples/agent_world_arena/bridge_lifecycle.py`
- `tests/test_agent_world_bridge_lifecycle.py`
- `docs/MUSE_REALTIME_BRIDGE_STABILIZATION.md`

## Not yet demonstrated

This receipt does not establish:

- independently audited Godot source;
- live Muse-model participation;
- a provider benchmark;
- stable R1-R8 realtime bridge acceptance;
- production remote transport security;
- MCP administration over the Godot arena.

Those remain separate gates.
