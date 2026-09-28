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
- explicit think/action budgets;
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

## Immediate next milestone

Demonstrate the out-of-process JSON brain bridge in the existing Godot sandbox:

1. one external reference brain;
2. same sense/act semantics as the in-process brain;
3. the world-owned think deadline remains enforced;
4. brain failure falls back without killing the match;
5. shared chat stays world-mediated and recorded;
6. replay records request ID, slot, tick, action, latency, and fault class;
7. a second external worker can be substituted without changing Godot scene logic.

Once this works, attach local Ollama, then Muse, then additional frameworks to the same bridge contract.
