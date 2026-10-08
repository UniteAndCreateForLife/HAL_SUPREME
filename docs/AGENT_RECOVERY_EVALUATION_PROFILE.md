# Agent Recovery Evaluation Profile

This document defines a small, reproducible way to use HAL's existing headless evidence recorder for agent-recovery evaluation.

It is intentionally narrower than a general reliability claim. One successful run proves one successful run.

## Why this exists

Current agent-evaluation practice increasingly separates three questions:

1. Did a failure actually occur?
2. Did the agent restore progress?
3. Did the final environment state satisfy the task?

Execution traces are useful evidence, but a trace alone does not prove the final state. Recovery should be verified independently and measured across repeated trials.

References:
- Hugging Face: Using Execution Traces to Evaluate AI Agent Behavior
- Hugging Face: Measuring Agent Recovery
- Hugging Face: How to Evaluate AI Agents

## HAL evidence boundary

This profile can use the public evidence components already present in this branch:

- hash-chained evidence sessions;
- process/headless event capture;
- artifact SHA-256 registration;
- explicit validation events;
- clearly labeled telemetry replay;
- secret/path sanitization.

These facilities record observable execution. They do not expose or claim hidden reasoning.

## Minimal recovery fixture

A public recovery fixture should declare:

- exact source commit;
- harness/evaluator revision;
- task identifier;
- deterministic injected failure;
- expected final state;
- independent final-state validator;
- maximum attempts or recovery budget.

For each trial, retain:

- failure observed: yes/no;
- recovery attempted: yes/no;
- recovery verified: yes/no;
- task ultimately passed: yes/no;
- additional tool calls after failure;
- elapsed recovery time;
- artifact/report hashes.

## Metrics

For a fixed task and failure class:

- **failure incidence** = eligible failure episodes / trials;
- **verified recovery rate** = verified recovered episodes / eligible failure episodes;
- **final task success rate** = validated successful trials / trials;
- **median recovery effort** = median additional tool calls among eligible failure episodes;
- **median recovery time** = median elapsed time from failure to verified progress restoration.

Report unresolved failure episodes in effort statistics rather than dropping them.

## Repeated-trial rule

Do not describe a single successful recovery as a reliability rate.

For an initial public canary, run at least five identical trials under the same source revision, evaluator revision, task fixture, failure injection, and acceptance criteria.

If the model/provider is nondeterministic, say so and report every trial.

## Public-safe receipt

A promoted receipt should include only public-safe metadata:

```json
{
  "schema": "hal.agent-recovery-eval.v1",
  "source_commit": "<sha>",
  "harness_revision": "<version-or-sha>",
  "task_id": "<fixture-id>",
  "trial_count": 5,
  "eligible_failure_episodes": 5,
  "verified_recovered_episodes": 0,
  "validated_successful_trials": 0,
  "median_recovery_tool_calls": null,
  "median_recovery_seconds": null,
  "raw_report_sha256": "<digest>",
  "limitations": []
}
```

Do not publish credentials, private payloads, hidden prompts, account identifiers, or machine-local operational paths.

## Acceptance for the first HAL canary

The first public recovery canary is complete only when:

- the failure injection is deterministic;
- the same fixture is run at least five times;
- the final state is checked independently of the agent message;
- every trial is retained, including failures;
- the raw report is hashed;
- the public receipt states explicit limitations;
- the result is tied to an exact source revision.

This profile measures one bounded recovery behavior. It does not establish general agent reliability, security certification, or production readiness.
