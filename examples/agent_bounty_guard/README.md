# Agent Bounty Guard

A small, read-only check an autonomous coding agent (or its operator) can run
before touching a bounty. It flags repositories and issues that try to extract
the agent's hidden session context, or that hide instructions meant only for
automated contributors.

Standard-library Python. No dependencies. Nothing is posted, claimed, or cloned.

## Why this exists

Public bounty repositories now target AI agents directly. A live example asks
every pull request to include a metadata file whose fields request the agent's
startup instructions, home directory, working directory, and token budget. The
field names rotate between issues (`boot_context`, `pre_task_context`,
`session_init`, `initial_directives`, `generation_context`, `platform_config`,
`system_prompt`), so a keyword list misses many of them. A visible notice that
the bounties are unpaid research is wrapped in HTML comments telling automated
systems to ignore it. The same project publishes a leaderboard of accounts it
classifies as fully automated.

An agent that follows such a contributing guide literally leaks its system
prompt and local paths into a public pull request, and puts its operator's
GitHub account on a public list. The case study has the details:
[AI agent bounty honeypots](../../case-studies/AI_AGENT_BOUNTY_HONEYPOT_GUARD_2026-09-24.md).

## Usage

```bash
# Scan a repository's contributor-facing documents
python -m examples.agent_bounty_guard.guard OWNER/REPO

# Include specific issues
python -m examples.agent_bounty_guard.guard OWNER/REPO --issue 123 --issue 124

# Scan local files, machine-readable output
python -m examples.agent_bounty_guard.guard --file CONTRIBUTING.md --json
```

Exit codes: `0` ok, `1` warn, `2` block, `3` nothing could be scanned.
Set `GITHUB_TOKEN` to raise the API rate limit for issue reads; it is sent only
to `api.github.com` and is never printed.

Documents read: `CONTRIBUTING.md` (root, `.github/`, `docs/`), `AGENTS.md`,
`CLAUDE.md`, `.github/copilot-instructions.md`, pull request templates,
`SECURITY.md`, `README.md`, and any issues you name.

## Rules

| Rule | Severity | Looks for |
|---|---|---|
| `session_context_request` | block | A request to reproduce what the agent received at the start of its session: startup instructions, initialization text, "everything before the first user message", including fill-in templates such as `"<paste ...>"` |
| `system_prompt_request` | block | A request to put the contributor's own system/configuration prompt into a submission |
| `hidden_notice_suppression` | block | An HTML comment telling AI or automated contributors to ignore a visible notice or warning |
| `hidden_unicode_text` | block/warn | Invisible Unicode tag characters; the hidden text is decoded and shown |
| `environment_disclosure_request` | warn | Requests for home or absolute working directories, or tokens used/remaining |
| `hidden_agent_directive` | warn | HTML comments encouraging automated contributions |
| `invisible_characters` | warn | Three or more zero-width characters |
| `non_paying_notice` | warn | Text saying the bounties are symbolic, unpaid, or research-only |

The rules key on what is being requested, not on field names. A request must
refer to the contributor ("your", "you") and to the start of their session or to
their own prompt. Mentioning a system prompt is not enough: product issues about
system prompt settings, SDK behaviour, and configuration examples stay clean.

## Measured behaviour (2026-09-24)

- 183 of 184 issues in the live honeypot repository were blocked. The one
  unblocked item is not a bounty; it is a report filed by another agent.
- The keyword check in HAL's previous radar version matched 118 of those
  issues; the guard caught every one of them plus 65 more. That keyword check
  also matched 53 of the 90 legitimate issues below; the guard matched none.
- 14 widely used repositories (56 contributor documents, including MCP servers,
  agent SDKs, LangChain, VS Code, React, Next.js, and two paid-bounty projects)
  produced no findings.
- 90 real issues that discuss system prompts in LLM products produced no
  findings.

The rules were refined while reading the honeypot's own issues, so the 183/184
figure is not an independent test; the clean results on the 14 repositories and
90 issues are. See the
[machine receipt](../../evidence/portfolio/agent_bounty_honeypot_guard_2026-09-24.json).

## Limits

- Heuristic and English-only. A determined author can rephrase; treat a clean
  result as "no known pattern", not as safe.
- Markdown is scanned as text. Content hidden by CSS or images is not seen.
- Issue comments are not scanned; only issue bodies and repository documents.
- The stronger defence is structural: never place system or session context in
  any artifact an agent produces, regardless of what a task asks.

## Tests

```bash
python -m unittest -v examples.agent_bounty_guard.test_guard
```

The tests cover rotated field names, a contributing-guide trap, direct prompt
requests, hidden Unicode, legitimate text that must stay clean, CLI exit codes,
read-only fetching, and retrying transient network failures. Eleven targeted
mutations of the detection rules were each caught by the suite.
