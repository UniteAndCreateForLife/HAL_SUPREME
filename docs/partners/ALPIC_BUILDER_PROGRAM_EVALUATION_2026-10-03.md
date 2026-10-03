# Alpic Builder Program Evaluation — HAL SUPREME

Date: 2026-10-03

## Status

Public-safe evaluation profile only.

This document does **not** claim an Alpic partnership, accepted application, production deployment, customer implementation, paid plan, or endorsement.

## First-party program facts

Alpic's Builder Program currently advertises:

- eligibility for agencies building MCP / ChatGPT Apps for clients and startups shipping their own apps;
- six months of the Business plan free;
- $10,000 in delivery credits;
- MCP-native hosting and observability;
- open-source Skybridge tooling;
- app audit / store-readiness tooling;
- dedicated onboarding/support;
- co-marketing opportunities and early product access.

Program page:
https://alpic.ai/partners

## HAL service mapping

### 1. MCP / Tool Integration

Use Alpic only behind a bounded integration contract:

- explicit authentication boundary;
- typed tool inputs/outputs;
- read/write authority separation;
- deterministic failure handling;
- human approval for protected actions;
- provider-neutral operating notes.

### 2. Agent Reliability Audit

Evaluate:

- auth failures;
- unavailable tools;
- timeouts;
- malformed/partial results;
- duplicate/retry behavior;
- tool-call latency;
- observable completion versus model-reported success.

### 3. Evidence & Citation Validation Harness

For any tool that returns factual business data:

- keep supported, inferred, conflicting, unresolved and unavailable states distinct;
- reject unsupported specifics;
- capture machine-readable receipts;
- preserve source/provenance metadata where available.

### 4. Private / Local AI Architecture Review

Define:

- what data may leave local systems;
- what must never enter model prompts;
- provider and hosting boundaries;
- fallback behavior;
- what can remain local versus use hosted Alpic infrastructure.

## Proposed synthetic proof

Use only synthetic or public-safe test data.

Suggested first proof:

1. deploy one small MCP app with two read-only tools and one protected write-like simulation;
2. validate schema and authentication behavior;
3. induce auth, timeout, malformed-result, and partial-completion failures;
4. ensure protected actions cannot proceed without human approval;
5. record configured -> authorized -> attempted -> observed -> validated -> reported;
6. rerun a small regression set after any tool/schema change;
7. publish sanitized receipts and operating notes only.

## Promotion gate

Do not place Alpic-hosted tools into a consequential production path until:

- the synthetic regression set passes;
- auth and permission boundaries are verified;
- fail-closed behavior is demonstrated;
- protected actions remain human-gated;
- any model/tool version change reruns the acceptance suite.

## Claim boundary

HAL SUPREME's public evidence is primarily self-operated engineering evidence. It should not be represented as third-party customer production deployment where that has not been established.
