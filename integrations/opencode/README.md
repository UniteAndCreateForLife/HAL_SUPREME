# HAL × OpenCode runtime adapter

This directory turns OpenCode into a bounded HAL engineering worker through OpenCode's HTTP API. It complements the repository-level `AGENTS.md` contract and the project commands under `.opencode/`.

## Boundary

The adapter intentionally exposes only:

- health checks;
- V2 session creation at an explicit working directory;
- durable prompt admission;
- wait-for-idle;
- context reads;
- active-session reads;
- interrupt.

It does **not** expose OpenCode's shell endpoint, permission-approval endpoints, config mutation, provider credential operations, delete/revert operations, or arbitrary remote hosts by default.

The point is to make OpenCode productive inside HAL without silently turning it into an unrestricted control plane.

## Start OpenCode locally

Protect the service even on loopback:

```powershell
$env:OPENCODE_SERVER_PASSWORD = "<set-in-your-shell-not-in-git>"
opencode serve --hostname 127.0.0.1 --port 4096
```

OpenCode's server defaults to loopback and supports HTTP Basic auth through `OPENCODE_SERVER_PASSWORD`. The HAL adapter reads the same environment variable and never writes it to receipts or command output.

Check connectivity:

```powershell
python -m integrations.opencode.worker health
```

## Run a bounded HAL task

```powershell
python -m integrations.opencode.worker run `
  --directory D:\\HAL_SUPREME `
  --mode fix `
  --task "Find the smallest high-impact reliability defect, add regression coverage, implement the fix, and verify it."
```

Supported modes are `plan`, `fix`, `review`, and `verify`. The adapter asks the OpenCode session to read `AGENTS.md` and the corresponding project command before executing.

The CLI prints only the session ID, mode, and context-message count after completion. It does not dump the full conversation into logs by default.

## Python integration

```python
from integrations.opencode import OpenCodeClient

client = OpenCodeClient()
result = client.run_hal_task(
    directory=r"D:\\HAL_SUPREME",
    mode="review",
    task="Review the current diff for regressions and missing tests.",
)
print(result["session_id"])
```

## Remote servers

Remote OpenCode URLs are rejected by default. A future HAL gateway can deliberately opt in to `allow_remote=True` only after it adds transport security, an authenticated trust boundary, and an explicit remote-worker policy. Do not solve remote access by binding an unauthenticated OpenCode service to `0.0.0.0`.

## API contract

The adapter targets OpenCode V2 session routes:

- `POST /api/session`
- `POST /api/session/:sessionID/prompt`
- `POST /api/session/:sessionID/wait`
- `GET /api/session/:sessionID/context`
- `GET /api/session/active`
- `POST /api/session/:sessionID/interrupt`

Health uses `GET /global/health`.

OpenCode publishes its current OpenAPI specification at the running server's `/doc` endpoint. When OpenCode changes its protocol, update the adapter against that contract and keep the regression tests pinned to the expected request shapes.
