# HAL Agent World — interoperability roadmap

## Objective

Agent World should become a neutral meeting layer for heterogeneous agent
systems rather than another framework that asks everyone to migrate.

The integration rule is:

**adopt open protocols at the boundary; keep provider/framework specifics in
thin adapters.**

The simulation authority remains HAL Agent World. External systems may discover,
delegate, observe, act, or render interfaces, but they do not become canonical
owners of world state.

## Protocol stack

### MCP — tools and bounded world actions

Use MCP when a model or framework needs tools and resources exposed by Agent
World.

Current Agent World MCP surface:

- create/list episode
- read observation
- submit action
- read status
- advance tick
- explicit timeout-to-idle commit
- replay/evidence retrieval

This is the natural integration path for OpenAI Agents SDK, AutoGen, CrewAI,
Claude-compatible clients, Codex, Muse Code when MCP is available, and other
tool-oriented runtimes.

Official MCP:
https://modelcontextprotocol.io/

### A2A v1.0 — remote agent discovery and coarse-grained collaboration

Use Agent2Agent for agent discovery, delegation, asynchronous collaboration,
capability negotiation, and cross-organization task exchange.

Do **not** use A2A as the physics tick authority. A2A tasks may request or
coordinate a simulation trial; the bounded Agent World action contract remains
the real-time world interface.

Agent World now has a public-safe A2A v1 discovery-card generator.

Official A2A:
https://a2a-protocol.org/v1.0.0/

Official project:
https://github.com/a2aproject/A2A

### AG-UI — spectator/operator frontend

AG-UI is a strong candidate for the human-facing event plane: streamed agent
messages, activity, tool calls, state snapshots, approval interrupts, and
sub-agent visibility.

Use AG-UI for the spectator/control interface, not as the simulation authority.

Official project:
https://github.com/ag-ui-protocol/ag-ui

## Framework integration targets

### OpenAI Agents SDK

Integration: **MCP first**.

The OpenAI Agents SDK supports Streamable HTTP MCP, tool filtering, approvals,
sessions, guardrails, tracing, and multi-agent handoffs. An OpenAI agent should
consume the Agent World MCP server rather than requiring Agent World to embed an
OpenAI-specific execution loop.

Docs:
https://openai.github.io/openai-agents-python/mcp/

### Microsoft Agent Framework / A2A

Integration: **A2A + MCP**.

Microsoft Agent Framework can consume and host A2A agents. That makes it useful
for higher-level delegation into Agent World, while MCP remains the bounded
world-tool surface.

Docs:
https://learn.microsoft.com/en-us/agent-framework/journey/agent-to-agent

### AutoGen

Integration: **MCP**.

AutoGen exposes `McpWorkbench` with Streamable HTTP support. AutoGen teams can
therefore enter Agent World without a bespoke AutoGen simulation API.

Docs:
https://microsoft.github.io/autogen/stable/reference/python/autogen_ext.tools.mcp.html

### LangGraph / LangChain

Integration: **MCP for world tools; A2A for independently hosted agents**.

LangGraph remains useful for durable provider-side state machines, long-running
planning, human-in-the-loop behavior, and checkpoints. Agent World should not
duplicate those provider-internal graphs.

LangGraph:
https://langchain-ai.github.io/langgraph/

LangChain Agent Protocol:
https://langchain-ai.github.io/agent-protocol/

### CrewAI

Integration: **MCP**.

CrewAI can hydrate MCP tools into crews and flows. A Crew can therefore act as
one Agent World participant, or individual crew members can be mapped to
separate slots when the scenario explicitly permits it.

Docs:
https://docs.crewai.com/

### LlamaIndex

Integration: **MCP knowledge/retrieval worker**.

LlamaIndex and LlamaParse expose MCP-compatible retrieval surfaces. This is
valuable for scenarios where an embodied agent must consult documents, manuals,
maps, scientific evidence, or structured knowledge before acting.

Docs:
https://developers.llamaindex.ai/

### Meta Muse

Integration today: **OpenAI-compatible action adapter**.

Future integration: MCP/A2A where Meta exposes or adopts those surfaces for the
relevant product. Muse must never get provider-specific world privileges.

### Local HAL / Ollama

Integration today: **OpenAI-compatible loopback adapter**.

Local models use exactly the same observation/action contract as hosted models.

## Existing HAL systems to converge on this fabric

The same interoperability layer should become the common boundary for HAL's
existing orchestration systems rather than maintaining separate one-off bridges.

Targets include:

- AgentZero
- CrewAI
- LangGraph
- AutoGen
- local Ollama models
- OpenCode / coding workers
- Claude Code through bounded MCP
- ChatGPT through bounded MCP
- Livepeer Creative MCP for media/render work
- future remote A2A agents

The goal is **one authority, many workers**.

## Participant manifest

Every external participant should be representable by the public-safe
`hal.agent_world.participant.v0` manifest.

Core fields:

- participant ID and display name
- framework/runtime
- transport
- public capabilities
- protocol versions
- optional public/loopback endpoint
- non-secret metadata

Credential-like metadata keys are rejected.

## High-leverage integration order

1. Finish authenticated Agent World MCP gateway boundaries.
2. Run Muse vs local Ollama through the identical action contract.
3. Add A2A discovery and a reviewed trial-request service.
4. Add OpenAI Agents SDK MCP client example.
5. Add AutoGen MCP Workbench example.
6. Add CrewAI MCP example.
7. Add LangGraph participant example.
8. Add AG-UI spectator event projection.
9. Connect the protocol to the real Godot world.
10. Add a public interoperability harness where outside developers can submit a
    participant adapter and run deterministic evaluation scenarios.

## What not to do

Avoid creating separate canonical worlds for each framework.

Avoid provider-specific scoring.

Avoid direct provider-to-provider secret channels inside scored episodes.

Avoid giving framework plugins arbitrary host shell access merely to join a
simulation.

Avoid claiming compatibility from configuration alone; every integration should
earn a small executable proof and receipt.

## Public interoperability challenge

A useful community milestone is a public **Agent World Interop Challenge**:

- one fixed scenario package;
- official scripted baseline;
- HAL-local reference entrant;
- adapters for at least three external ecosystems;
- randomized seeded slots;
- identical action budgets;
- replay/evidence bundle;
- optional spectator video;
- open adapter template.

This creates a concrete reason for other framework communities to integrate with
HAL instead of only reading about it.
