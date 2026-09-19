from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ComfyInventory:
    node_classes: tuple[str, ...]
    checkpoint_names: tuple[str, ...]
    unet_names: tuple[str, ...]
    vae_names: tuple[str, ...]
    clip_names: tuple[str, ...]

    def video_candidates(self) -> dict[str, list[str]]:
        def matches(values: tuple[str, ...], terms: tuple[str, ...]) -> list[str]:
            return [v for v in values if any(t in v.lower() for t in terms)]
        return {
            "wan": matches(self.unet_names + self.checkpoint_names, ("wan",)),
            "ltx": matches(self.unet_names + self.checkpoint_names, ("ltx",)),
            "video_nodes": matches(self.node_classes, ("video", "wan", "ltx", "animatediff")),
        }


class ComfyUIProbe:
    def __init__(self, endpoint: str = "http://127.0.0.1:8188", timeout_s: float = 5.0):
        self.endpoint = endpoint.rstrip("/")
        self.timeout_s = timeout_s

    def _get(self, path: str) -> Any:
        with urllib.request.urlopen(self.endpoint + path, timeout=self.timeout_s) as response:
            return json.loads(response.read().decode())

    def inventory(self) -> ComfyInventory:
        info = self._get("/object_info")
        def choices(class_name: str, input_name: str) -> tuple[str, ...]:
            try:
                value = info[class_name]["input"]["required"][input_name][0]
                return tuple(str(x) for x in value) if isinstance(value, list) else ()
            except (KeyError, IndexError, TypeError):
                return ()
        return ComfyInventory(
            node_classes=tuple(sorted(info)),
            checkpoint_names=choices("CheckpointLoaderSimple", "ckpt_name"),
            unet_names=choices("UNETLoader", "unet_name"),
            vae_names=choices("VAELoader", "vae_name"),
            clip_names=choices("CLIPLoader", "clip_name"),
        )
