# Muse arena-side brain bridge receipt — 2026-09-28

## Evidence class

**External sandbox report, not yet independently audited from HAL SUPREME source.**

The Muse sandbox reported this result from its separate Godot project. The
reported source tree is not present in the HAL SUPREME repository, so this file
records the claim and its provenance without upgrading it to HAL-verified source
evidence.

## Reported arena-side result

Muse reported **9/9 bridge acceptance tests passing**, with a filmed Godot match
and updated sandbox documentation.

Reported implementation location:

`~/workspace/skate_game/godot/scripts/sandbox/bridge/`

Reported bridge implementation included:

- `bridge_protocol.gd`
- `bridge_server.gd`
- `bridge_replay.gd`
- `external_brain_runner.gd`
- `reference_worker.py`
- TCP_NODELAY handling
- a stationary label-obeyer adversarial worker

Reported supporting changes included:

- bridge acceptance tests in `tests/check_bridge.py`
- a `run_bridge_tests.sh` launcher
- sandbox director CLI/pacing changes
- observation/action-dictionary methods in the Godot agent API
- standing design updates in `docs/ai_sandbox.md`

## Reported architecture

Protocol:

`hal.agent_world.brain_bridge.v0`

Transport:

loopback TCP with newline-delimited JSON.

Authority boundary:

**Models propose actions; the arena owns reality.**

The Muse sandbox reports one exact outstanding request per slot and a
world-enforced realtime code-brain deadline of 2 ms.

The reported design keeps simulation-tick transport separate from MCP, A2A, and
AG-UI responsibilities.

## Reported acceptance cases

The sandbox reported all nine acceptance cases passing:

1. baseline operation;
2. structural determinism;
3. mid-match worker crash -> fallback without match failure;
4. corrupt worker output -> rejected;
5. wrong-slot response -> rejected;
6. stale tick response -> rejected;
7. world-label injection attempt -> malicious action kind rejected before
   dispatch;
8. worker swap -> clean handoff;
9. slow worker -> timeout/fallback while the match survives.

The report explicitly treats timeout and late-response rejection as successful
enforcement of policy rather than test failure.

## Reported evidence

Video:

`~/workspace/your_files/sandbox_bridge_external_worker_2026-09-28.mp4`

Reported duration: 18 seconds.

Reported match:

HAL blue agent driven by an external Python worker versus a red in-process dummy
agent.

Replay:

- 1,096 ticks reported;
- `hello_accepted` reported from `film_worker3`.

Reported clean-worker latency:

- average: 0.20 ms;
- maximum: 0.88 ms.

The sandbox also reported that CPU contention can produce timeouts and that the
arena converts those to fallback behavior without killing the match.

## Security/fairness findings reported by Muse

- world/object text remained data rather than authority;
- slot isolation was enforced;
- stale/late responses were rejected by exact request identity;
- network arrival order did not directly mutate physics;
- credentials were absent from observations and replay;
- a plain Python worker could participate without provider-specific privileges.

The label-injection acceptance case reportedly caused the adversarial worker to
attempt a smuggled action kind; the arena rejected it as
`unknown_action_kind` before dispatch.

## Known remaining hardening

The Muse sandbox identified timeout quarantine as the next hardening slice:

- close the realtime brain connection after a deadline violation;
- require a fresh handshake before accepting later actions;
- eliminate the residual ambiguity created by draining a connection after a
  timed-out request.

This should be completed before describing the realtime transport as fully
duplicate/late-reply hardened.

## HAL-side reconciliation

The HAL branch now carries a transport-neutral version of the same envelope plus:

- stdio reference worker;
- loopback TCP reference client;
- local Ollama brain worker;
- request/response JSON schemas;
- out-of-process subprocess tests;
- TCP round-trip tests;
- model-agent deadline separation.

The Godot sandbox chose loopback TCP as its first transport while HAL initially
used stdio for the reference proof. That is not a protocol conflict: both use the
same request/response semantics and preserve the arena as authority.

## Claim boundary

What this receipt supports:

> An external Muse sandbox reported a filmed, fault-injected Godot bridge run
> using the shared Agent World brain-bridge contract, with 9/9 acceptance cases
> passing.

What this receipt does not yet support:

- independent HAL audit of the Godot source;
- exact source-hash correspondence between Muse and HAL implementations;
- local-model participation;
- live Muse-model participation;
- production remote transport security;
- a statistically meaningful provider benchmark.

Those require separate evidence.
