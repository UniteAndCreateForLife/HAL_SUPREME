# HAL Science Director

**Hackathon target:** Atumera Livepeer Agent Hackathon 2026 — Livepeer Agent Builder / Innovation Track.

HAL Science Director is a steerable scientific-media workflow. A user describes a scientific concept, then Livepeer Agent is used twice in the core path:

1. **Science shot planning** — a Livepeer `gemini-text` capability turns the brief into an explicit observable claim, camera/environment plan, exclusions, accuracy guardrails, and render prompt.
2. **Media generation** — a Livepeer image or video capability renders the planned shot. Video jobs are polled through the Livepeer Agent MCP until the artifact is ready.
3. **Human correction loop** — the operator can add scientific feedback; the next attempt replans with those corrections rather than starting from scratch.
4. **Provenance receipt** — each run records the plan, exact render prompt, capabilities used, output reference, and a SHA-256 provenance hash.

The product direction matches HAL SUPREME's larger production doctrine: AI workers may generate media, but a visible plan, user correction, provenance, and quality gate remain first-class.

## Why this is distinct

Most generative media demos optimize for spectacle. Science Director optimizes for **reviewable scientific communication**: the planner must state what claim is being shown, what is illustrative rather than literal, what must be excluded, and how operator feedback changes the next attempt.

The workflow is deliberately small enough to demonstrate live in a few minutes while still exposing the full generate → review → correct → regenerate loop.

## Run

Requires Node.js 20+.

```bash
cp .env.example .env
set -a; . ./.env; set +a
npm start
```

Open `http://localhost:8787`.

By default the server points at `https://agent.livepeer.org/api/mcp`. If Livepeer's keyless demo is enabled, `LIVEPEER_MCP_BEARER` may be left empty. For normal authenticated use, place the Daydream/Livepeer bearer in the environment; it is never sent to the browser or committed to Git.

## Validation

```bash
npm test
npm run check
```

## Architecture

Browser → HAL server → Livepeer Agent MCP → `gemini-text` planner → `run_capability` media render → `get_create_media` polling for async video → browser review → feedback → next Livepeer-planned attempt.

The integration intentionally uses the current Livepeer Agent MCP endpoint rather than calling a media vendor directly. That keeps Livepeer Agent central to both reasoning and media production.

## Security / privacy

- Bearer credentials stay server-side.
- Error messages redact bearer-like values.
- Runtime run history is in-memory in this prototype and is not committed.
- No hidden prompts, credentials, machine paths, or private chain-of-thought are written to provenance receipts.

## License

Apache-2.0, consistent with the HAL SUPREME repository direction.
