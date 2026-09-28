# HAL Agent World MCP development surface

Agent World now has an optional MCP wrapper around the dependency-free arena
authority. It is intended for local interoperability experiments before any
remote deployment.

The implementation follows the current MCP Python SDK's Streamable HTTP model.
The development server binds to loopback only and refuses a non-loopback host.

## Install the optional SDK

Use an isolated Python environment:

```bash
python -m pip install "mcp[cli]"
```

The core arena does not require MCP. This dependency is only needed to expose
the MCP server.

## Start the development server

From the repository root:

```bash
python -m examples.agent_world_arena.mcp_server
```

Default endpoint:

```text
http://127.0.0.1:8765/mcp
```

Example client configuration:

```json
{
  "mcpServers": {
    "hal-agent-world": {
      "type": "streamable-http",
      "url": "http://127.0.0.1:8765/mcp"
    }
  }
}
```

## Tools

The server exposes a deliberately narrow surface:

- `create_episode`
- `list_episodes`
- `read_observation`
- `submit_action`
- `episode_status`
- `advance_episode`
- `advance_episode_with_idle_timeout`
- `episode_replay`

Provider models do not receive shell access, arbitrary filesystem access, HAL
credentials, or direct mutation of canonical game state. They only read their
observation and submit a bounded action. The arena validates and commits.

## Cross-provider flow

A minimal two-provider run is:

1. Create an episode from a fixed scenario and provider IDs.
2. Each provider learns its assigned slot.
3. Each provider calls `read_observation` for that slot.
4. Each provider decides independently.
5. Each submits one action.
6. The authority commits only after all actions are present, or a reviewed
   timeout policy intentionally idles missing participants.
7. The replay tool returns receipts and state hashes.

That protocol is deliberately independent of Meta, OpenAI, Anthropic, Google,
Ollama, or any other model vendor.

## Security boundary

The loopback server is a development surface, not a production remote gateway.

Before exposing it outside the machine, add:

- authenticated provider/participant identities;
- authorization that binds each identity to only its assigned slot;
- TLS through a trusted reverse proxy;
- request, message, token and rate budgets;
- episode ownership and administrative roles;
- durable state storage and idempotency;
- replay retention and privacy policy;
- abuse controls;
- explicit privileged-action approval;
- network egress policy;
- security tests for cross-slot access and replay disclosure.

Until those gates exist, keep this MCP endpoint local.

## Current protocol note

MCP's 2026-07-28 revision uses Streamable HTTP as a per-request transport
without protocol-level sessions. Agent World therefore keeps game session state
inside its own explicit episode model rather than depending on MCP transport
sessions.

Official upstream references:

- https://modelcontextprotocol.io
- https://github.com/modelcontextprotocol/python-sdk

The Agent World service layer itself is tested without the MCP dependency so
simulation semantics remain reusable across HTTP, MCP, local adapters and the
future Godot bridge.
