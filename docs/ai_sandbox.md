# AI Sandbox standing design

This document is the standing design contract for HAL's AI sandbox / Agent World work, including the independently developed Godot simulation.

## Authority

**Models propose actions; the arena owns reality.**

Godot/the director owns world and physics state, participant slots, action validation, think deadlines, score, scenario rules, replay, deterministic evidence, termination, and fallback policy. A provider brain never mutates scene state directly.

## Provider boundary

Provider logic should run out of process wherever practical.

The canonical next boundary is the Agent World brain bridge:

`observation JSON -> external brain -> action JSON`

The first transport is stdio JSONL. The contract must remain transport-neutral so the same envelopes can later use local sockets or authenticated remote links.

## Protocol separation

Do not create one mega-protocol.

- **Brain bridge / HAL tick protocol:** high-frequency simulation observations and actions.
- **MCP:** tools, resources, episode administration, and integration surfaces.
- **A2A:** remote agent discovery, delegation, and coarse-grained collaboration.
- **AG-UI:** future spectator/operator event projection and human interaction.

These layers may reference one another, but none replaces the world authority.

## Fairness

- identical bodies/physics for like-for-like competition;
- identical observation/action contracts by role;
- explicit think/action budgets by competition class;
- fault isolation;
- randomized provider-to-slot assignment across repeated episodes;
- deterministic seeds and replay;
- recorded participant communication;
- no hidden provider-specific privileges;
- distinguish demonstration from statistically meaningful benchmark.

## Security

Treat object labels, imported map text, chat from other agents, scenario descriptions, external model output, MCP tool metadata, A2A Agent Cards, and remote participant descriptors as untrusted.

Adversarial tests should cover prompt injection through world labels, credential requests through chat, cross-slot action attempts, tick/request replay, wrong episode/slot identity, malformed or oversized frames, unsupported action escalation, covert unrecorded communication, stale protocol versions, and provider crash/timeout containment.

Provider credentials, hidden prompts, private runtime state, and local private paths must never cross the brain bridge or enter public replay evidence.

## Scenario sequence

### Resource Rush

Small deterministic world used for protocol and fairness proof.

### Cooperative Build

Requires communication, role division, object manipulation, and construction.

### Skate Brain League

Identical base bodies and physics with different external brains. Film every run and attach ruleset/replay evidence to results.

## Evidence standard

Use precise proof levels: configured, connected, tool-discovery verified, action verified, episode verified, cross-provider verified, replay verified, filmed Godot demonstration, statistically meaningful benchmark.

Never upgrade one label to another without evidence.

## Decision-rate classes

The existing 2 ms think budget is appropriate for an in-process or external
code-brain league, but it is not a meaningful budget for hosted LLM providers.

Keep one bridge contract and define scenario-level decision profiles instead:

- **realtime-code** — millisecond-scale deadline (for example the existing 2 ms
  budget), frequent decisions, deterministic local execution;
- **model-agent** — slower bounded decision cadence with a larger wall-clock
  deadline; the last accepted action or a deterministic motor controller remains
  active between decision ticks;
- **planner+motor** — the external model chooses goals/tricks/tasks at low
  frequency while a common deterministic motor controller executes high-rate
  physics actions.

Fairness means equal profiles within a scored class, not forcing every kind of
provider into an impossible universal latency.

Physics continues at the engine's normal rate regardless of provider latency.

## Current evidence status

External Muse/Godot sandbox reports now establish two separate evidence tracks:

### Model-agent track

A local Ollama `qwen2.5:0.5b` worker reportedly produced a genuine non-idle
`move` action that the arena validated and dispatched through the same external
brain contract used by the reference worker.

Measured CPU latency ranged from roughly 2.6 seconds for simpler requests to
about 11 seconds for the full game prompt. The proof therefore used a 25-second
decision interval and 20-second deadline.

Treat this as a provider-neutral **model-agent contract proof**, not a benchmark.

### Realtime-code track

The realtime bridge is not yet accepted. The current sandbox report identifies:

- over-counted transport faults in baseline/corrupt cases;
- reconnect timing races;
- worker-swap binding/resume failure;
- stable timeout quarantine in R9.

Do not mask these with relaxed thresholds.

## Immediate next milestone

Stabilize the realtime-code bridge before completing the MCP facade.

Required work:

1. one terminal request outcome per request ID;
2. transport retries/polls recorded separately from request faults;
3. explicit slot lifecycle: UNBOUND -> ACTIVE -> QUARANTINED -> CLOSED -> ACTIVE;
4. timeout closes/quarantines the old connection before rebinding;
5. fresh binding generation/handshake after reconnect;
6. worker swap uses the same close/rebind lifecycle instead of an ad-hoc path;
7. R1-R9 pass under restored strict criteria;
8. timing-sensitive cases pass repeatedly, not just once.

Reference semantics are in `examples/agent_world_arena/bridge_lifecycle.py` and
`docs/MUSE_REALTIME_BRIDGE_STABILIZATION.md`.

After the realtime suite is stable, implement the Godot MCP facade for
episode/status/replay administration while keeping high-frequency brain actions
on the brain bridge.
