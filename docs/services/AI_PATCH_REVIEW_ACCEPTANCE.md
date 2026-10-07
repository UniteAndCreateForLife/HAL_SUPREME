# AI Patch Review Acceptance

This checklist supports HAL SUPREME's existing **Evidence & Citation Validation Harness** and **Agent Reliability Audit** offers. It is not a new service.

## Goal

Review AI-generated code as a proposed change that must earn acceptance through repository evidence. A model's claim that a patch is complete is never the acceptance criterion.

## Evidence sequence

intent -> patch -> independent reproduction -> tests -> adversarial checks -> review rationale -> merge decision

## Minimum review contract

1. Restate the intended behavior and the repository boundary before judging the patch.
2. Identify the smallest observable acceptance criteria.
3. Inspect the actual diff rather than relying on the generating agent's summary.
4. Reproduce the relevant behavior from a clean checkout or otherwise isolated state when practical.
5. Run the repository's required tests plus a focused regression test for the claimed change.
6. Check failure paths, malformed inputs, duplicate/retry behavior, and state mutation where they are relevant.
7. Separate deterministic evidence from reviewer judgment.
8. Record unsupported claims, untested assumptions, and environment limitations explicitly.
9. If the patch affects tools, APIs, MCP servers, or external state, verify downstream state instead of trusting success text.
10. Do not merge solely because the generating model, evaluator model, or original author says the change is correct.

## Regression requirement

For a defect fix, prefer a test that fails against the prior behavior and passes with the proposed change. When practical, mutation-check the new test by deliberately restoring the defect or weakening the guard and confirming the test catches it.

## Review output

A useful review should contain:

- verdict: accept / reject / revise;
- acceptance criteria evaluated;
- commands or checks performed;
- observed results;
- remaining uncertainty;
- exact reason for any rejection or requested revision.

## Public HAL evidence

- [HAL public portfolio](../../PORTFOLIO.md)
- [PR #49 — repeated evidence-ID conflict fix](https://github.com/UniteAndCreateForLife/HAL_SUPREME/pull/49)
- [PR #50 — adversarial Evidence Gate fixture](https://github.com/UniteAndCreateForLife/HAL_SUPREME/pull/50)

PR #49 documents an AI-generated patch independently checked in a clean checkout, including Python and browser parity tests. PR #50 documents 11 adversarial tests plus mutation checks that caught 7 deliberately broken gate variants.

## Claim boundary

HAL's public record demonstrates self-operated open-source review and verification. This checklist does not claim a large contributor community, third-party production ownership, security certification, or a specific number of professional software-engineering years.
