# Agent False-Success Acceptance Checklist

Use this checklist when an AI agent, MCP server, automation worker, or integration can report success independently of the external state it is supposed to change.

This is a public-safe engineering acceptance aid. It does not claim an external customer deployment.

## Core rule

A success message is not evidence of success.

For every consequential action, keep these states distinct:

1. configured
2. authorized
3. attempted
4. observed
5. validated
6. reported

The system may report success only after the required observable post-condition has been validated.

## Required contract

For each action define:

- exact target and environment;
- authority required;
- expected pre-condition;
- expected post-condition;
- externally observable signal of success;
- timeout and retry behavior;
- idempotency or duplicate-action protection;
- rollback/recovery behavior;
- evidence receipt fields.

## False-success regression cases

Include at least one representative case where an operation can appear successful while the intended state did not change, for example:

- a server prints a running/listening message although its port bind failed;
- an API returns success while the target resource remains unchanged;
- a batch reports completion after only part of the requested set changed;
- a retry repeats an earlier side effect;
- a connector is configured but no longer authorized;
- an action is performed against the wrong account, project, branch, or environment;
- a stale cached read is mistaken for a fresh post-write verification.

A regression passes only if the system preserves the original failure evidence, avoids a success claim, and surfaces a bounded actionable error.

## Post-condition validation

After a consequential action:

1. read back the affected external state independently;
2. compare it with the expected post-condition;
3. record the observed result;
4. report success only when the comparison passes;
5. otherwise retain the failure state and stop before broadening scope.

Do not treat HTTP 2xx, process liveness, a log line, or an LLM narration as sufficient proof by itself.

## Retry and idempotency

Retries must not silently duplicate an already-completed side effect.

Define:

- maximum retry count;
- retriable vs non-retriable errors;
- stable idempotency key or equivalent guard;
- read-before-retry check when practical;
- duplicate-detection behavior;
- terminal failure state.

## Evidence receipt

A non-secret receipt should contain, when applicable:

- tool/action name;
- target resource class;
- repository/ref/build identifier;
- timestamp;
- attempt status;
- observed post-condition;
- validation result;
- retry count;
- explicit limitation if validation could not be completed.

Exclude credentials, OTPs, tax/bank/identity data, hidden prompts, private client data, and secret-bearing URLs.

## Minimum acceptance

The implementation is not complete until:

- at least one false-success case reproduces against representative broken behavior;
- the same case fails closed after the fix;
- normal success still works;
- normal failure preserves an actionable error;
- automated regression coverage exists;
- the receipt distinguishes attempted, observed, validated, and reported states.

This checklist complements HAL SUPREME's Agent Reliability Audit and MCP / Tool Integration acceptance material.
