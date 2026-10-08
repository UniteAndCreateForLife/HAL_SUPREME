from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from renderers.base import RenderRequest
from renderers.comfyui_wan import ComfyUIWanRenderer
from renderers.pipeline import render_and_accept
from renderers.registry import RendererRegistry
from renderers.router import CapabilityRouter


def main() -> int:
    parser = argparse.ArgumentParser(description="HAL genuine-motion renderer canary")
    parser.add_argument("--workflow", required=True, type=Path, help="Prepared ComfyUI API workflow JSON")
    parser.add_argument("--bindings", required=True, type=Path, help="WorkflowBindings JSON for prompt/seed/size/frame injection")
    parser.add_argument("--output-node", help="ComfyUI node ID that must contain the final artifact")
    parser.add_argument(
        "--prompt",
        default="A cinematic alien lowrider glides through a luminous impossible city, continuous physical motion",
    )
    parser.add_argument("--endpoint", default="http://127.0.0.1:8188")
    parser.add_argument("--output", type=Path, default=Path("artifacts"))
    parser.add_argument("--seed", type=int, default=160016)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--fps", type=float, default=24.0)
    parser.add_argument("--frames", type=int, default=121)
    args = parser.parse_args()

    workflow = json.loads(args.workflow.read_text(encoding="utf-8"))
    metadata = {
        "comfy_workflow": workflow,
        "render_timeout_s": 1800,
        "render_download_timeout_s": 120,
        "video_quality_policy": {
            "expected_duration_s": args.frames / args.fps,
            "duration_tolerance_s": 1.0,
            "minimum_width": args.width,
            "minimum_height": args.height,
            "minimum_fps": max(12.0, args.fps * 0.75),
            "deep_scan": True,
            "freeze_threshold_s": 1.5,
            "max_freeze_s": 2.0,
            "black_threshold_s": 0.75,
            "max_black_s": 1.5,
        },
    }
    if args.bindings:
        metadata["comfy_bindings"] = json.loads(args.bindings.read_text(encoding="utf-8"))
    if args.output_node:
        metadata["comfy_output_node"] = args.output_node

    renderer = ComfyUIWanRenderer(endpoint=args.endpoint)
    registry = RendererRegistry.from_renderers([renderer])
    router = CapabilityRouter(registry, ["comfyui_wan"])
    request = RenderRequest(
        task_id="renderer-canary-v2",
        shot_id="shot-001",
        prompt=args.prompt,
        output_dir=args.output,
        width=args.width,
        height=args.height,
        fps=args.fps,
        frames=args.frames,
        seed=args.seed,
        metadata=metadata,
    )
    accepted = render_and_accept(request, router)
    print(json.dumps({
        "artifact": str(accepted.artifact_path),
        "receipt": str(accepted.receipt_path),
        "sha256": accepted.receipt.artifact_sha256,
        "motion": accepted.receipt.motion_evidence,
        "quality": accepted.receipt.quality_evidence,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
