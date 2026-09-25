# Hackathon submission package

## Project
HAL Science Director

## Track
**Track 1 — Livepeer Agent Builder**

## One-line pitch
HAL Science Director uses Livepeer Agent to plan a scientific claim, generate the media, independently inspect the rendered artifact for visible scientific errors, and turn those errors into the next correction.

## Demonstrated path
1. Enter a scientific concept and explicit accuracy constraints.
2. Livepeer `gemini-text` creates the observable claim, guardrails, exclusions, and production prompt.
3. Livepeer `flux-schnell` or the configured video capability renders the artifact.
4. A separate Livepeer multimodal `gemini-text` call judges the actual artifact by `source_url`.
5. The UI exposes score, verdict, visible issues, and a suggested correction.
6. The operator can load that correction into the refinement field and generate the next attempt.
7. The provenance ledger records the capabilities, prompts, review result, output reference, and SHA-256 receipt.

## Verified evidence
- GitHub Actions: 8/8 automated tests passing.
- Syntax checks passing on server, Livepeer adapter, planner, judge, and browser client.
- Real keyless Livepeer planner call: passing.
- Real keyless Livepeer image generation: passing.
- Real Livepeer multimodal visual-science review: passing.
- Real rendered artifact and JSON receipt preserved by CI.
- Latest Saturn example: **6/10, revise**; the judge correctly identified excessive apparent ring thickness, weak major divisions, and insufficient density/banding detail.
- 1920×1080 H.264 submission demo rendered from the real artifact and verified results.
- Credential-free public video route: https://hal-science-director-production.up.railway.app/HAL_SCIENCE_DIRECTOR_SUBMISSION_DEMO.mp4
- Enhanced 25-second judge demo: five HQ Livepeer Agent motion scenes, keyframe-then-animate, deterministic titles, neutral narration, and an explicit provenance/cost receipt.
- Enhanced demo route: https://hal-science-director-production.up.railway.app/HAL_SCIENCE_DIRECTOR_JUDGE_DEMO_V2.mp4
- Enhanced demo SHA-256: `62050dc0eaeafac6807fc07769558359eaf79b7c21263512c12aa38bbc029531`.
- Public judge path is resilient to temporary keyless MCP budget-store outages: it shows a verified recorded demo and marks the fresh review unavailable instead of returning 500 or inventing a score.

## Live demo
https://hal-science-director-production.up.railway.app

## Public code
Repository:
https://github.com/UniteAndCreateForLife/HAL_SUPREME/tree/hackathon/livepeer-science-director/hackathons/livepeer-agent-science-director

Review surface:
https://github.com/UniteAndCreateForLife/HAL_SUPREME/pull/4

Website:
https://halsupreme.com

## Official form record
- Email: uniteandcreateforlife@gmail.com
- Access code: supplied privately by the organizer and intentionally not stored in Git.
- Track: **Track 1 — Livepeer Agent Builder**
- Repository URL: use the public code URL above
- Original form demo video: https://hal-science-director-production.up.railway.app/HAL_SCIENCE_DIRECTOR_SUBMISSION_DEMO.mp4
- Enhanced supplemental judge demo: https://hal-science-director-production.up.railway.app/HAL_SCIENCE_DIRECTOR_JUDGE_DEMO_V2.mp4
- Live application: https://hal-science-director-production.up.railway.app
- Website: https://halsupreme.com

## Submission status
The user reports that the official Atumera form was submitted on **22 Sep 2026**. Preserve any confirmation/receipt outside the public repository. The enhanced judge demo was produced before the deadline as supplemental evidence; it does not alter or expose the private access code.

Registration/outreach and fallback submission records have also been sent to the organizer.
