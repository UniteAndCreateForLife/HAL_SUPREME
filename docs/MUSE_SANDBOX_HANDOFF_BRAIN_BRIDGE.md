# Muse sandbox handoff — build the JSON brain bridge now

This handoff is intentionally self-contained. It does not require the Muse sandbox to have the HAL SUPREME repository or GitHub access.

## Decision

Start the out-of-process JSON brain bridge now. Do not wait for repository synchronization.

Also fold the protocol separation, fairness, and security invariants into the sandbox's standing `docs/ai_sandbox.md` design.

## Existing sandbox facts to preserve

- Godot/director owns world state, physics, scoring, and replay.
- Brains currently use an exclusive sense/act boundary.
- The runner already has a code-brain think budget and fault isolation.
- A brain failure must not terminate a match.
- Shared participant chat is world-mediated and recorded.
- Matches are already filmable/replayable.

## New boundary

Move one brain out of the Godot process while preserving the same game semantics.

Use persistent newline-delimited JSON over stdio first.

### Request

```json
{
  "protocol_version": "hal.agent_world.brain_bridge.v0",
  "request_id": "episode-1:7:slot-a",
  "episode_id": "episode-1",
  "tick": 7,
  "slot_id": "slot-a",
  "deadline_ms": 2,
  "allowed_actions": ["idle", "move", "look", "grab", "say"],
  "observation": {}
}
```

### Response

```json
{
  "protocol_version": "hal.agent_world.brain_bridge.v0",
  "request_id": "episode-1:7:slot-a",
  "episode_id": "episode-1",
  "tick": 7,
  "slot_id": "slot-a",
  "action": {"kind": "idle"},
  "diagnostics": {"elapsed_us": 450, "worker": "reference-v0"}
}
```

## Validation

Before an action can reach the director, require exact match on protocol version, request ID, episode ID, tick, and slot ID. Reject action kinds not present in the request's `allowed_actions`.

Frames must be bounded in size. Malformed, late, stale, duplicate, wrong-slot, or unsupported responses fail closed to the existing scenario fallback, normally idle.

Do not echo raw malformed input into logs or replay.

## Replay evidence

For each external decision record:

- request ID;
- episode/tick/slot;
- provider/worker identity;
- accepted action kind;
- elapsed time;
- status: ok / timeout / malformed / worker-crash / rejected;
- fallback used, if any.

Do not record hidden reasoning.

## Timing

For the first reference-worker proof, preserve the existing code-brain deadline (2 ms if that is the current configured rule).

Do not force hosted LLMs into a 2 ms deadline later. Keep the same bridge contract but add scenario-level decision profiles:

- realtime-code: millisecond deadline, high-frequency decisions;
- model-agent: slower bounded decision cadence and larger deadline;
- planner+motor: low-frequency external planning plus a shared deterministic high-frequency motor controller.

Physics stays authoritative and continues at the engine rate in every class.

## Security tests

Add executable tests for:

1. prompt injection in object labels remains observation data only;
2. agent chat asking for private configuration cannot change bridge authority;
3. wrong slot ID is rejected;
4. stale/duplicate tick response is rejected;
5. unsupported action escalation is rejected;
6. malformed/oversized JSON is contained;
7. worker crash becomes fallback rather than match crash;
8. timeout becomes fallback and replay evidence;
9. external brain cannot directly mutate Godot state;
10. shared chat remains world-mediated/recorded.

## Protocol separation to add to docs/ai_sandbox.md

- brain/tick bridge = high-frequency simulation sense/act;
- MCP = tools, resources, episode administration, integration;
- A2A = discovery/delegation/coarse collaboration;
- AG-UI = spectator/operator event plane.

Do not turn any one of those into the simulation authority.

## Acceptance proof

The slice is complete only when:

1. an external reference worker is launched as a separate process;
2. Godot sends observations through the JSONL bridge;
3. responses are validated before action dispatch;
4. existing think/fault semantics still work;
5. an intentional worker failure does not kill the match;
6. replay shows the external decision evidence;
7. swapping the external worker does not require changing Godot scene logic;
8. a filmed match or deterministic test demonstrates the external brain actually participated.

## Output

Return exact files changed, commands/tests run, pass/fail results, replay/video evidence, security/fairness findings, what is demonstrated, what remains unproven, and the next highest-leverage slice.
