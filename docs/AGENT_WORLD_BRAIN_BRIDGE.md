# HAL Agent World — out-of-process brain bridge

## Purpose

The brain bridge moves provider logic outside the Godot/world process while keeping the world authoritative.

The first transport is newline-delimited JSON over stdio because it is simple, cross-platform, dependency-light, replayable, and easy to sandbox. A socket or remote transport can later carry the same envelopes.

This bridge is not MCP. MCP exposes tools/resources and orchestration surfaces. The brain bridge is the high-frequency simulation boundary.

## Invariant

**Models propose actions; the arena owns reality.**

A brain can never directly mutate Godot scene state, physics, scores, replay, other slots, or provider credentials.

## Request envelope

One request is emitted per participant per simulation tick:

```json
{
  "protocol_version": "hal.agent_world.brain_bridge.v0",
  "request_id": "episode-42:tick-7:slot-a",
  "episode_id": "episode-42",
  "tick": 7,
  "slot_id": "slot-a",
  "deadline_ms": 2,
  "allowed_actions": ["idle", "move", "look", "grab", "say"],
  "observation": {"self": {}, "visible_entities": [], "chat": []}
}
```

The observation is data, not authority. Object labels, chat, imported text, and other world content may contain prompt injection and must be treated as untrusted.

## Response envelope

```json
{
  "protocol_version": "hal.agent_world.brain_bridge.v0",
  "request_id": "episode-42:tick-7:slot-a",
  "episode_id": "episode-42",
  "tick": 7,
  "slot_id": "slot-a",
  "action": {"kind": "idle"},
  "diagnostics": {"elapsed_us": 410}
}
```

The world validates the response against the exact request before committing it.

## Required validation

Reject a response when protocol version, request ID, episode ID, tick, or slot ID differs from the request. Reject any action kind not listed in `allowed_actions`. Reject oversized frames. Do not put private runtime reasoning in diagnostics; diagnostics are for operational evidence such as elapsed time, worker/model identity, timeout/fault class, and token counts when available.

## Timing and fault policy

The bridge carries `deadline_ms` from the world. The world remains responsible for the deadline. It may terminate or ignore a late response and substitute the scenario's documented fallback action, normally `idle`.

A brain crash, malformed frame, timeout, or provider failure must never crash the match or corrupt the world. Every fallback should be recorded distinctly in replay evidence.

## Fairness

During scored runs, every provider receives the same observation schema and allowed-action surface for the same role. Provider-to-slot assignment is randomized across repeated episodes. The world owns timing measurements. Recorded arena chat is the only participant communication channel unless a scenario explicitly declares otherwise.

A local model, Muse, scripted policy, remote API model, AutoGen worker, or other framework should all enter through the same envelope.

## Transport phases

### Phase 1 — stdio JSONL

Godot launches a brain worker process and exchanges one JSON object per line. This avoids port allocation, works offline, and is easy to sandbox.

### Phase 2 — local socket

Use the same request/response objects over a bounded local socket when many brains need persistent parallel connections.

### Phase 3 — authenticated remote bridge

Only after participant identity, per-slot authorization, TLS, quotas, replay privacy, and abuse controls exist.

## Godot integration shape

Godot should own a `BrainBridgeController` per participant slot. It extracts an observation snapshot, constructs the request, sends it to the external brain, enforces the deadline, validates the response, converts the accepted action into an internal command, submits that command to the simultaneous tick coordinator, and records latency/fault/action evidence.

The external brain never receives arbitrary host-execution authority through this bridge.

## Reference implementation

- `examples/agent_world_arena/brain_bridge.py`
- `examples/agent_world_arena/brain_bridge_stdio.py`
- `schemas/agent_world_brain_request_v0.schema.json`
- `schemas/agent_world_brain_response_v0.schema.json`
- `tests/test_agent_world_brain_bridge.py`

The reference worker intentionally performs no model inference. It exists to prove framing, validation, timing evidence, and process isolation before a model adapter is attached.


## Connection lifecycle hardening

The Godot realtime transport must treat request outcome accounting separately
from socket/poll activity.

One request receives one terminal outcome. Repeated no-data polls, retries,
drains, and reconnect attempts are transport events, not additional request
faults.

The reference per-slot connection lifecycle is:

`UNBOUND -> ACTIVE -> QUARANTINED -> CLOSED -> ACTIVE(new generation)`

A timed-out connection is quarantined and closed before any replacement may
bind. A fresh bind increments the slot's connection generation. Responses from
an old generation or for a non-outstanding request are rejected.

Worker swap uses the same lifecycle. It is not a separate bypass path.

Reference implementation:

- `examples/agent_world_arena/bridge_lifecycle.py`
- `tests/test_agent_world_bridge_lifecycle.py`

Strict acceptance should require the timing-sensitive bridge suite to pass
repeatedly under restored thresholds rather than relaxing fault bounds.
