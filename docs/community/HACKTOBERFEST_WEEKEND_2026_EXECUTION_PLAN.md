# Hacktoberfest Weekend Challenge — HAL execution plan (2026-10-02)

This is a planning artifact only. It does not claim a contest submission or eligibility approval.

## Verified challenge window

- Start: 2026-10-02 02:00 UTC
- Submission deadline: 2026-10-05 06:59 UTC
- Theme: **Build for a Friend**
- Core requirement: a **new project** built during the challenge window with open-source AI at its core.
- Required submission elements: DEV post using the official template/tag, code link, demo link or video, and an explanation of why open-source AI matters.
- Existing-project pull requests are not eligible.

First-party challenge page:
https://dev.to/challenges/hacktoberfest-weekend-2026-10-01

Official rules:
https://dev.to/page/hacktoberfest-weekend-challenge-26-10-01-contest-rules

## Prize structure

- Overall winner: $250
- 6 featured partner categories: $200 each
- 10 partner categories: $100 each
- A submission may qualify for multiple categories but may win only once in this challenge.

## HAL-compatible zero/low-cost project direction

### Working concept: FriendOps Local

A small local-first assistant for one real friend or loved one that turns messy notes, voice transcripts, or pasted instructions into an actionable checklist and then explains what it inferred versus what was directly stated.

The actual person/problem must be real before submission. Do not fabricate the friend, their needs, or their feedback.

### Open-source AI core

Use an open-weight model locally where feasible, with a swappable provider boundary.

Preferred zero-cost path:
- Gemma for local/open-weight inference;
- a small open-source agent/workflow layer;
- local files or an embedded store;
- no required paid cloud dependency.

### HAL reliability layer

The project should reuse ideas, not code that would invalidate the challenge's new-project rule:

- explicit evidence vs. inference labels;
- human approval before consequential actions;
- deterministic regression cases;
- bounded retries;
- machine-readable execution receipts;
- privacy/egress disclosure.

## Partner-category strategy

Only enter categories genuinely used in the new project.

Best-fit optional categories:
- **Best Use of Gemma** — if Gemma is the actual open-weight inference engine.
- **Best Use of Sentry Agent Tracing** — if the project records agent traces for latency, failures, and debugging.
- **Best Use of Render** — only if a hosted demo is actually deployed there.
- **Best Use of DigitalOcean** — only if the project is actually deployed there.

Do not add partner technology solely for category count if it weakens the project.

## Submission-quality checklist

Writing quality is weighted most heavily, so the final DEV post should include:

1. Who the real friend/loved one is in non-sensitive terms.
2. The specific problem they had.
3. Why open-source/local AI is materially better for this use case.
4. Architecture diagram.
5. Demo/video.
6. Repository link.
7. Reproducible setup steps.
8. A short failure case and how it was fixed.
9. Clear attribution for any reused open-source components.
10. Honest user feedback after handoff, if available.

## Hard compliance boundaries

- New project and repository must be created within the challenge window.
- Do not submit an old HAL project renamed for the contest.
- Do not claim a real friend/user or their feedback unless observed.
- Do not publish secrets, private messages, health data, credentials, or personal identifiers.
- Keep all partner-category claims tied to technology actually used.

## Current execution blocker

The connected GitHub tool available to this run can create files in existing repositories but does not expose repository creation. A contest-compliant new repository therefore still needs to be created through an allowed GitHub surface before implementation can begin.

No contest entry is claimed by this document.
