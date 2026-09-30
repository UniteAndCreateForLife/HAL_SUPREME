from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from renderers.comfyui_probe import ComfyUIProbe


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect a live ComfyUI worker for HAL video capabilities")
    parser.add_argument("--endpoint", default="http://127.0.0.1:8188")
    args = parser.parse_args()
    inv = ComfyUIProbe(args.endpoint).inventory()
    print(json.dumps({
        "node_count": len(inv.node_classes),
        "checkpoint_names": inv.checkpoint_names,
        "unet_names": inv.unet_names,
        "vae_names": inv.vae_names,
        "clip_names": inv.clip_names,
        "video_candidates": inv.video_candidates(),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
