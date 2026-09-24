# Global Smart Campus 2026 - Startup Application Packet

Project: **HAL Campus Evidence Desk - Private, Auditable AI for Campus Operations and Research**
Track: Early-Stage EdTech Startup
Applicant/startup: HAL SUPREME
Founder / team leader: Jakob Hedrich
Founder email: use the email already confirmed with the organizer

## Fields that must be verified immediately before submission
- Mobile number and country code
- Place / city / country
- Year founded (organizer clarification pending for an eligible unincorporated solo-founder project)
- Annual turnover (organizer clarification pending for the correct form entry; must truthfully satisfy the published < INR 1 crore requirement)
- Funding status
- Any website/product URL used in the form

Do not guess these fields. Everything below is submission-ready unless new evidence changes it.

## Startup details
**Startup Name**
HAL SUPREME

**Founder / Team Leader Full Name**
Jakob Hedrich

**Founder / Co-Founder Names**
Jakob Hedrich - solo founder

**Team Size**
1

**Product Stage**
Functional MVP / early-stage prototype; pre-institutional-pilot for this campus-specific product.

## Project / Idea Title
HAL Campus Evidence Desk - Private, Auditable AI for Campus Operations and Research

## Problem Statement
Campus administrators, faculty, researchers, facilities teams, and IT staff routinely reconcile policies, service requests, research records, operational notes, and security requirements across disconnected systems. Manual synthesis is slow and inconsistent. Generic AI assistants can omit provenance, blur uncertainty, or generate confident recommendations that are difficult to audit. The result is avoidable delay and decision risk precisely where institutions need traceable evidence and accountable human judgment.

## Proposed Solution
HAL Campus Evidence Desk is a bounded AI evidence-synthesis workspace for campus operations and research. A reviewer selects an approved case evidence set; the system produces cited findings, detects known contradictions, proposes reversible next actions, exposes uncertainty, and keeps a mandatory human-review gate. A deterministic acceptance layer rejects uncited items, invalid evidence IDs, and unsupported conflict relations before live-model output is shown. The reference review layer also binds actions to validated tenant scopes and roles so cross-tenant actions, tenant-scope switching, malformed tenant identifiers, and unauthorized review closure fail closed. Tenant identifiers are constrained to 1–64 lowercase alphanumeric/hyphen characters with alphanumeric boundaries. The MVP intentionally excludes admissions, grading, employment, disciplinary, medical, or other high-impact individual decisions.

## How the solution addresses a Smart Campus / Higher Education challenge
The product targets institutional efficiency, campus operations, research support, data use, cybersecurity, and sustainability. It reduces the time required to turn fragmented operational evidence into an auditable brief while preserving human authority. The same architecture can support policy reconciliation, research-access review, facilities incident analysis, sustainability anomalies, IT/security triage, and other evidence-heavy campus workflows without replacing accountable institutional decision makers.

## Target Users
Campus operations and administrative staff; faculty and research teams; IT and security staff; facilities and sustainability teams; department leaders who need an auditable brief before making a decision.

## Key Features
- Evidence-scoped analysis with explicit evidence IDs and citations
- Deterministic citation and conflict acceptance checks
- Live-model synthesis only behind bounded output limits
- Fail-closed direct-identifier egress gate before hosted-model calls
- Tenant-scoped authorization with role/action enforcement and bounded tenant identifiers
- Tamper-evident SHA-256 report receipts and chained review events
- Explicit uncertainty and contradiction surfacing
- Reversible action plans rather than automatic decisions
- Mandatory `PENDING_HUMAN_REVIEW` gate
- Synthetic-demo mode that never requires student records

## Innovation / Difference
The differentiator is not a generic campus chatbot. HAL Campus Evidence Desk treats provenance, tenant boundaries, and reviewability as first-class product behavior. Live AI cannot silently promote its own claims into accepted evidence: every accepted item must reference supplied evidence IDs, conflict claims are checked against a deterministic case truth layer, and review events are bound to a tenant-scoped tamper-evident audit chain. Model suggestions remain subordinate to auditable evidence and human review. This creates a safer path for universities that want AI assistance without delegating institutional authority to an opaque model.

## Technologies Used / Proposed
Python 3.12 local MVP; browser-based HTML/CSS/JavaScript UI; deterministic validation engine; tenant-scoped RBAC reference layer; SHA-256 report/audit receipts; NVIDIA NIM prototype inference; HAL provider-routing layer; Cloudflare Workers AI/Workers for bounded edge inference and APIs; D1 for durable metadata; KV for fast configuration; Vectorize for semantic retrieval; Queues and Workflows for asynchronous/resumable tasks; Durable Objects for coordination; GitHub Actions for reproducible four-platform CI and validation. Production integrations remain modular and subordinate to institutional access controls.

## Use of AI
AI is used only for bounded evidence synthesis: concise findings, advisory actions, and conflict suggestions from a supplied evidence set. The model is instructed to use only provided evidence, and its output passes through deterministic checks before display. The live MVP currently uses `openai/gpt-oss-20b` through verified NVIDIA NIM developer access. The design supports provider substitution and local/open models without changing the acceptance policy.

## Working Prototype / POC Availability
Yes. A functional local MVP exists and a zero-cost public safety-mode prototype is deployed at https://hal-campus-evidence-desk.therealjakobhedrich.workers.dev. The public build exposes the three synthetic scenarios and deterministic evidence acceptance while intentionally disabling unbounded external model calls. The local competition build retains verified live-model synthesis, citation validation, conflict checks, tenant-scoped review controls, tamper-evident audit verification, and the mandatory human-review gate.

A public competition release containing the recorded demo, proposal PDF, and pitch PDF is available at:
https://github.com/UniteAndCreateForLife/HAL_SUPREME/releases/tag/gsc2026-demo-v1

## Expected Impact / Benefits
The intended impact is faster, more consistent preparation of campus evidence briefs without sacrificing provenance or accountable review. The MVP evaluation targets 100% citation validity, zero unsupported material claims in the canonical synthetic cases, complete detection of seeded contradictions, and source traceability that a reviewer can inspect in under 30 seconds. The system is designed to reduce repetitive synthesis work while keeping decisions with authorized staff.

## Solution Benefits
- Reduces manual evidence reconciliation across campus workflows
- Makes every accepted AI-assisted item traceable to supplied evidence
- Surfaces contradictions instead of inventing a resolution
- Rejects cross-tenant review actions in the reference authorization layer
- Validates tenant identifiers at explicit size/character boundaries
- Makes review-state tampering detectable through chained receipts
- Keeps a human reviewer in control of all recommendations
- Supports private/local or managed deployment patterns
- Reuses one evidence architecture across operations, research, security, facilities, and sustainability cases

## Scalability Potential
The system is designed as a provider-agnostic evidence layer rather than a one-off workflow. Institutions can add new case schemas, evidence connectors, model providers, policy rules, and review roles without changing the core provenance contract. The MVP now includes application-layer tenant-scoped authorization and a tenant-bound audit chain. Production scale-up would add institution-managed SSO, authoritative role mapping, storage/query-level tenant partitioning, configurable retention, durable audit export, and institution-approved provider routing. Edge APIs, durable state, vector retrieval, async job infrastructure, and multi-provider routing are already represented in HAL's verified infrastructure fabric.

## Implementation Feasibility
The core MVP already works locally and has verified live inference. The competition reference implementation also includes tenant-scoped role authorization, explicit tenant-ID validation, a tamper-evident review chain, privacy egress checks, a one-command judge verifier, and four-platform CI. A pilot-ready version is primarily an integration and governance hardening exercise rather than a greenfield build: authentication/SSO, authoritative institutional role mapping, storage/query-level tenant partitioning, institutional connectors, audit retention/export, deployment policy, and user testing are the main remaining work. No specialized hardware is required for the client; inference can use sponsored/serverless capacity or institution-controlled local/open models.

## Estimated Time Required to Develop / Implement
Functional MVP: complete. Pilot hardening: approximately 6-8 weeks for one bounded institutional workflow, assuming timely access to a designated data owner, authentication/integration endpoints, and reviewer feedback. Broader multi-department rollout would follow after pilot acceptance.

## Current Validation
The current unit suite contains **30 tests** covering deterministic grounding, privacy egress, audit integrity, role authorization, tenant isolation, and tenant-ID boundary validation. All three canonical synthetic cases pass deterministic citation validity, conflict detection, zero unsupported-material-claim, and human-review constraints. Adversarial tests reject cross-tenant actions, tenant-scope switching, malformed tenant IDs, unauthorized review closure, invalid report receipts, mutation, and broken audit linkage. Dedicated authorization tests verify valid 1-character, 2-character, and 64-character tenant scopes; reject overlength, uppercase, slash-containing, and hyphen-bounded invalid scopes; fail closed on unknown roles; and exercise analyst/reviewer/auditor permission boundaries. The public CI runs the acceptance workflow on Ubuntu x64, Ubuntu ARM64, Windows 2025 x64, and macOS 15 ARM64. A deterministic reference benchmark processed **30,000 reports with zero acceptance-invariant failures** and no paid/external-model calls. A bounded live NVIDIA NIM run on all three cases completed without provider errors; all accepted live items were evidence-grounded and all live conflict relations matched seeded truth. The three live runs used 1,409 total tokens with mean latency about 18.6 seconds in the recorded prototype path.

## Business Model
Initial hypothesis: institution-hosted or managed deployment with a free/open public-interest core where practical, plus paid integration, managed infrastructure, support, and governance services for institutions that need them. The application should present this as an early-stage model, not established revenue.

## Pricing Approach
Pricing is not yet validated. The proposed pilot approach is a fixed-scope implementation tied to one defined workflow and measurable acceptance criteria, followed by institution-specific annual support or managed-service pricing if the pilot proves value. No current customer pricing or recurring-revenue claim should be made.

## Data Privacy
The competition demo uses synthetic data only. Before hosted inference, the reference privacy gate blocks common direct identifiers and records only identifier category/location rather than the matched value. The application-layer review path also enforces a validated tenant scope. Production design still requires explicit institutional authority, institution-specific DLP/classification, least-privilege connectors, SSO/authoritative role mapping, storage/query-level tenant partitioning, purpose limitation, configurable retention/deletion, key management, and formal privacy/legal review. The product is designed so an institution can keep sensitive evidence inside its chosen deployment boundary and can select local/open inference where policy requires it.

## Security
Secrets remain outside Git. Model and route allowlists bound unpredictable execution. Evidence retrieval is scoped per case rather than searching unrelated records. The reference MVP now includes fail-closed tenant/role authorization, explicit 1–64 character tenant-ID validation, and SHA-256-linked review receipts; cross-tenant access and unauthorized closure fail verification. Production hardening still includes institutional SSO, authoritative role mapping, storage/query-level tenant partitioning, encryption in transit and at rest, durable access/audit logging, input/output size limits, retention/deletion controls, key management, incident response, security review, and fail-closed provider routing. No autonomous action is granted by the MVP, and no FERPA, HIPAA, GDPR, SOC 2, ISO 27001, or equivalent certification is claimed.

## Responsible AI
Every accepted model item must cite supplied evidence. Missing or conflicting evidence is surfaced rather than concealed. Unsupported conflict relations are rejected. Model output is advisory, never self-approving, and is separated from evidence and user-entered decisions. Review closure is restricted to the reviewer role in the reference workflow. High-impact individual decisions such as admissions, grading, employment, discipline, and medical decisions are intentionally outside MVP scope.

## Scale-Up Plan
1. Finalize the competition MVP and submission package.
2. Run a bounded campus workflow pilot with synthetic/public or institution-approved data.
3. Measure review time, citation validity, conflict detection, unsupported-claim rate, tenant-boundary behavior, and reviewer usability.
4. Integrate institutional SSO, authoritative role mapping, storage/query-level tenant partitioning, retention/deletion policy, and audit export.
5. Add institution-approved connectors and local/open inference options.
6. Expand only to additional workflows that pass the same evidence-grounding, authorization, audit, and human-review acceptance gates.

## Founder / Core Team Profile
Jakob Hedrich is the solo founder and AI engineer behind HAL SUPREME, an active software/AI engineering environment focused on orchestration, local/open models, auditable agent workflows, infrastructure routing, embodied systems, and reusable production tooling. The campus product is deliberately scoped to evidence-grounded operational assistance rather than unrestricted general automation.

## Users / Pilots / Revenue / Validation
No university customer, institutional deployment, campus pilot, learning-outcome result, or campus-product revenue is claimed. Validation currently consists of the working synthetic MVP, automated tests, deterministic evidence checks, tenant/RBAC adversarial tests, tenant-ID boundary tests, tamper-evident audit verification, four-platform CI, a deterministic benchmark, and verified bounded live-model canaries. This is the accurate early-stage position for the submission.

## Links / Uploads
- Project Summary / Proposal PDF: `HAL_CAMPUS_EVIDENCE_DESK_PROPOSAL_2026-09-23.pdf` (required by current application UI)
- Pitch deck: `HAL_CAMPUS_EVIDENCE_DESK_PITCH_2026-09-23.pdf` (optional during initial application)
- Prototype / Demo Link: https://hal-campus-evidence-desk.therealjakobhedrich.workers.dev
- GitHub / Repository Link: https://github.com/UniteAndCreateForLife/HAL_SUPREME/tree/main/challenges/global-smart-campus-2026
- Public Competition Release: https://github.com/UniteAndCreateForLife/HAL_SUPREME/releases/tag/gsc2026-demo-v1
- Demo Video: `HAL_CAMPUS_EVIDENCE_DESK_DEMO_2026-09-23.mp4` in the public competition release
- Product / Website Link: optional; verify before submission
- Supporting Images: `public_demo/PUBLIC_DEMO_HOME.png` and `public_demo/PUBLIC_DEMO_ANALYSIS.png` captured from the deployed prototype

## Final truthfulness gate
Before pressing Submit, verify contact/location/startup facts, organizer guidance for the unincorporated founding-year/turnover fields, funding status, every external link, and every numeric claim. Do not add customer, pilot, revenue, institutional adoption, learning-outcome, FERPA-compliance, or security-certification claims without evidence.
