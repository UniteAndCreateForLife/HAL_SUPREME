# HAL Video Pipeline V2 — Evidence-First Production

This pipeline turns HAL video work into a repeatable production system rather than a sequence of model calls.

## Core rule

**Generation is not acceptance.** Every shot has a declared purpose, source lineage, technical gate, semantic gate, and promotion state. Provider success only creates a candidate.

## What changed in V2

1. **ComfyUI request bindings are real.** A known-good API workflow can now receive HAL's prompt, seed, width, height, and frame count through WorkflowBindings. The renderer no longer has to queue an unchanged graph.
2. **ComfyUI artifacts are downloaded through /view.** HAL does not assume the ComfyUI output directory is the same filesystem as the orchestrator.
3. **Final-output selection is deterministic.** A configured comfy_output_node may be required, and video outputs are preferred over still images.
4. **Technical QC is first-class.** qc/video.py checks decodability, duration, resolution, FPS, optional audio, freeze spans, and black spans. scripts/video_audit.py combines that with the existing temporal-motion gate.
5. **Receipts carry quality evidence.** Accepted renders can include the technical QC report alongside SHA-256 and motion evidence.

## Production graph

1. **Brief + claim contract**
   - Define what the viewer must understand.
   - Separate product proof, cinematic illustration, and narration.
   - Mark claims that require visible evidence.

2. **Shot manifest**
   - Every shot gets an ID, duration, source class, continuity anchors, and acceptance criteria.
   - Real UI / terminal / metrics shots must remain real. Do not synthesize proof footage.

3. **Capability routing**
   - Screen capture and product proof: deterministic capture/edit path.
   - Generated motion: route to the healthiest available renderer.
   - Image-to-video / reference continuity: require a backend that explicitly supports the needed control.
   - Do not hardwire a vendor or model merely because it is fashionable.

4. **Candidate generation**
   - Preserve source inputs, prompt, seed, model ID, provider job ID when available, and cost estimate.
   - Keep candidates private until accepted.

5. **Technical QC**
   - Decode / probe.
   - Resolution and FPS.
   - Expected duration.
   - Genuine temporal motion.
   - Freeze detection.
   - Black-frame / black-span detection.
   - Audio-stream requirement for assembled masters.

6. **Semantic QC**
   - Does the shot prove the intended claim?
   - Identity / wardrobe / environment continuity.
   - Hand, prop, face, text, and geometry defects.
   - Camera direction and screen direction.
   - Dialogue timing and lip-sync where applicable.
   - Reject misleading or invented evidence.

7. **Edit + sound**
   - Evidence before spectacle for product demos.
   - Do not reuse the same coverage to pad runtime.
   - Keep dialogue, music, ambience, SFX, and narration as separate stems until final mix.
   - Use deterministic local finishing for cuts, titles, mix, subtitles, and delivery encodes.

8. **Master gate**
   - Full-duration decode.
   - Loudness / true peak target.
   - Freeze and black-span scan.
   - No missing or repeated shots outside the manifest.
   - SHA-256 and final receipt.
   - Human approval before release.

9. **After-action loop**
   - Record rejected shots and causes.
   - Convert failures into reusable prompt, routing, QC, and continuity rules.
   - Update the pipeline only through tested changes.
   - Produce a sanitized review/case-study cut when appropriate.

## Current judge-demo strategy

For HAL Science Director — AI That Checks Its Own Work, the strongest story is one real end-to-end failure/correction cycle:

**brief → plan → generate → independent visual judge → visible failure → correction → second attempt → provenance**

The hook is not "we can generate video." The hook is **the system rejects its own attractive but scientifically weak result instead of pretending success**.

Use configs/video/hal_science_director_judge_demo_v3.json as the editorial contract.

## Local model note

LTX development has moved to LTX-2 / LTX-2.5, including synchronized audio-video generation and multi-keyframe control. Treat it as a capability candidate, not an assumed local default: the current model family is large, hardware requirements are material, and its current license must be reviewed before product deployment.

Official references:
- https://github.com/Lightricks/LTX-2
- https://ffmpeg.org/ffmpeg-filters.html

## Commands

Audit any candidate:

    python scripts/video_audit.py candidate.mp4 --deep --max-freeze 2.0 --max-black 1.5

Run a deterministic ComfyUI canary:

    python scripts/canary_render.py --workflow path/to/workflow_api.json --bindings path/to/workflow_bindings.json --output-node 42

A canary is not production proof until its artifact, motion evidence, technical QC, SHA-256, and receipt are all present.
