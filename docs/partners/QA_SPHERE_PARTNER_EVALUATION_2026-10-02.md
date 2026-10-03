# QA Sphere Partner Evaluation — HAL SUPREME

Date: 2026-10-02

Sources:
- https://qasphere.com/partners/
- https://qasphere.com/pricing/
- https://qasphere.com/docs/billing/

QA Sphere's current partner program has both Solution Partner and Technical Partner tracks. The Solution track is aimed at consultancies and implementation/integration firms, while the Technical track supports product integrations through REST API, CLI, MCP, and webhooks.

Public partner terms currently state there is no joining fee, no annual fee, no minimum sales commitment, and no certification exam. QA Sphere also provides a free tier for up to three users with API, CLI, MCP and integrations available.

## HAL service fit

- Agent Reliability Audit: turn observed failures into reproducible test cases, regression coverage, retries/idempotency checks, and observability requirements.
- MCP / Tool Integration: connect bounded MCP tools into test-management workflows with explicit read/write authority and approval gates.
- Evidence & Citation Validation Harness: attach evidence and machine-readable receipts to test outcomes so unsupported success claims are rejected.
- Private / Local AI Architecture Review: document tool/provider boundaries, egress, auth, and failure behavior for teams evaluating AI-assisted development workflows.

## Proposed synthetic proof

1. Create one non-sensitive QA project or approved demo workspace.
2. Define a small set of deterministic cases for one HAL public workflow.
3. Push or create results through the supported API/CLI/MCP surface.
4. Preserve explicit pass, fail, blocked, skipped, and not-run states.
5. Attach one machine-readable receipt or artifact reference to each completed result.
6. Require human approval before any consequential external issue creation or write beyond the test workspace.
7. Re-run the same cases to prove regression stability.
8. Document the exact authority and failure boundary for the MCP/tool path.

## Acceptance checks

- A failed or blocked run cannot be reported as passed.
- Missing evidence is visible rather than silently treated as success.
- Retries do not create duplicate test records or external actions.
- Test-state changes are attributable to a specific run.
- The same public-safe regression set can be replayed after a change.
- The integration does not require production customer data or secrets.

## Questions before commitment

- Can an early-stage independent AI engineering practice apply to both the Solution and Technical Partner tracks?
- Can the initial technical proof be completed entirely on the free tier?
- Are there insurance, incorporation, client-volume, or revenue requirements beyond the published no-fee/no-minimum-sales terms?
- What commercial terms apply to Solution Partner referrals or implementation delivery?
- For Technical Partners, what evidence is expected before an integration is featured publicly?
- Is there a preferred synthetic/demo project structure for partner evaluations?

## Claim boundary

This document is an evaluation plan only. It does not claim QA Sphere partner approval, third-party customer production deployment, a signed commercial agreement, or paid usage.
