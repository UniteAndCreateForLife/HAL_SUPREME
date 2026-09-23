# HAL Campus Evidence Desk - 3 Minute Recorded Demo Script

## 0:00-0:20 - Problem
Campus teams make operational decisions from fragmented policies, research notes, facilities records, and security requirements. Generic chatbots can summarize quickly, but provenance, contradictions, and accountability are often unclear.

## 0:20-0:45 - Product
HAL Campus Evidence Desk is a private, auditable evidence-synthesis workspace. It scopes analysis to an approved evidence set, cites every accepted item, surfaces contradictions, proposes reversible next actions, and keeps a mandatory human-review gate.

## 0:45-1:25 - Policy conflict scenario
Open the `Conflicting policy guidance` case. Show E1, E2, and E3. Run deterministic mode first. Point to 100% citation validity, the E1/E2 conflict, zero unsupported material claims, and `PENDING_HUMAN_REVIEW`.

Switch to live-model mode. Explain that the model cannot write directly into accepted evidence. Its findings, actions, and conflict relations pass through a deterministic acceptance layer before display.

## 1:25-2:00 - Research and facilities scenarios
Open `Research access request` and show that the product identifies missing owner approval without inventing a policy conflict. Open `Facilities energy anomaly` and show the reversible investigation sequence grounded in meter, maintenance, occupancy, and weather evidence.

## 2:00-2:30 - Architecture and safety
Briefly show the architecture: bounded browser/API front end; provider-routed inference; deterministic evidence acceptance; D1/KV/Vectorize for state and retrieval; Queues/Workflows for async jobs; human review as the final authority. State clearly that the competition demo uses synthetic data only.

## 2:30-3:00 - Evidence of readiness
State: eight automated tests pass. Three bounded live-model canaries completed without provider errors. Accepted live items were evidence-grounded and conflict relations matched seeded truth. Close with the pilot plan: one bounded institutional workflow, measurable review-time and citation-quality metrics, then controlled scale-up.
