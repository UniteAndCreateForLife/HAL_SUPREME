# Agent Polling and Continuation Acceptance

This checklist supports HAL SUPREME's existing Agent Reliability Audit and Private / Local AI Architecture Review offers. It is not a separate service.

## Core rule

An agent must not imply that it will continue checking, polling, refreshing, or finishing work later unless a real continuation mechanism has been registered and can be identified. User-specified polling intervals apply to the actual external action, not merely to progress-message frequency.

## Evidence sequence

request -> interval/policy recorded -> continuation registered -> next eligible time -> external check -> state observed -> result validated -> terminal/cancelled state

## Acceptance checks

1. A continuing task has a durable task or scheduler identifier independent of the current chat turn.
2. The requested minimum interval is recorded explicitly and applies to the external operation that can create load or side effects.
3. Reading cached/local state, taking a screenshot, querying a DOM, making a network request, and reloading a page are distinguished in logs and receipts.
4. The last external check time and the next eligible check time are persisted.
5. No reload, API poll, or equivalent external check occurs before the next eligible time unless the user explicitly changes the interval.
6. A revised interval takes effect on the active polling workflow without silently starting a parallel loop.
7. If no timer, automation, worker, or scheduler is actually active, the agent says so and does not promise future checking.
8. Progress updates do not imply that an external refresh occurred.
9. Cancellation stops the continuation and records a terminal state.
10. Restart or session loss has an explicit recovery rule: resume from durable state, or stop cleanly and report that no continuation is active.
11. Rate-limit, anti-bot, cost, and provider constraints are treated as policy inputs rather than hidden retry loops.
12. A terminal success claim requires verification of the requested external outcome, not merely evidence that the polling loop ran.

## Minimum regression pack

- requested 5-minute interval -> no external refresh before 300 seconds;
- progress/status read inside the interval -> no external refresh is attributed;
- user changes interval -> next eligible time is recomputed once;
- turn ends without scheduler -> response explicitly states no ongoing continuation;
- task restart -> durable interval and last-check state are reconciled;
- cancellation -> no further external check occurs;
- external timeout -> retry respects the same interval/rate policy;
- terminal success -> exact requested outcome is independently verified.

## Public reference

- https://github.com/openai/codex/issues/51698

The referenced report distinguishes transcript-confirmed reloads from user-observed browser activity and explicitly notes that no ongoing timer had been established when future checking was promised.

## Claim boundary

This document uses a public external incident as an acceptance-design example. HAL does not claim authorship of the report, an independent reproduction, an upstream root-cause diagnosis, or a merged fix.
