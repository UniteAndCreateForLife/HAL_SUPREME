# Hackathon submission working draft

## Project
HAL Science Director

## One-line pitch
A steerable scientific-media director that uses Livepeer Agent to plan an observable scientific claim, generate the media, expose the exact accuracy guardrails, and learn from a human correction on the next attempt.

## Working path to demonstrate
1. Enter a scientific concept.
2. Generate an image or short video.
3. Inspect the Livepeer-generated plan and accuracy guardrails.
4. Add one scientific correction.
5. Refine and show that the next plan/render prompt incorporates the correction.
6. Open the provenance ledger to show capabilities and hash for each attempt.

## Livepeer centrality
The app sends the scientific planning step to the Livepeer Agent MCP using a text capability and sends the rendering step through the same MCP using Livepeer media capabilities. Video completion is tracked through Livepeer's async media-job polling tool.

## Remaining before final submission
- Register the participant/team through Atumera's official registration path.
- Run at least one real keyless or bearer-backed image generation end-to-end.
- Run one short video generation if budget/latency permits.
- Capture a short demo video showing generate → review → correct → regenerate.
- Deploy the app or provide reproducible local run instructions.
- Fill the official submission form before 24 Sep 2026 23:59 Europe/Athens.
