# ComfyUI Workflow Integration

HAL uses **known-good workflow templates plus explicit bindings** instead of inventing arbitrary ComfyUI graphs at runtime.

This is intentional: ComfyUI installations vary by node pack and model family. Guessing a graph can queue invalid or semantically wrong jobs.

## Discovery
Run:

`python scripts/comfy_inventory.py --endpoint http://127.0.0.1:8188`

HAL queries `/object_info`, inventories loader choices and node classes, and reports likely Wan/LTX/video candidates.

## Enrollment
1. Build or import a working Wan/LTX workflow in ComfyUI.
2. Export it in API format.
3. Store the workflow outside Git if it contains machine-specific absolute paths; otherwise place a sanitized template under `configs/workflows/`.
4. Define bindings for prompt, seed, width, height and frame count.
5. HAL injects shot values deterministically using `WorkflowTemplate`.
6. The existing renderer pipeline submits the graph and accepts output only after artifact + motion + provenance gates pass.

## Why this is safer
HAL can discover what a worker has, but does not pretend every ComfyUI installation has the same custom nodes. Templates make the model/runtime contract explicit and testable.
