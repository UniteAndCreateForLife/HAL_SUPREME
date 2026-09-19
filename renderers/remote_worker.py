from __future__ import annotations

import json
import urllib.request
from pathlib import Path
from typing import Any, Mapping

from .base import RenderRequest, RenderResult, Renderer


class RemoteHALVideoWorker(Renderer):
    """Provider-agnostic HTTP boundary for any HAL-controlled GPU worker."""

    renderer_id = "remote_hal_video"
    provider_id = "hal-worker"

    def __init__(self, endpoint: str, model_id: str = "unknown", token: str | None = None, timeout_s: float = 10.0):
        self.endpoint = endpoint.rstrip("/")
        self.model_id = model_id
        self.token = token
        self.timeout_s = timeout_s

    def _request(self, path: str, payload: dict[str, Any] | None = None) -> Any:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        data = None if payload is None else json.dumps(payload).encode()
        req = urllib.request.Request(self.endpoint + path, data=data, headers=headers,
                                     method="GET" if data is None else "POST")
        with urllib.request.urlopen(req, timeout=self.timeout_s) as response:
            return json.loads(response.read().decode())

    def health(self) -> Mapping[str, Any]:
        try:
            result = self._request("/v1/health")
            return {"health": result.get("health", "unknown"), "endpoint": self.endpoint}
        except Exception as exc:
            return {"health": "offline", "endpoint": self.endpoint, "error": str(exc)}

    def capabilities(self) -> Mapping[str, Any]:
        try:
            return self._request("/v1/capabilities")
        except Exception:
            return {}

    def render(self, request: RenderRequest) -> RenderResult:
        result = self._request("/v1/render", {
            "task_id": request.task_id, "shot_id": request.shot_id, "prompt": request.prompt,
            "width": request.width, "height": request.height, "fps": request.fps,
            "frames": request.frames, "seed": request.seed,
        })
        path = result.get("artifact_path")
        if not path:
            raise RuntimeError("remote worker returned no artifact_path")
        return RenderResult(
            renderer_id=self.renderer_id,
            provider_id=str(result.get("provider_id", self.provider_id)),
            model_id=str(result.get("model_id", self.model_id)),
            artifact_path=Path(path),
            seed=request.seed,
            metadata={"worker_receipt": result.get("receipt")},
        )
