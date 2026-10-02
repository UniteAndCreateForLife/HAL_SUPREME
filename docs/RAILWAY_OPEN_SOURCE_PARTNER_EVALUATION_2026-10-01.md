# HAL SUPREME — Railway Open Source Partner Evaluation

Date: 2026-10-01

## Claim state

This is a public-safe evaluation note. It does not claim Railway partner acceptance, commission eligibility, or template verification.

## Existing Railway evidence

Authenticated Railway readback shows two HAL SUPREME projects:

- **HAL Compute Fabric**
  - source repository: `UniteAndCreateForLife/HAL_SUPREME`
  - current main service: `hal-router-main-v11`
  - latest observed deployment status: **SUCCESS**
  - build: Railpack
  - runtime: Railway V2

- **HAL Science Director**
  - source repository: `UniteAndCreateForLife/HAL_SUPREME`
  - branch: `hackathon/livepeer-science-director`
  - root: `/hackathons/livepeer-agent-science-director`
  - latest observed deployment status: **SUCCESS**
  - Dockerfile build
  - healthcheck: `/api/health`

Historical failed services in HAL Compute Fabric are not hidden; current partner positioning should use the successfully deployed services only and treat previous failures as engineering history rather than success evidence.

## Why the Railway partner program fits

Railway's Open Source Partner Program currently offers:

- one-click deployment templates;
- verified marketplace placement;
- community/support feedback loops;
- commission on template usage;
- private-image support for premium tiers;
- co-marketing for technology partners.

HAL's best first contribution is not a broad commercial claim. It is a bounded, documented template or agent-facing deployment that demonstrates:

1. reproducible deployment from the public repository;
2. explicit health/readiness checks;
3. provider-neutral configuration;
4. secret-safe environment handling;
5. agent/MCP operation with human confirmation around destructive changes;
6. observable failure states and rollback notes.

## Candidate partner artifact

**HAL Agent Reliability / Compute Router template**

Initial acceptance target:

- deploys from the public HAL repository;
- requires no embedded secrets;
- starts with a documented minimal configuration;
- exposes a health endpoint;
- fails closed when required configuration is missing;
- documents which actions are read-only vs consequential;
- includes a short operator runbook;
- carries no claim of production customer deployment.

## Relevant HAL service lanes

- Agent Reliability Audit
- MCP / Tool Integration
- Private / Local AI Architecture Review
- Evidence & Citation Validation Harness

## Public sources

Railway Open Source Partner Program:
https://railway.com/partners

Railway MCP Server:
https://docs.railway.com/ai/mcp-server

HAL SUPREME:
https://github.com/UniteAndCreateForLife/HAL_SUPREME
