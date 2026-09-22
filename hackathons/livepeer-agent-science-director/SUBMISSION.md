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

## Live demo
https://hal-science-director-production.up.railway.app

## Public code
Repository:
https://github.com/UniteAndCreateForLife/HAL_SUPREME/tree/hackathon/livepeer-science-director/hackathons/livepeer-agent-science-director

Review surface:
https://github.com/UniteAndCreateForLife/HAL_SUPREME/pull/4

Website:
https://halsupreme.com

## Official form fields
- Email: uniteandcreateforlife@gmail.com
- Access code: **pending organizer email**
- Track: **Track 1 — Livepeer Agent Builder**
- Repository URL: use the public code URL above
- Demo video URL: **completed MP4; organizer delivery by email is available, public video-host URL still pending**
- Live application: https://hal-science-director-production.up.railway.app
- Website: https://halsupreme.com

## Remaining before final submission
- Receive the organizer-issued six-digit access code.
- Obtain a public/shareable video-host URL for the completed demo MP4 (the live application itself is already public).
- Enter the completed fields in Atumera's official submission form before **24 Sep 2026 23:59 Europe/Athens**.
- Preserve the submission confirmation/receipt.

Registration/outreach email has already been sent to the organizer. Do not claim final submission until the form confirmation is received.
