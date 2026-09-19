from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path
from typing import Any, Mapping

from .base import RenderRequest, RenderResult, Renderer


class ComfyUIWanRenderer(Renderer):
    renderer_id = "comfyui_wan"
    provider_id = "comfyui"

    def __init__(self, endpoint: str = "http://127.0.0.1:8188", model_id: str = "wan", timeout_s: float = 5.0):
        self.endpoint = endpoint.rstrip("/")
        self.model_id = model_id
        self.timeout_s = timeout_s

    def _json(self, path: str, payload: dict[str, Any] | None = None) -> Any:
        data = None if payload is None else json.dumps(payload).encode()
        req = urllib.request.Request(
            self.endpoint + path,
            data=data,
            headers={"Content-Type": "application/json"},
            method="GET" if data is None else "POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout_s) as response:
            return json.loads(response.read().decode())

    def health(self) -> Mapping[str, Any]:
        try:
            self._json("/system_stats")
            return {"health": "healthy", "endpoint": self.endpoint}
        except Exception as exc:
            return {"health": "offline", "endpoint": self.endpoint, "error": str(exc)}

    def capabilities(self) -> Mapping[str, Any]:
        return {
            "text_to_video": True,
            "image_to_video": True,
            "video_to_video": False,
            "reference_identity": False,
            "control_video": False,
        }

    def render(self, request: RenderRequest) -> RenderResult:
        workflow = request.metadata.get("comfy_workflow")
        if not isinstance(workflow, dict):
            raise ValueError("RenderRequest.metadata['comfy_workflow'] must contain a prepared ComfyUI workflow")
        queued = self._json("/prompt", {"prompt": workflow})
        prompt_id = queued["prompt_id"]
        deadline = time.monotonic() + float(request.metadata.get("render_timeout_s", 900))
        while time.monotonic() < deadline:
            history = self._json(f"/history/{prompt_id}")
            record = history.get(prompt_id)
            if record:
                outputs = record.get("outputs", {})
                candidates = []
                for node in outputs.values():
                    candidates.extend(node.get("gifs", []))
                    candidates.extend(node.get("videos", []))
                    candidates.extend(node.get("images", []))
                if candidates:
                    item = candidates[0]
                    filename = item.get("filename")
                    if not filename:
                        raise RuntimeError("ComfyUI returned output without filename")
                    # The local worker must resolve/copy this into HAL's artifact store.
                    return RenderResult(
                        renderer_id=self.renderer_id,
                        provider_id=self.provider_id,
                        model_id=self.model_id,
                        artifact_path=Path(filename),
                        seed=request.seed,
                        metadata={"prompt_id": prompt_id, "raw_output": item},
                    )
            time.sleep(1.0)
        raise TimeoutError(f"ComfyUI render timed out: {prompt_id}")
