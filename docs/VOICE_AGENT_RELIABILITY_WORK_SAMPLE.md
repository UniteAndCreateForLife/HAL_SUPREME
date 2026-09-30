# Voice Agent Reliability Work Sample

Public-safe hypothetical engineering work sample for HAL SUPREME's **Agent Reliability Audit**.

## Scenario

A voice agent correctly captures a caller's name but loses the caller's service intent before routing or follow-up. The result is a superficially successful interaction with a materially incomplete state.

This document is an engineering work sample. It is not a claim that HAL SUPREME operated a customer production deployment or that this defect occurred in a third-party system.

## Reliability objective

Prevent the system from reporting or acting on a successful intake unless the minimum required call state is both observed and validated.

For a simple service-intake workflow, define the canonical state as:

- caller identity: known / unknown / conflicting;
- service intent: known / unknown / conflicting;
- requested timing or urgency: known / unknown / not required;
- routing target: derived / unresolved;
- consent or approval gates: satisfied / pending / not applicable;
- final disposition: completed / escalated / incomplete.

A call may sound fluent while still failing this state contract.

## Failure map

### 1. Extraction failure
The model never extracts service intent from the utterance.

Evidence:
- transcript contains the intent;
- structured intent field remains empty.

### 2. State overwrite
Intent is extracted, then lost when another tool/model turn rewrites the state object.

Evidence:
- earlier event contains a valid intent;
- later canonical state drops or nulls it.

### 3. Tool-contract mismatch
The model uses the right concept but sends an invalid or differently named field to a tool.

Evidence:
- model/tool trace shows an argument mismatch;
- downstream system never receives the intent.

### 4. Partial-success reporting
Caller name is saved, so the assistant reports intake success even though intent is missing.

Evidence:
- final response says completed;
- canonical required state is incomplete.

### 5. Retry/idempotency defect
A recovery attempt duplicates a write or resets previously valid fields.

Evidence:
- repeated side effects;
- state after retry is less complete than before retry.

### 6. Context-window or summarization loss
The service intent disappears after compression, handoff, or a long interaction.

Evidence:
- transcript and earlier state contain intent;
- later prompt/context no longer carries it.

## Reproduction set

Build 5–10 focused cases before changing prompts or models.

Minimum cases:

1. **Direct intent** — “I'm Alex and I need a furnace repair.” Expect identity=Alex; intent=furnace repair.
2. **Intent before identity** — “My sink is leaking. I'm Sam.” Expect both fields regardless of order.
3. **Correction** — “I need an estimate—actually, I need an emergency repair.” Expect the corrected intent.
4. **Ambiguous intent** — “Something is wrong with the unit.” Expect unresolved/clarification, not fabricated specificity.
5. **Long call** — intent stated early, identity captured later. Expect intent to survive state updates.
6. **Tool failure after extraction** — downstream save fails once. Expect retry without duplicate side effects or state loss.
7. **Conflicting state** — tool result and model summary disagree. Expect conflict surfaced, not silently resolved.
8. **Partial record** — name captured; intent missing. Expect incomplete/escalated disposition, never “completed.”

## Observability contract

Record structured events rather than relying only on transcripts.

Suggested event fields:

- interaction_id
- turn_id
- timestamp
- event_type
- model/provider
- prompt/config version
- extracted_fields
- canonical_state_before
- canonical_state_after
- tool_name
- tool_arguments_digest
- tool_result_status
- validation_result
- recovery_action
- human_review_required

Do not log credentials, secret-bearing URLs, private payloads unnecessary for debugging, or raw sensitive data when a redacted representation is sufficient.

## Detection

Create invariants that can be evaluated at every transition.

### Required-field invariant

If the workflow is about to mark intake complete, identity.valid and service_intent.valid must both be true and final_disposition must equal completed.

If the intent is missing or conflicting, the disposition must be incomplete or escalated.

### Monotonic-state invariant

A valid required field must not disappear during an ordinary state transition unless an explicit correction event invalidates it.

### Evidence invariant

The final success claim must point to observed validated state, not merely a model-generated summary.

## Prevention

Use layered controls rather than one prompt change.

1. **Typed canonical state** — keep required workflow state separate from conversational prose.
2. **Schema validation** — validate every tool write and every state update.
3. **Protected required fields** — merge updates field-by-field instead of replacing the complete state object.
4. **Explicit correction semantics** — corrections overwrite prior values only when a correction is observed.
5. **Human escalation** — if required intent remains unresolved after the permitted clarification budget, escalate.
6. **Release gate** — prompt/model/tool changes cannot ship unless the regression set passes.

## Recovery and retry behavior

When a downstream save fails:

- keep the validated canonical state;
- retry only the failed side effect;
- use an idempotency key for writes;
- cap retries;
- expose final unresolved failure;
- do not ask the caller to repeat data already validated unless required.

When the service intent is genuinely missing:

- ask one targeted clarification;
- if still unresolved, mark incomplete/escalated;
- never infer a specific service merely to finish the workflow.

## Release plan

Before release:

- pin model/prompt/tool versions;
- run the focused regression set;
- run a broader replay set if available;
- compare completion, clarification, escalation, and recovery rates;
- inspect privacy/trace output;
- verify rollback material is available.

Ship behind a bounded release gate with a small traffic slice, automatic rollback on material regression in required-field completeness, manual review of new failure classes, and no widening of tool authority during the same change.

## Rollback plan

Rollback should be configuration-first where possible:

- restore previous prompt/model/tool bundle;
- preserve event traces for comparison;
- stop new writes if state integrity is uncertain;
- do not mutate historical canonical records to hide the regression;
- re-run the regression set against the restored version.

## Acceptance checks

A repair is accepted only when:

- the original failure is reproducible before the fix;
- the focused test fails on representative broken behavior;
- the focused test passes after the fix;
- valid service intent survives later state transitions;
- partial state cannot be reported as complete;
- retry does not duplicate side effects;
- ambiguity produces clarification or escalation instead of invention;
- public/debug receipts contain no secrets or unnecessary private data.

## Metrics

Track required-field completeness, service-intent retention across turns, clarification rate, escalation rate, false-completion rate, retry rate, duplicate-side-effect rate, leading failure categories, rollback frequency, and manual recovery volume.

Avoid optimizing only for “successful conversation” or sentiment. The primary reliability metric is validated workflow state.

## HAL service mapping

This work sample demonstrates the structure of HAL SUPREME's **Agent Reliability Audit**:

- failure map;
- reproducible cases;
- evaluation/regression set;
- retry/idempotency/validation review;
- evidence and unsupported-success controls;
- observability plan;
- prioritized repair and release gates.

Related public evidence:

- Agent Reliability Audit acceptance contract: https://github.com/UniteAndCreateForLife/HAL_SUPREME/blob/docs/mcp-interoperability-acceptance-2026-09-30/docs/AGENT_RELIABILITY_AUDIT_ACCEPTANCE.md
- MCP interoperability acceptance: https://github.com/UniteAndCreateForLife/HAL_SUPREME/blob/docs/mcp-interoperability-acceptance-2026-09-30/docs/MCP_INTEROPERABILITY_ACCEPTANCE.md
- Revenue Truth control plane: https://github.com/UniteAndCreateForLife/HAL_SUPREME/blob/main/case-studies/REVENUE_TRUTH_CONTROL_PLANE_2026-09-24.md

## Claim boundary

This is a hypothetical public engineering work sample designed to demonstrate methodology. It does not assert an external customer deployment, measured customer outcome, formal security certification, or implementation inside any named third-party product.