from __future__ import annotations

import argparse
import json
from pathlib import Path

from renderers.base import RenderRequest
from renderers.lightx2v_wan import LightX2VWanRenderer
from renderers.pipeline import render_and_accept
from renderers.registry import RendererRegistry
from renderers.router import CapabilityRouter


DEFAULT_PROMPT = (
    "Photoreal cinematic night corridor, damp concrete and oxidized steel, "
    "slow forward camera motion, cloth and hanging cables moving naturally in "
    "airflow, physically plausible lighting, subtle volumetric haze, deep "
    "parallax, realistic materials, continuous motion, no text."
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--seed", type=int, default=731)
    parser.add_argument("--task-id", default="nightmare_v3")
    parser.add_argument("--shot-id", default="lightx2v_canary_001")
    args = parser.parse_args()

    renderer = LightX2VWanRenderer()
    registry = RendererRegistry.from_renderers([renderer])
    router = CapabilityRouter(registry, [renderer.renderer_id])

    request = RenderRequest(
        task_id=args.task_id,
        shot_id=args.shot_id,
        prompt=args.prompt,
        output_dir=args.output_dir,
        width=832,
        height=480,
        fps=24.0,
        frames=121,
        seed=args.seed,
        metadata={
            "render_timeout_s": 14400,
            "purpose": "5-second photoreal genuine-motion canary",
        },
    )

    accepted = render_and_accept(request, router, capability="text_to_video")
    print(json.dumps({
        "status": "accepted",
        "artifact_path": str(accepted.artifact_path),
        "receipt_path": str(accepted.receipt_path),
        "renderer_id": accepted.receipt.renderer_id,
        "model_id": accepted.receipt.model_id,
        "seed": accepted.receipt.seed,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
