# Meta Muse / Model API setup for HAL Agent World

This runbook keeps provider credentials out of Git while wiring Muse Spark into
the same Agent World contract used by other workers.

## Current provider facts

As of 2026-09-27, Meta Model API is in public preview with Muse Spark 1.3.
Meta documents an OpenAI-compatible base URL at:

https://api.meta.ai/v1

The Agent World adapter uses the Chat Completions endpoint and Meta's structured
JSON output support so a Muse worker can return exactly one bounded arena action.

Official references:

- https://dev.meta.ai/products/meta-model-api
- https://dev.meta.ai/docs/quickstart
- https://dev.meta.ai/docs/cookbook/structured-output
- https://dev.meta.ai/docs/cookbook/quickstart-chat-completions

## Account / sign-in

1. Open the Meta Model API page and choose **Start building** or **Sign up**.
2. Sign in to the Meta developer account you want associated with HAL.
3. Create a Model API key from the dashboard if you want direct API access.
4. Do not paste that key into GitHub issues, source files, chat transcripts,
   replay files, screenshots, or public receipts.

Meta's quickstart also documents Muse Code. On Windows, the documented installer
is:

```powershell
irm https://dev.meta.ai/install.ps1 | iex
```

Then run:

```powershell
muse
```

On first run, Muse Code can use browser sign-in or an API key.

## HAL environment variable

The public adapter reads the secret from `MODEL_API_KEY` when using
`MetaMuseAdapter.from_environment()`.

For a temporary PowerShell session:

```powershell
$env:MODEL_API_KEY = "<your key>"
```

Prefer an OS or HAL secret store for durable use. Never commit the value.

## No-spend verification first

The public tests use a fake transport and do not call Meta or consume provider
tokens:

```powershell
python -m unittest -v tests.test_agent_world_meta_muse
```

The full Agent World contract suite is:

```powershell
python -m unittest -v tests.test_agent_world_arena tests.test_agent_world_meta_muse tests.test_agent_world_schemas
```

## Live trial gate

Do not perform a live provider call until all of the following are true:

- the API key exists only in a private secret surface;
- the local contract tests pass;
- the scenario manifest is fixed;
- the per-run token/cost ceiling is defined;
- provider identity has been randomized to an arena slot;
- the operator explicitly approves the live run.

The first live experiment should use the small `resource-rush-v0` scenario,
not the 3D game. Once the provider contract is proven, the same adapter can be
connected to the bounded Godot bridge.

## Pricing note

Model API is metered. Meta currently lists separate standard and contributor
tiers; contributor-tier inputs may be used to improve Meta products. Choose the
tier deliberately and do not treat public-preview access as unlimited free
compute.
