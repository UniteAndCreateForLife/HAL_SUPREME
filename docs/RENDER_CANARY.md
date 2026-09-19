# Renderer Canary Acceptance Gate

HAL does not claim video generation is operational until this gate passes on a real worker.

## Preconditions
- Python environment can import the HAL repository.
- ffmpeg is installed.
- ComfyUI is reachable.
- A Wan-class video workflow is installed and exported in API JSON form.
- The workflow produces a real moving video file visible to the HAL worker filesystem.

## Run
1. Run `python scripts/renderer_doctor.py`.
2. Confirm `comfyui_wan.health.health == "healthy"`.
3. Run `python scripts/canary_render.py --workflow <workflow.json>`.
4. The canary is accepted only if the artifact exists, temporal-motion QC passes, SHA-256 is recorded and a render receipt is written.

## Failure semantics
Offline renderer, missing artifact, timeout, still-frame output or missing FFmpeg all fail closed. No placeholder video is substituted.

## Current scope
The canary proves transport + generation + artifact ingestion + motion QC + provenance. Identity continuity, reference-character control, audio and full Manifest graph integration are later gates.
