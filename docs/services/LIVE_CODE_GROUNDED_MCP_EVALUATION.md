# Live-Code Grounded MCP Evaluation

Public-safe evaluation method for MCP services that answer product or software questions from a live repository or other source-of-truth codebase.

This is supporting evidence for HAL SUPREME's existing **Evidence & Citation Validation Harness** and **MCP / Tool Integration** offers. It is not a new service category.

## Evidence states

```text
configured -> authorized -> attempted -> observed -> validated -> reported
```

A fluent answer is not accepted merely because a model or tool returned successfully. The evaluation separately verifies that the source was reachable, the correct source was consulted, the answer is traceable to that source, and the reported result matches the current code state.

## Bounded evaluation pack

Use 5-20 reproducible cases across:

1. **Current-state answer** — a fact present in the current default branch.
2. **Recent-change answer** — a behavior changed in a recent commit or merge.
3. **Removed behavior** — a feature that used to exist but no longer does.
4. **Unknown / absent fact** — the source cannot support the requested claim.
5. **Conflicting evidence** — comments/docs and executable code disagree.
6. **Versioned behavior** — current behavior differs from an older release.
7. **Authorization boundary** — caller can query answers without receiving broader repository authority.
8. **Revocation** — access stops after the repository/source credential is revoked.
9. **Stale-cache case** — a new push changes the correct answer and the service must not keep returning the old result beyond its stated freshness contract.
10. **Tool-use enforcement** — a model cannot substitute unsupported memory when the workflow requires source-backed answers.

## Evidence contract

Each case should record, where available:

- case_id
- question
- expected_answer_or_expected_unknown
- repository/source identifier
- branch/ref
- source files or commits consulted
- source freshness timestamp
- tool/request identifier
- authorization scope
- raw tool result hash
- answer/citation set
- deterministic validation result
- rubric result, if needed
- final disposition
- receipt hash

## Acceptance rules

### Grounding

A claim passes only when the cited source materially supports it. File names, commit IDs, or URLs that do not support the claim are not evidence.

### Freshness

The evaluation states the freshness contract explicitly. If the source is intended to track every push, a post-push regression verifies that the next answer reflects the new code state.

### Explicit unknown

When the codebase does not establish an answer, the preferred result is an explicit unknown / insufficient-evidence outcome. Hedged invention is a failure.

### Source conflict

Executable behavior, configuration, tests, generated schemas, and written documentation may disagree. Conflicts are surfaced rather than silently resolved by the model.

### Negative-access behavior

A caller that can ask product questions must not automatically gain raw repository credentials or unrelated repository access. Read-only source access and answer-serving authority are tested separately.

### Tool-call reliability

If a workflow requires source-backed answers, the regression set includes cases where the model is tempted to answer from prior knowledge. An unsupported answer that bypasses the source tool fails.

### Downstream validation

Tool success is not proof that the final answer is correct. The answer is independently checked against the agreed source-of-truth material.

## Failure classes

- source_not_called
- source_unavailable
- stale_source
- unsupported_claim
- citation_mismatch
- wrong_version
- conflict_hidden
- authorization_overreach
- revoked_access_still_works
- malformed_result
- duplicate_or_replayed_result
- downstream_validation_failed

## Deliverable pattern

A bounded engagement can produce:

- source/evidence contract;
- 5-20 reproducible cases;
- deterministic validators;
- unsupported-claim rejection;
- freshness and revocation checks;
- machine-readable receipts;
- prioritized failure map;
- operator notes for rerunning the pack after product or model changes.

## Claim boundary

This is an engineering evaluation method. It is not a penetration test, compliance certification, legal opinion, customer-production deployment claim, or guarantee that a model will never hallucinate.
