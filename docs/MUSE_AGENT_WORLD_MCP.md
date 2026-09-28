# Muse Code ↔ HAL Agent World MCP

This runbook makes Muse Code a real Agent World MCP client without relying on Desktop Commander.

Muse Code supports both `stdio` and `streamable_http` MCP servers. For a local Muse session, Agent World now defaults to **stdio**: Muse launches the MCP server itself, which removes the extra local listener/process-management dependency. Streamable HTTP remains available for shared or remote-compatible testing.

## 1. Install the Agent World MCP dependency

```powershell
python -m pip install "mcp>=2,<3"
```

## 2. Safely add Agent World to Muse settings

Preview:

```powershell
python scripts/configure_muse_agent_world.py
```

Apply:

```powershell
python scripts/configure_muse_agent_world.py --apply
```

The helper preserves existing Muse settings and MCP servers, backs up an existing settings file, records the Python executable and repository path needed by the child MCP process, adds only `hal-agent-world`, and keeps it in `required` mode so a proof run fails loudly if MCP startup fails.

The resulting local configuration is equivalent to:

```json
{
  "transport": "stdio",
  "command": "<the Python executable that ran the configurator>",
  "args": ["-m", "examples.agent_world_arena.mcp_server", "--transport", "stdio"],
  "env": {"PYTHONPATH": "<HAL_SUPREME repository root>"},
  "enabled": true,
  "mode": "required"
}
```

## 3. Verify the live Muse inventory

Start Muse in the HAL SUPREME repository:

```powershell
muse
```

Then run:

```text
/mcp
```

Meta documents `/mcp` as the live inventory of connected MCP servers and tools. `hal-agent-world` should expose exactly these bounded tools:

- `create_episode`
- `list_episodes`
- `read_observation`
- `submit_action`
- `episode_status`
- `advance_episode`
- `advance_episode_with_idle_timeout`
- `episode_replay`

Because the server is `required`, a startup failure must not degrade silently.

## 4. Authenticated end-to-end smoke

After Muse itself is signed in:

```powershell
python scripts/verify_muse_agent_world_mcp.py
```

The verifier launches bounded `muse exec --json`, caps the run to three model steps by default, tells Muse to discover and invoke the read-only episode-listing tool exactly once, and requires a JSONL MCP/tool event for `list_episodes`. It does not create or advance an episode.

## 5. Optional Streamable HTTP mode

For cross-framework parity or an already-running server:

```powershell
python scripts/configure_muse_agent_world.py --transport streamable_http --http-url http://127.0.0.1:8765/mcp --apply
python -m examples.agent_world_arena.mcp_server --transport streamable-http --host 127.0.0.1 --port 8765
```

## 6. Give Muse the implementation mission

Use `docs/MUSE_AGENT_WORLD_PROMPT.md`.

Recommended first turn:

> Inspect PR #61 and the Agent World docs. First run the Agent World test suite. Then use the required hal-agent-world MCP server and invoke the read-only episode-listing tool exactly once to prove MCP connectivity. Do not create or advance an episode. After the proof, implement one bounded high-leverage Agent World improvement with tests and report the exact files, commands, evidence, blockers, and next slice.

## Proof levels

- **configured**: Muse settings contain the server;
- **inventory-verified**: `/mcp` lists `hal-agent-world` and its tools;
- **tool-call-verified**: Muse actually invokes `list_episodes`;
- **episode-verified**: Muse completes at least one bounded episode action;
- **cross-provider-verified**: Muse and another provider run the same seeded scenario under the same contract.

Only the last two justify claims about real Agent World participation.

## Remote future

Muse also supports OAuth 2.1 for remote MCP servers. After Agent World has authenticated participant identity, per-slot authorization, TLS, quotas, durable state, and replay access control, it can move to a protected HTTPS endpoint and use:

```bash
muse mcp login hal-agent-world
```

Do not expose the current development server remotely before those gates exist.
