# End-to-End Workflow Acceptance

This checklist supports HAL SUPREME's existing **Agent Reliability Audit**, **MCP / Tool Integration**, and **Evidence & Citation Validation Harness** offers. It is not a separate service.

## Core rule

A workflow is not complete because a process started, a window opened, a helper existed, or an agent reported success. Completion is established only when the exact delivered user or system flow is exercised and its required outcome is independently verified.

## Evidence sequence

requested -> configured -> executed in target context -> observed -> downstream state validated -> failure paths checked -> completion reported

## Acceptance checks

1. **Test the delivered path**
   - Run the exact command, click path, API call, or operator flow being handed to the user.
   - Do not substitute a nearby proxy such as "process exists", "server is listening", "workspace opened", or "UI rendered" when the requirement is an end-to-end user action.

2. **Preserve execution context**
   - Record the shell/session, working directory, environment, identity, target account, provider, transport, and relevant permissions.
   - A success in a different console, browser session, model worker, or account does not prove the delivered context works.

3. **Validate authoritative state**
   - For writes, check the downstream system that owns the state.
   - For reads, compare the returned value against the expected source or deterministic oracle when practical.
   - Agent-generated success text is never sufficient evidence for consequential external changes.

4. **Treat contradictory evidence as blocking**
   - If the user, regression test, API, or downstream system reproduces the original failure, completion is not established.
   - Reopen diagnosis instead of explaining away the contradictory result.

5. **Separate partial proof from completion**
   - Examples of partial proof:
     - process launched;
     - connection established;
     - tool discovered;
     - file exists;
     - command parsed;
     - UI opened.
   - Completion requires the acceptance condition for the requested workflow.

6. **Declare unexecuted checks**
   - If policy, permissions, missing credentials, unavailable infrastructure, or another blocker prevents the final acceptance step, report the missing proof explicitly.
   - Do not convert a planned or blocked test into a completion claim.

7. **Regressionize failures**
   - Every reproduced defect should become a repeatable test or runbook check when practical.
   - Include the original failing context, not only a simplified substitute.

8. **Capture receipts**
   - Keep enough evidence to answer:
     - what was attempted;
     - where it ran;
     - what result was observed;
     - what downstream state was checked;
     - what remains unverified.

9. **Bound retry behavior**
   - Retrying a failed flow must not create duplicate writes or stronger authority.
   - After ambiguous completion, validate state before retrying a consequential action.

10. **Report with calibrated language**
    - Use **verified** only for checks actually executed.
    - Use **partially verified** when supporting components work but the target path is untested.
    - Use **blocked** when the acceptance check could not be run.
    - Use **failed** when the target path was executed and did not meet acceptance criteria.

## Minimum regression pack

- exact target user flow succeeds in the intended environment;
- same flow from an intentionally wrong context fails as expected;
- contradictory downstream state prevents a success report;
- blocked final verification is surfaced as blocked, not complete;
- retry after ambiguous completion does not duplicate a write;
- user-reported reproduction reopens the workflow and invalidates prior completion;
- terminal receipt identifies the evidence used for the completion claim.

## Public external example

OpenAI Codex issue #51692 documents a reported terminal workflow where partial checks such as process/window existence were treated as completion even though the exact delivered command path had not been verified and the user reproduced the original error.

Reference:
https://github.com/openai/codex/issues/51692

The issue is used here only as a public reliability example. HAL does not claim authorship, an upstream diagnosis, a merged fix, or independent reproduction of the entire incident.

## Public HAL evidence

- Portfolio:
  https://github.com/UniteAndCreateForLife/HAL_SUPREME/blob/main/PORTFOLIO.md
- AI Patch Review Acceptance:
  https://github.com/UniteAndCreateForLife/HAL_SUPREME/blob/main/docs/services/AI_PATCH_REVIEW_ACCEPTANCE.md
- MCP Tool Exposure Acceptance:
  https://github.com/UniteAndCreateForLife/HAL_SUPREME/blob/main/docs/services/MCP_TOOL_EXPOSURE_ACCEPTANCE.md
- Agent Task Startup Acceptance:
  https://github.com/UniteAndCreateForLife/HAL_SUPREME/blob/main/docs/services/AGENT_TASK_STARTUP_ACCEPTANCE.md

## Claim boundary

HAL's strongest public evidence is self-operated engineering and reproducible public proof. This checklist does not claim third-party customer production ownership, protocol certification, security certification, or guaranteed business outcomes.
