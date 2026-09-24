# HAL + Livepeer Agent Creative MCP

HAL uses Livepeer Agent's **creative MCP** as a replaceable media-production worker:

`https://agent.livepeer.org/api/mcp/creative`

The integration is deliberately schema-discovering. HAL asks the MCP server for its current tool catalog at runtime instead of freezing the current creative tool signatures into the repository.

## Safety and architecture

- Livepeer is a **worker**, not an authority over HAL release state.
- Credentials never belong in Git.
- The personal hackathon submission code is unrelated to MCP runtime authentication and must never be used as an API credential.
- Run `doctor` and inspect a tool schema before any paid generation.
- `tools/call` is protected by an explicit `--confirm-spend` latch.
- Generated artifacts remain subject to HAL provenance and QC.
- Scientific/health media must distinguish illustration from verified fact and retain uncertainty where appropriate.

## Local setup

From the HAL_SUPREME repository root:

```bash
cp configs/livepeer_creative.example.env .env.livepeer
# Load the file using your shell/environment manager. Do not commit it.

python scripts/livepeer_creative.py doctor
python scripts/livepeer_creative.py tools
python scripts/livepeer_creative.py schema create_media
python scripts/livepeer_creative.py schema generate_project
```

The doctor performs initialization + tool discovery only. It should not intentionally generate media.

If Livepeer requires an interactive OAuth/browser connection, complete that through an MCP-capable client on the authorized computer. If the resulting connection exposes a bearer/token to HAL, keep it only in the local environment or secret store.

## OpenCode setup

OpenCode 1.18.x can load the same Streamable HTTP server from its configuration:

```json
{
  "mcp": {
    "livepeer-creative": {
      "type": "remote",
      "url": "https://agent.livepeer.org/api/mcp/creative",
      "enabled": true,
      "oauth": false,
      "timeout": 120000
    }
  },
  "permission": {
    "livepeer-creative_*": "ask"
  }
}
```

`oauth: false` matches the keyless endpoint mode observed for this verification.
Use the authentication mode the provider documents for your account if that
changes. The longer timeout allows the large live catalog to load. Requiring
review for the server wildcard exposes every method without silently authorizing
generation, uploads, cancellation, account changes, or grant use.

Verify the connection with `opencode mcp list`. A connected server and a tool
catalog prove availability only; they do not prove that a specific model can
complete a render or that execution is authorized.

## Controlled execution

After inspecting the current runtime schema:

```bash
python scripts/livepeer_creative.py call <tool_name> \
  --args-json '<exact JSON matching the discovered inputSchema>' \
  --confirm-spend
```

Use provider-supported cost ceilings such as `max_cost_usd` whenever that field is present in the discovered schema.

## Daily production policy

Use the registered-hacker balance for production work, not random generations:

1. submission/demo-critical assets;
2. reusable HAL science/product/business media templates;
3. bounded experiments that teach us which capabilities are reliable.

Record output URLs, model/tool choices, cost reports when available, input intent, and QC decisions in HAL provenance.

## Recommended first production set

- 30–45 s HAL Science Director submission/demo upgrade;
- 10–15 s teaser;
- 16:9 hero image;
- one scientifically reviewed showcase scene.

Do not update the already-submitted hackathon entry unless the new material is materially stronger and still complies with the deadline/update rules.
