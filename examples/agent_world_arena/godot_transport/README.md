# Native nonblocking transport component

This is an additive Godot transport/test component, not the externally developed game runner. The existing arena remains authoritative for request identities, actions, scoring, deadlines and terminal outcomes.

## Verified at baeb1e8169db67d9f39c2083388762dffeb74f9a

The [native proof workflow](https://github.com/UniteAndCreateForLife/HAL_SUPREME/actions/runs/36532292232) completed successfully on 2026-09-29:

- Godot 4.7.2, verified against the official archive SHA-256.
- 500 assertions across 20 repeated component-test passes, using a fake peer.
- An actual loopback TCP probe with a moving CharacterBody3D and delayed, fragmented scripted reply: 20 physics ticks before the first reply, 0.900000095367432 m total displacement, exact reply reassembly, 450 ms wall duration.
- All 60 discovered public Agent World Python tests passed, including the previously failing authorization_token diagnostic-field regression.
- Five Muse settings tests passed. These are configuration tests, not a live Muse run.

No paid model, render service, public gameplay upload or live third-party agent was used. The probe is not the external R1-R9 suite and is not an end-to-end model-controlled game test. No game frame-rate or native production latency guarantee is inferred from it.

## What changed

`partial_frame_pump.gd` uses only partial send/receive operations, retains incomplete bytes, limits bytes and frames per poll, and emits one sanitized `protocol_fault` event on terminal transport failure. A no-data poll is not a fault. Close is explicit before rebinding; generation increases on bind.

An existing Python denylist omitted credential aliases including authorization_token. The bounded fix adds explicit aliases while preserving legitimate game fields such as token_count and tokens. This denylist is defense-in-depth, not a general secret detector or replacement for egress minimization.

## Integrate into the existing runner without creating a second authority

1. Bind an already connected peer to one pump. Keep the runner's existing slot and request state machine.
2. Queue at most the current outstanding request; do not introduce a second inference scheduler or TCP service.
3. Poll once with bounded work, then match complete raw frames against the exact request/episode/tick/slot and current connection generation in the runner.
4. Handle the poll's fault result synchronously: record at most one terminal outcome for the outstanding request, quarantine the slot, clear held controls, and close the pump. Keep transport-event counts separate from request-failure counts.
5. Connect the signal with CONNECT_DEFERRED for diagnostics only; never let a delayed callback terminate a newer request or count a second terminal outcome. Capture request identity at the synchronous fault transition.
6. Maintain the wall-clock deadline in the host, including the period spent flushing a request. On timeout, quarantine and explicitly close before rebind; reject old-generation replies.
7. Dispatch every physics tick. Latch only continuous motion with a bounded expiry. Jump, spawn, build and message commands must be edge-triggered, not replayed every waiting tick.
8. Collect eligible actions across slots before the authoritative world commit. Response arrival order must not decide competitive outcomes.

A fault stops this component but deliberately leaves socket close to the host so lifecycle policy stays explicit. Native signal listeners must not perform blocking work. Loopback transport is not a public internet authentication boundary.

## Run

From repository root, with Godot 4.7.2 installed:

```sh
godot --headless --path examples/agent_world_arena/godot_transport --script res://test_partial_frame_pump.gd
godot --headless --path examples/agent_world_arena/godot_transport --script res://test_loopback_physics.gd
python -m unittest discover -s tests -p 'test_agent_world*.py' -v
python -m unittest -v tests.test_muse_agent_world_config
```

Install the project's optional MCP SDK dependency in an isolated environment for the Python integration tests (`mcp>=2,<3`; this run resolved 2.2.0). Native tests emit structured receipts. CI fails on script errors, missing receipts or failed assertions; it does not equate exit zero alone with proof.

## Remaining proof gates

Obtain the current external bridge/runner source; integrate this component or the equivalent fixes without replacing working ownership; rerun the actual R1-R9 harness repeatedly; run one explicitly bounded local-model episode; capture genuine new gameplay with request outcomes, body motion, frame timing and source hashes. No production/full-game claim should precede those gates.

Reference API behavior: [Godot StreamPeer partial I/O](https://docs.godotengine.org/en/stable/classes/class_streampeer.html).
