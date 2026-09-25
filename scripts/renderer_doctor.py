from __future__ import annotations

import json

from renderers.comfyui_wan import ComfyUIWanRenderer
from renderers.lightx2v_wan import LightX2VWanRenderer
from renderers.ltx import LTXRenderer
from renderers.registry import RendererRegistry


def main() -> int:
    registry = RendererRegistry.from_renderers([
        LightX2VWanRenderer(),
        ComfyUIWanRenderer(),
        LTXRenderer(),
    ])
    report = {}
    for renderer_id in ("lightx2v_wan22", "comfyui_wan", "ltx"):
        renderer = registry.get(renderer_id)
        report[renderer_id] = {
            "health": dict(renderer.health()),
            "capabilities": dict(renderer.capabilities()),
            "model_id": renderer.model_id,
        }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
