from __future__ import annotations

import argparse
import json
from pathlib import Path

from renderers.base import RenderRequest
from renderers.comfyui_wan import ComfyUIWanRenderer
from renderers.pipeline import render_and_accept
from renderers.registry import RendererRegistry
from renderers.router import CapabilityRouter


def main() -> int:
    parser = argparse.ArgumentParser(description="HAL 5-second genuine-motion renderer canary")
    parser.add_argument("--workflow", required=True, type=Path, help="Prepared ComfyUI API workflow JSON")
    parser.add_argument("--prompt", default="A cinematic alien lowrider glides through a luminous impossible city, continuous physical motion")
    parser.add_argument("--endpoint", default="http://127.0.0.1:8188")
    parser.add_argument("--output", type=Path, default=Path("artifacts"))
    parser.add_argument("--seed", type=int, default=160016)
    args = parser.parse_args()

    workflow = json.loads(args.workflow.read_text(encoding="utf-8"))
    renderer = ComfyUIWanRenderer(endpoint=args.endpoint)
    registry = RendererRegistry.from_renderers([renderer])
    router = CapabilityRouter(registry, ["comfyui_wan"])
    request = RenderRequest(
        task_id="renderer-canary-v1",
        shot_id="shot-001",
        prompt=args.prompt,
        output_dir=args.output,
        width=1280,
        height=720,
        fps=24,
        frames=121,
        seed=args.seed,
        metadata={"comfy_workflow": workflow, "render_timeout_s": 1800},
    )
    accepted = render_and_accept(request, router)
    print(json.dumps({
        "artifact": str(accepted.artifact_path),
        "receipt": str(accepted.receipt_path),
        "sha256": accepted.receipt.artifact_sha256,
        "motion": accepted.receipt.motion_evidence,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
