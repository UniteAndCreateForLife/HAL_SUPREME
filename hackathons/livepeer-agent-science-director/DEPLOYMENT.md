# Production deployment

HAL Science Director is a single-process Node.js service and can be deployed without a database.

## Container contract

- Runtime: Node.js 22 Alpine
- Service port: `PORT` (defaults to `8787`)
- Health check: `GET /api/health`
- Livepeer endpoint: `LIVEPEER_MCP_URL` (defaults to `https://agent.livepeer.org/api/mcp`)
- Optional authentication: `LIVEPEER_MCP_BEARER`
- No secrets are required in the browser.

The included `Dockerfile` runs the service as the unprivileged `node` user and includes an application-level health check.

## Railway

Deploy the repository branch `hackathon/livepeer-science-director` with the service root directory:

```
/hackathons/livepeer-agent-science-director
```

Recommended service settings:

```
Dockerfile: Dockerfile
Health check: /api/health
Restart policy: ON_FAILURE
```

The application binds to `0.0.0.0` and reads Railway's injected `PORT` automatically.

## Production verification

After deployment:

```bash
curl -fsS https://<public-domain>/api/health
```

Expected response includes `"ok":true` and the active Livepeer authentication mode.

Then perform one image generation in the browser and confirm the complete control loop is visible:

```
Livepeer planner -> Livepeer render -> Livepeer visual science judge -> operator correction -> provenance receipt
```

Do not add bearer tokens, submission access codes, or other credentials to Git.
