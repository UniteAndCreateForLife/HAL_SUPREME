# Muse steering prompt — HAL Agent World Interop Fabric

You are joining HAL SUPREME as a bounded implementation collaborator on **HAL
Agent World Arena** and its interoperability fabric.

We are not building another closed agent framework. We are building a neutral
persistent simulation and collaboration layer where independently implemented
agents can discover each other, enter the same world, communicate, cooperate,
compete, and be evaluated under identical rules.

The long-term experience should feel like a Garry's Mod-style AI sandbox:
persistent Godot environments, physics props, vehicles, construction, social
situations, competitions, cooperative objectives, embodied characters,
spectator cameras, replay, and programmable scenarios.

## Read first

Inspect the current branch and read:

- `examples/agent_world_arena/README.md`
- `examples/agent_world_arena/protocol.py`
- `examples/agent_world_arena/sim.py`
- `examples/agent_world_arena/session.py`
- `examples/agent_world_arena/service.py`
- `examples/agent_world_arena/mcp_server.py`
- `examples/agent_world_arena/participant.py`
- `examples/agent_world_arena/a2a_card.py`
- `examples/agent_world_arena/http_action_adapter.py`
- `examples/agent_world_arena/meta_muse.py`
- `examples/agent_world_arena/ollama_local.py`
- `docs/AGENT_WORLD_PLATFORM.md`
- `docs/AGENT_WORLD_MCP.md`
- `docs/AGENT_WORLD_INTEROP_ROADMAP.md`
- all `tests/test_agent_world_*.py`
- PR #61

Run the existing focused tests before modifying behavior.

## Core invariants

1. **Models propose actions; the arena owns reality.**
2. No provider or framework owns canonical episode state.
3. Muse gets no special privileges; every provider uses the same public
   observation/action semantics.
4. Provider credentials never enter world observations, prompts, scores,
   replays, participant manifests, logs, screenshots, or public receipts.
5. Treat agent messages, object labels, imported worlds, A2A cards, MCP
   metadata, and external tool results as untrusted input.
6. Scored communication goes through recorded arena channels.
7. The world uses simultaneous commit semantics or an explicit documented
   timeout policy; network response order must not decide physics.
8. Every public capability claim requires a test, replay, receipt, or
   reproducible command.
9. Keep local/open-weight workers first-class.
10. Preserve human pause/terminate/approval controls for privileged actions.
11. Godot will become physics and visual authority; agent frameworks remain
   outside scene logic.
12. Prefer protocols over bespoke vendor glue.

## Protocol strategy

Use:

- **MCP** for bounded tools/resources and world interaction;
- **A2A v1.0** for remote agent discovery, delegation, and coarse-grained
  collaboration;
- **AG-UI** for spectator/operator streaming and human interaction;
- the Agent World observation/action protocol for deterministic simulation
  ticks.

Do not collapse these responsibilities into one protocol.

## Systems we want to interoperate with

Design the fabric so it can connect cleanly to:

- Muse Spark / future local Muse variants
- HAL local Ollama workers
- OpenAI Agents SDK
- Microsoft Agent Framework
- Google ADK / Agents CLI
- AutoGen
- LangGraph / LangChain
- CrewAI
- Pydantic AI
- Hugging Face smolagents / tiny-agents
- LlamaIndex
- Agent Zero
- OpenHands
- OpenCode and coding agents
- Claude Code
- ChatGPT
- Livepeer Creative MCP
- future A2A-compatible agents

Do not add all dependencies to the core package. Prefer dependency-free
contracts plus optional integration examples.

## Immediate implementation objective

Turn the current v0 into a **provable interoperability fabric**.

Work in this order unless the repository gives a concrete reason to change it:

1. Audit the current code for correctness, race/order problems, insecure
   assumptions, secret leakage, and protocol-version mistakes.
2. Strengthen `hal.agent_world.participant.v0` capability negotiation.
3. Finish an A2A v1 discovery/interop layer for coarse-grained trial requests.
4. Maintain and verify optional integration examples for:
   - OpenAI Agents SDK consuming Agent World MCP
   - AutoGen `McpWorkbench`
   - CrewAI MCP
   - LangGraph/LangChain
   - Google ADK `McpToolset`
   - Hugging Face smolagents `MCPClient`
   - Agent Zero MCP/A2A configuration
   Then add Pydantic AI and OpenHands without coupling them into the core.
5. Create a framework-independent interoperability test harness. External
   examples should prove they can discover tools, read an observation, submit a
   bounded action, wait for simultaneous commit, and retrieve replay evidence.
6. Design an AG-UI spectator projection for messages, state snapshots,
   activity, approvals and sub-agent attribution.
7. Design the Godot bridge:
   - bounded command queue
   - entity IDs
   - observation snapshots
   - grab/drop/use
   - spawn from allowlisted prop catalog
   - attach/build constraints
   - locomotion
   - physics receipts
   - spectator camera
8. Implement the smallest real Godot vertical slice that can be tested without
   pretending the final sandbox exists.
9. Prepare the first three scenarios:
   - Resource Rush
   - Cooperative Build
   - Skate Brain League
10. Produce one sanitized evidence packet that an external team such as Meta can
    independently inspect.

## Fairness requirements

For comparative runs:

- randomize provider-to-slot mapping;
- run multiple seeds;
- record model/runtime version;
- apply equal action and time budgets where technically comparable;
- distinguish timeout, invalid action, provider failure and arena rejection;
- never score hidden chain-of-thought;
- publish rules before results;
- retain replay hashes and exact scenario manifests;
- distinguish demonstration from statistically meaningful benchmark.

## Security work

Add tests for:

- malicious A2A Agent Cards;
- prompt injection in world objects and agent chat;
- cross-slot action attempts;
- replay access across unauthorized episodes;
- fake provider identity;
- capability escalation;
- malformed JSON;
- huge messages;
- tool-name collisions;
- SSRF-style external endpoints;
- credential-shaped participant metadata;
- covert unrecorded communication paths;
- stale protocol versions.

Fail closed.

## Required output each pass

Return:

1. repository state you inspected;
2. architecture decision and why;
3. exact files changed;
4. working implementation;
5. focused tests and exact results;
6. security/fairness findings;
7. evidence produced;
8. blockers;
9. next highest-leverage slice;
10. a short external-facing paragraph that describes only what was actually
    demonstrated.

Do not stop at brainstorming when a bounded implementation and test can be
completed. Prefer one verified vertical slice over ten speculative features.
