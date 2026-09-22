# HAL Science Director

**Hackathon target:** Atumera Livepeer Agent Hackathon 2026 — **Track 1: Livepeer Agent Builder**.

HAL Science Director is a steerable scientific-media workflow for producing scientific visuals that can critique themselves before a human accepts them. Livepeer Agent is central to the complete loop:

1. **Science shot planning** — Livepeer `gemini-text` converts the operator brief into an explicit observable claim, camera/environment plan, exclusions, accuracy guardrails, and render prompt.
2. **Media generation** — a Livepeer image or video capability renders the planned shot. Async video jobs are polled through Livepeer Agent until the artifact is ready.
3. **Independent visual science review** — a second Livepeer multimodal `gemini-text` pass receives the rendered artifact by `source_url`, scores visible scientific fidelity, identifies concrete errors, and proposes a correction.
4. **Human correction loop** — the operator can accept or edit the judge correction and regenerate; the next attempt replans with that feedback rather than starting from scratch.
5. **Provenance receipt** — each run records the plan, exact render prompt, Livepeer capabilities, review result, output reference, and a SHA-256 provenance hash.

This follows HAL SUPREME's production doctrine: generation is not acceptance. AI workers may create media, but visible plans, independent quality gates, operator correction, and provenance remain first-class.

## Why this is distinct

Most generative-media demos optimize primarily for spectacle. Science Director optimizes for **reviewable scientific communication**. It makes the intended claim explicit, separates illustrative abstractions from literal science, exposes constraints, evaluates the actual pixels after rendering, and turns visible failures into the next production instruction.

A real CI run demonstrated the value of that gate: the Livepeer renderer produced a dramatic Saturn-rings image, while the independent Livepeer reviewer scored it **6/10 — revise** because the rings appeared too thick, major divisions were insufficiently defined, and density banding was weak. The system generated a specific correction rather than silently passing the artifact.

## Run

Requires Node.js 20+.

```bash
cp .env.example .env
set -a; . ./.env; set +a
npm start
```

Open `http://localhost:8787`.

By default the server points at `https://agent.livepeer.org/api/mcp`. If Livepeer's keyless demo is available, `LIVEPEER_MCP_BEARER` may be left empty. For authenticated use, place the Livepeer bearer in the server environment; it is never sent to the browser or committed to Git.

## Validation

Local:

```bash
npm test
npm run check
```

Public CI additionally performs a **real keyless Livepeer smoke test**:

`gemini-text planner → flux-schnell render → gemini-text visual science judge`

The workflow preserves the real rendered JPEG and JSON receipt as a GitHub Actions artifact. The latest verified run passed **8/8 tests**, syntax checks, real planning, real rendering, real multimodal review, and evidence upload.

## Architecture

Browser → HAL server → Livepeer Agent MCP → `gemini-text` planner → Livepeer media render → `gemini-text` visual science judge → browser review → operator correction → next Livepeer-planned attempt.

The integration deliberately uses Livepeer Agent for planning, generation, and artifact review rather than calling a media vendor directly. Livepeer Agent is therefore part of the product's control loop, not a cosmetic API wrapper.

## Security / privacy

- Bearer credentials stay server-side.
- Error messages redact bearer-like values.
- Runtime run history is in-memory in this prototype and is not committed.
- No hidden prompts, credentials, machine paths, or private chain-of-thought are written to provenance receipts.

## License

Apache-2.0, consistent with the HAL SUPREME repository direction.
