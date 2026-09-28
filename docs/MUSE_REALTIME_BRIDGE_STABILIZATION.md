# Muse realtime bridge stabilization plan

The local-model proof is valid, but the realtime bridge suite is **not accepted**
while R1-R8 remain timing-flaky. Do not proceed to treating the MCP facade as a
completed integration until the realtime transport is green under strict
criteria.

## Current reported failures

- R1 baseline: hundreds of transport faults, plus reconnect race.
- R3 corrupt worker: hundreds of non-malformed faults.
- R7 worker swap: second worker does not reliably bind; match does not reliably
  return to clean ticks.
- R9 quarantine: consistently passes.

The large 651/702 counts strongly indicate that the harness is counting
transport polls/retries/events as independent request faults.

## Decision

Fix the realtime bridge next.

MCP-facade design can continue on paper, but its implementation should sit on a
stable bridge lifecycle rather than encode current races.

## 1. Separate request outcomes from transport events

One request may have **exactly one terminal outcome**:

- accepted
- timeout
- malformed
- rejected
- worker_crash
- transport_closed

Socket reads, retries, no-data polls, reconnect attempts, drain operations, and
handshake waits are transport events, not additional request faults.

The reference semantics are implemented in
`examples/agent_world_arena/bridge_lifecycle.py`.

Do not relax acceptance thresholds to accommodate repeated counting. Fix the
accounting model.

## 2. Make binding a state machine

Use explicit per-slot states:

`UNBOUND -> ACTIVE -> QUARANTINED -> CLOSED -> ACTIVE(new generation)`

Rules:

- only one active connection owns a slot;
- one active slot has at most one outstanding request;
- timeout moves ACTIVE to QUARANTINED;
- quarantined connection is closed;
- a replacement cannot bind until the old connection is closed;
- every successful bind increments a connection generation;
- responses are accepted only from the active peer/generation for the exact
  outstanding request.

Do not solve this with arbitrary sleeps.

## 3. Eliminate startup/reconnect races

The runner should wait on an explicit readiness condition, not timing guesses.

Recommended sequence:

1. arena listener ready;
2. worker connects;
3. worker/slot handshake accepted;
4. slot state becomes ACTIVE;
5. match begins or resumes.

For reconnect:

1. request times out;
2. mark terminal request outcome once;
3. quarantine connection;
4. close old socket;
5. transition slot to CLOSED/UNBOUND-ready state;
6. accept new connection;
7. complete fresh handshake;
8. increment binding generation;
9. resume clean ticks.

## 4. Fix worker swap as the same lifecycle

Worker swap should not have a separate ad-hoc path.

Use:

`ACTIVE(worker A) -> CLOSED -> ACTIVE(worker B, generation+1)`

The acceptance test should wait for the explicit second ACTIVE state and then
require a run of clean accepted ticks.

## 5. Strict acceptance criteria

Restore strict bounds. Do not leave debug-relaxed thresholds such as baseline
fault <= 50 as the final gate.

Recommended assertions:

- baseline: zero terminal faults after initial handshake;
- corrupt test: exactly the deliberately injected malformed/rejected outcome,
  not hundreds of transport faults;
- crash test: one crash-class terminal outcome for the affected outstanding
  request, followed by fallback and match survival;
- timeout test: one timeout outcome, quarantine, close, fresh bind;
- worker swap: exactly two successful binding generations and clean post-swap
  accepted ticks;
- no duplicate terminal outcome for any request ID.

Run each timing-sensitive case repeatedly (for example 20 consecutive runs)
before calling the bridge stable.

## 6. Keep the Ollama proof separate

The reported Ollama proof remains valuable:

- genuine non-idle move action accepted and dispatched;
- local model used the same provider-neutral bridge;
- arena-measured latency reached about 11.3 s on the full game prompt;
- fallback behavior survived unavailable/timeout/crash cases.

Do not invalidate that proof because the realtime-code suite is flaky. Record it
as a **model-agent contract proof**, while realtime-code transport acceptance
remains pending.

## 7. Next gate after stabilization

Once R1-R9 are green under strict criteria and repeated runs:

1. expose read/admin episode status and replay through the Godot MCP facade;
2. keep high-frequency brain decisions on the brain bridge;
3. run the authenticated Muse MCP tool-discovery proof;
4. then attach Muse/model-provider reasoning to the model-agent profile.
