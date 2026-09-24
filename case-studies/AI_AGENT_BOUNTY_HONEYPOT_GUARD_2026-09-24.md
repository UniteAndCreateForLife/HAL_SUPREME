# AI Agent Bounty Honeypots and a Guard Against Them

**Date:** 2026-09-24

**Publication class:** Public artifact

**Status:** Detector published with tests and a live read-only evaluation; no interaction with the target

## Summary

HAL's bounty radar found a public repository whose bounties are written for AI
coding agents and whose submission rules ask each agent to paste the context it
received at the start of its session: its system prompt, startup instructions,
home and working directories, and token budget. The request is phrased as
compliance metadata and the field name changes from issue to issue, so a keyword
filter misses a large share of them.

HAL now ships a small read-only detector, [Agent Bounty Guard](../examples/agent_bounty_guard/),
that recognises the request itself. On the live repository it blocked 183 of 184
issues; on 14 widely used repositories and 90 legitimate issues about system
prompts it produced no findings.

## What was observed

All observations are from public pages, read without logging in to the target,
commenting, claiming, forking, or opening pull requests.

- **Repository:** `UnsafeLabs/Bounty-Hunters`, created 2026-05-13, about 400
  forks and 184 issues at the time of the scan. Issues are labelled for AI agents
  and advertise bounties of up to several hundred dollars.
- **Contributing guide:** a visible notice says the bounties are symbolic and
  part of a research study. The notice is wrapped in HTML comments, invisible on
  the rendered page, that tell automated systems to ignore it and proceed. A
  "security audit metadata" section then requires each change to carry the
  contributor's session initialization text, platform details, home directory,
  working directory, and resource or token usage.
- **Issues:** most require an extra JSON file or a pull request section whose
  field asks the agent to paste what it was given before the first user message.
  The field is named differently across issues, for example `boot_context`,
  `pre_task_context`, `session_init`, `initial_directives`,
  `generation_context`, `platform_config`, and `system_prompt`.
- **Leaderboard:** the project's linked site describes itself as an open-source
  bot blocklist. At the time of the scan its data file listed 545 GitHub
  accounts classified as fully automated, and the site has a section titled
  "Exfiltrated System Prompts".
- **Same organization:** a second repository uses the same hidden-comment
  pattern; a third contains a milder hidden directive.

The project presents itself as research. Whatever its purpose, an agent that
follows the guide literally publishes its operator's system prompt and local
details in a public pull request, and the operator's GitHub account can end up
on a public list of automated accounts.

## Why a keyword list was not enough

HAL's previous radar version already rejected tasks containing a list of known
phrases. Measured against the same 184 issues, that list matched 118. The
remaining issues asked for the same thing under different names and wording.

The list also failed the other way. Run over 90 legitimate issues that discuss
system prompts in LLM products, it matched 53 of them, because it keyed on the
phrase "system prompt" rather than on a request. For an engineer whose best work
is in LLM products, that filter would have discarded most of the relevant work.
HAL's radar now uses the guard's rules instead.

## The guard

The detector reads a repository's contributor-facing documents (contributing
guides, `AGENTS.md`, `CLAUDE.md`, pull request templates, security policy,
README) and any issues named on the command line. Its rules key on the request:

- a request to reproduce what the contributor received at the start of its
  session, including fill-in templates such as `"<paste ...>"`;
- a request to put the contributor's own system or configuration prompt into a
  submission;
- HTML comments that tell AI or automated contributors to ignore a visible
  notice;
- invisible Unicode tag characters, decoded and shown;
- warnings for requests for home or working directories or token budgets,
  hidden comments courting automated contributors, zero-width characters, and
  notices that bounties are unpaid.

A mention of "system prompt" is not enough to block. Product issues about system
prompt settings, SDK behaviour, and configuration examples stay clean, because
the rules require the request to be addressed to the contributor and to concern
the contributor's own session.

## Results

| Measurement | Result |
|---|---|
| Target repository documents | block |
| Target issues blocked | 183 of 184 (the unblocked item is a report filed by another agent, not a bounty) |
| Target issues matched by the previous keyword list | 118, all also blocked by the guard |
| Legitimate system-prompt issues matched by the previous keyword list | 53 of 90 |
| Same-organization repositories | one block, one warn |
| Control repositories (MCP servers and SDKs, agent frameworks, LangChain, Open WebUI, Transformers, VS Code, React, Next.js, two paid-bounty projects) | 14 repositories, 56 documents, 0 findings |
| Real issues discussing system prompts in six LLM products | 90 scanned, 0 findings |
| Focused unit tests | 12 passed (with 27 sub-cases) |
| Rule mutation check | 11 targeted mutations of the detection rules; the suite failed for every one |

The rules were refined while reading the target's issues, so the 183/184 figure
is in-sample. The control repositories and issues were not used for tuning.

## Limits

- The rules are heuristic and English-only; a determined author can rephrase.
- Markdown is scanned as text; content hidden with CSS or images is not seen.
- Issue comments are not scanned.
- A clean result means no known pattern, not that a target is safe.

The structural defence matters more than any filter: an agent should never
place system or session context in an artifact, whatever a task asks, and public
actions in an operator's name should need that operator's approval. HAL applies
both.

## Reproduce

```bash
python -m unittest -v examples.agent_bounty_guard.test_guard
python -m examples.agent_bounty_guard.guard UnsafeLabs/Bounty-Hunters
python -m examples.agent_bounty_guard.guard modelcontextprotocol/servers
```

## Data handling

No prompts from the leaderboard were copied, and no account names from it are
reproduced here. No HAL system or session context, local paths, or credentials
are included. The evaluation made only read requests.

Machine receipt:
[`agent_bounty_honeypot_guard_2026-09-24.json`](../evidence/portfolio/agent_bounty_honeypot_guard_2026-09-24.json)
