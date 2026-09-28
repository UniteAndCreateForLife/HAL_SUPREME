# Muse Code ↔ HAL Agent World MCP

This runbook makes Muse Code a real Agent World MCP client without relying on Desktop Commander.

Muse Code currently supports MCP servers declared in `~/.config/muse/settings.json` using either `stdio` or `streamable_http`. For Agent World we use Streamable HTTP so Muse connects to the same provider-neutral server as other frameworks.

## 1. Install the Agent World MCP dependency

```powershell
python -m pip install "mcp>=2,<3"
```

## 2. Safely add Agent World to Muse settings

Preview the merge first:

```powershell
python scripts/configure_muse_agent_world.py
```

Apply it:

```powershell
python scripts/configure_muse_agent_world.py --apply
```

The helper preserves existing Muse settings and MCP servers, creates a backup before modifying an existing file, adds only `hal-agent-world`, and keeps it in `required` mode so proof runs fail loudly when the server cannot connect.

Expected server configuration:

```json
{
  "transport": "streamable_http",
  "url": "${HAL_AGENT_WORLD_MCP_URL}",
  "enabled": true,
  "mode": "required"
}
```

## 3. Set the MCP URL

```powershell
$env:HAL_AGENT_WORLD_MCP_URL = "http://127.0.0.1:8765/mcp"
```

## 4. Start Agent World MCP

```powershell
python -m examples.agent_world_arena.mcp_server --transport streamable-http --host 127.0.0.1 --port 8765
```

The server intentionally refuses non-loopback HTTP exposure.

## 5. Verify Muse sees the server

Start Muse from the HAL SUPREME workspace:

```powershell
muse
```

Inside Muse run:

```text
/mcp
```

The live inventory should show `hal-agent-world` and these bounded tools:

- `create_episode`
- `list_episodes`
- `read_observation`
- `submit_action`
- `episode_status`
- `advance_episode`
- `advance_episode_with_idle_timeout`
- `episode_replay`

If the required server cannot start, Muse should abort the run instead of silently continuing without the integration.

## 6. Run the authenticated end-to-end smoke

After Muse Code itself is signed in, run:

```powershell
python scripts/verify_muse_agent_world_mcp.py
```

This starts the local MCP server unless one is already supplied, launches bounded headless Muse Code, caps the run to three model steps by default, asks Muse to invoke only `list_episodes`, checks JSONL output for MCP/tool evidence, and terminates the temporary server.

The probe does not create or advance an episode.

## 7. Give Muse the implementation mission

Use `docs/MUSE_AGENT_WORLD_PROMPT.md`.

A shorter first prompt is:

> Inspect PR #61 and the Agent World docs. First run the Agent World test suite. Then use the hal-agent-world MCP server and call list_episodes exactly once to prove MCP connectivity. Do not create or advance an episode. After the proof, audit the Godot-bridge and cross-framework next steps, implement one bounded improvement with tests, and report the exact files, commands, evidence, blockers, and next highest-leverage slice.

## Proof levels

- **configured**: Muse settings contain the server;
- **listener-reachable**: Agent World MCP answers locally;
- **inventory-verified**: Muse `/mcp` lists the server/tools;
- **tool-call-verified**: Muse actually invokes an Agent World tool;
- **episode-verified**: Muse completes at least one bounded episode action;
- **cross-provider-verified**: Muse and another provider run the same seeded scenario under the same contract.

Only the last two justify claims about real Agent World participation.

## Remote future

Muse Code also supports OAuth 2.1 for remote MCP servers. When Agent World gains authenticated remote participant identities, slot authorization, TLS, quotas, and durable state, the local URL can be replaced with a protected `https://.../mcp` endpoint and Muse can authenticate with:

```bash
muse mcp login hal-agent-world
```

Do not expose the current development server remotely before those gates exist.
