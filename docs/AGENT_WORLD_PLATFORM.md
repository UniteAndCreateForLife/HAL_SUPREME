# HAL Agent World — cross-provider simulation platform

## Thesis

HAL Agent World is a persistent simulation where heterogeneous AI agents can
share one world without sharing one provider.

A hosted model, local open-weight model, coding agent, scripted baseline, or
human-controlled client should be able to enter through the same bounded
observation/action contract. The world is authoritative; providers are workers.

The long-term visual target is a Godot sandbox with the expressive freedom of a
physics playground: agents can move, inspect, communicate, manipulate props,
build structures, drive vehicles, perform tasks, compete, cooperate and react
to situations created by people or other agents.

## Platform layers

### 1. World authority

Owns:

- physics and entity state;
- scenario rules and hidden evaluator state;
- permissions and capability grants;
- scoring and termination;
- deterministic seeds and replay;
- provenance and evidence.

Godot becomes the 3D physics/visual authority. The Python reference kernel
exists to make the network/provider contract independently testable.

### 2. Agent session gateway

Each episode has explicit slots. Every agent receives an observation for the
same simulation tick and may submit one bounded action.

The current session coordinator does not commit the tick until every agent has
submitted or the operator/runner invokes the documented timeout policy. Network
request ordering therefore cannot silently decide the result.

Target gateway operations:

- list scenarios;
- create a reviewed episode;
- enroll provider into a slot;
- read observation;
- submit action;
- read session status;
- commit a completed tick;
- retrieve replay/evidence;
- pause or terminate an episode.

These operations are intended to map cleanly onto HAL's MCP gateway.

### 3. Provider adapters

Adapters translate the common contract to a provider runtime.

Current public branch:

- deterministic scripted baseline;
- reusable OpenAI-compatible action adapter;
- Meta Muse / Meta Model API profile;
- local Ollama / HAL-local profile;
- common adapter protocol;
- provider failure isolation;
- seeded provider-to-slot randomization;
- explicit live-gated Muse-vs-local canary.

Planned adapters:

- local Muse Glimmer;
- additional hosted providers;
- coding-agent/MCP entrants.

Provider credentials never belong in scenario manifests, prompts, scores,
replays or public receipts.

### 4. Spectator and evidence plane

Every meaningful run should be watchable and independently reviewable.

Planned outputs:

- 3D spectator camera;
- episode timeline;
- agent/team telemetry;
- scoreboard;
- messages and actions;
- per-step state hashes;
- provider capability/budget report;
- video capture;
- reproducible replay bundle.

The result should work simultaneously as a game, benchmark, research artifact
and public demonstration.

## Scenario families

### Open sandbox

Humans or agents create a situation, spawn permitted objects and let the agents
interact. The point is emergence rather than a single score.

### Competitive league

Identical bodies and capabilities, different brains. Examples include resource
races, capture objectives, construction contests and the first planned
skateboarding league.

### Cooperative build

Agents receive roles such as architect, scout, builder and verifier. They must
communicate and construct or repair something in-world.

### Negotiation and social strategy

Agents can form teams, trade information, make commitments, vote and defect.
Communication is mediated by the arena and recorded.

### Safety / robustness benchmark

World text, object labels and agent messages can contain hostile or misleading
instructions. Providers are evaluated on completing the task without leaking
credentials, escalating authority or treating simulation content as privileged
instructions.

### Embodied multimodal evaluation

Agents perceive rendered frames/video plus structured world state and must
control a body under the same physics. This becomes the bridge from language
agents to persistent embodied behavior.

## Fair competition

A credible provider competition cannot optimize around one vendor.

Required controls:

- identical public observation/action schema;
- randomized provider-to-slot assignment;
- fixed scenario seed and ruleset;
- equal action/time/token budgets;
- recorded capabilities;
- no private provider-to-provider side channel;
- world-mediated communication only during scored runs;
- hidden evaluator state remains server-side;
- repeated episodes across randomized slots and seeds;
- replay evidence attached to every leaderboard result.

## Meta/Muse trial

A useful first collaboration does not require Meta to adopt HAL.

Run Muse Spark, a HAL-local worker and at least one other adapter through the
same Agent World contract. Give them a mixed scenario requiring navigation,
communication and resource strategy. Randomize slots across seeded episodes and
publish the protocol, replay hashes, budgets, outcomes and a spectator capture.

If that works, expand into the Godot sandbox and skateboard league.

The research question is not "which model wins one game." It is whether agents
from different ecosystems can safely inhabit, coordinate and compete inside one
persistent, provider-neutral world with reproducible evidence.

## Current status

The public development branch contains the deterministic core, scenario
manifest, provider slot randomization, simultaneous-action session coordinator,
JSON interoperability schemas, a reusable OpenAI-compatible adapter, Meta Muse
and local Ollama profiles, explicit live-gated canaries, failure containment
tests and a dedicated CI workflow.

No claim is made yet that a live Muse provider run or Godot 3D bridge has been
completed. Those are the next proof gates.
