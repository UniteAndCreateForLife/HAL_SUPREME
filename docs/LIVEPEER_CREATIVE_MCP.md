# HAL + Livepeer Agent Creative MCP

HAL uses Livepeer Agent's **creative MCP** as a replaceable media-production worker:

`https://agent.livepeer.org/api/mcp/creative`

The integration is deliberately schema-discovering. HAL asks the MCP server for its current tool catalog at runtime instead of freezing the current creative tool signatures into the repository.

## Safety and architecture

- Livepeer is a **worker**, not an authority over HAL release state.
- Credentials never belong in Git.
- The personal hackathon submission code is unrelated to MCP runtime authentication and must never be used as an API credential.
- A keyless/demo MCP connection proves catalog availability only. It does **not** prove an authenticated account, a sponsored balance, a grant, or zero-spend production capacity.
- Run `doctor` and inspect a tool schema before any generation.
- `tools/call` is protected by an explicit `--confirm-spend` latch.
- Do not execute media-producing or otherwise spend-capable tools until the authenticated account identity and the current provider price/cap/balance have been independently verified.
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
complete a render, that execution is authorized, or that any observed demo
allowance belongs to a sponsored account.

## Router admission contract

The HAL compute router treats the Livepeer worker as fail-closed by default:

```text
HAL_PROVIDER_LIVEPEER_CREATIVE_ENABLED=false
HAL_PROVIDER_LIVEPEER_CREATIVE_AUTHENTICATED=false
HAL_PROVIDER_LIVEPEER_CREATIVE_ZERO_SPEND_READY=false
HAL_PROVIDER_LIVEPEER_CREATIVE_SPONSORSHIP_VERIFIED=false
```

- `AUTHENTICATED=true` requires independently verified account identity.
- `ZERO_SPEND_READY=true` requires current price/cap/balance evidence showing the intended workload can execute without paid overage.
- `SPONSORSHIP_VERIFIED=true` requires authenticated provider evidence explicitly identifying the balance as sponsored/grant-funded. Keyless/demo allowance is never enough.
- The router will not admit Livepeer media work unless both `AUTHENTICATED` and `ZERO_SPEND_READY` are true.

## Controlled execution

After inspecting the current runtime schema and verifying the authenticated account plus current cap/balance:

```bash
python scripts/livepeer_creative.py call <tool_name> \
  --args-json '<exact JSON matching the discovered inputSchema>' \
  --confirm-spend
```

Use provider-supported cost ceilings such as `max_cost_usd` whenever that field is present in the discovered schema.

## Production policy

Do not use the current keyless/demo connection for production merely because it exposes tools or a demo allowance. When an authenticated account balance is independently verified and the workload is inside a current zero-spend cap, prioritize:

1. submission/demo-critical assets for the canonical revenue pipeline;
2. reusable HAL science/product/business media templates;
3. bounded experiments that teach us which capabilities are reliable.

Record account class (without credentials), output URLs, model/tool choices, cost reports when available, input intent, and QC decisions in HAL provenance. Record sponsored/grant status only when provider evidence explicitly proves it.

## Recommended first production set after admission

- 30–45 s high-value demo upgrade for the currently selected canonical revenue workstream;
- 10–15 s teaser;
- 16:9 hero image;
- one scientifically reviewed showcase scene.

Do not update already-submitted entries unless the canonical bounty/revenue loop explicitly owns and requests that change.
