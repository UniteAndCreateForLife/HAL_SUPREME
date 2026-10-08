# Renderer Canary Acceptance Gate

HAL does not claim video generation is operational until this gate passes on a real worker.

## Preconditions
- Python environment can import the HAL repository.
- ffmpeg and ffprobe are installed.
- ComfyUI is reachable.
- A Wan-class video workflow is installed and exported in API JSON form.
- A separate WorkflowBindings JSON maps prompt, seed, width, height and frame-count fields into the known-good graph.
- The final output node is known when a workflow exposes multiple output nodes.

## Run
1. Run python scripts/renderer_doctor.py.
2. Confirm comfyui_wan.health.health == "healthy".
3. Run:

    python scripts/canary_render.py --workflow <workflow.json> --bindings <bindings.json> --output-node <node-id>

4. HAL queues the bound graph, downloads the artifact through ComfyUI /view, and stages it locally.
5. The canary is accepted only if:
   - the artifact exists;
   - temporal-motion QC passes;
   - ffprobe reports a valid video stream;
   - duration, minimum resolution and minimum FPS are within policy;
   - freeze and black-span checks pass;
   - SHA-256 is recorded;
   - the render receipt contains both motion and technical-quality evidence.

## Failure semantics
Offline renderer, missing binding nodes, missing output node, missing artifact, timeout, still-frame output, invalid video, excessive freeze/black spans, or missing FFmpeg/ffprobe all fail closed. No placeholder video is substituted.

## Current scope
The canary proves deterministic workflow injection + transport + generation + artifact ingestion + motion QC + technical QC + provenance.

ComfyUI image-to-video is not advertised by the generic adapter yet because HAL does not currently upload/bind RenderRequest.image_path into a workflow. That capability should be re-enabled only after the input-upload contract is implemented and tested.

Identity continuity, reference-character control, audio quality, semantic review and full project-manifest integration remain separate gates.
