from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Mapping

from .base import RenderRequest, RenderResult, Renderer
from .workflow_template import WorkflowBindings, WorkflowTemplate


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

    def _bytes(self, path: str, *, timeout_s: float | None = None) -> bytes:
        req = urllib.request.Request(self.endpoint + path, method="GET")
        with urllib.request.urlopen(req, timeout=timeout_s or self.timeout_s) as response:
            return response.read()

    def health(self) -> Mapping[str, Any]:
        try:
            self._json("/system_stats")
            return {"health": "healthy", "endpoint": self.endpoint}
        except Exception as exc:
            return {"health": "offline", "endpoint": self.endpoint, "error": str(exc)}

    def capabilities(self) -> Mapping[str, Any]:
        return {
            "text_to_video": True,
            "image_to_video": False,
            "video_to_video": False,
            "reference_identity": False,
            "control_video": False,
        }

    @staticmethod
    def _bound_workflow(request: RenderRequest) -> dict[str, Any]:
        workflow = request.metadata.get("comfy_workflow")
        if not isinstance(workflow, dict):
            raise ValueError("RenderRequest.metadata['comfy_workflow'] must contain a prepared ComfyUI workflow")
        bindings = request.metadata.get("comfy_bindings")
        if bindings is None:
            return workflow
        if isinstance(bindings, dict):
            bindings = WorkflowBindings(**bindings)
        if not isinstance(bindings, WorkflowBindings):
            raise TypeError("RenderRequest.metadata['comfy_bindings'] must be a mapping or WorkflowBindings")
        return WorkflowTemplate(workflow, bindings).build(request)

    @staticmethod
    def _candidates(record: Mapping[str, Any], preferred_node: str | None = None) -> list[dict[str, Any]]:
        outputs = record.get("outputs") or {}
        if preferred_node is not None:
            if preferred_node not in outputs:
                raise RuntimeError(f"configured ComfyUI output node missing from history: {preferred_node}")
            nodes = [outputs[preferred_node]]
        else:
            nodes = list(outputs.values())
        candidates: list[dict[str, Any]] = []
        for kind in ("videos", "gifs", "images"):
            for node in nodes:
                for item in node.get(kind, []) or []:
                    if isinstance(item, dict):
                        candidates.append(item)
        return candidates

    @staticmethod
    def _safe_component(value: str) -> str:
        return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._") or "artifact"

    def _download_candidate(self, item: Mapping[str, Any], request: RenderRequest) -> Path:
        filename = item.get("filename")
        if not filename:
            raise RuntimeError("ComfyUI returned output without filename")
        params = urllib.parse.urlencode({
            "filename": filename,
            "subfolder": item.get("subfolder") or "",
            "type": item.get("type") or "output",
        })
        data = self._bytes(
            f"/view?{params}",
            timeout_s=float(request.metadata.get("render_download_timeout_s", 120)),
        )
        suffix = Path(str(filename)).suffix or ".bin"
        staging = request.output_dir / ".staging"
        staging.mkdir(parents=True, exist_ok=True)
        target = staging / (
            f"{self._safe_component(request.task_id)}-"
            f"{self._safe_component(request.shot_id)}-"
            f"{self._safe_component(Path(str(filename)).stem)}{suffix}"
        )
        target.write_bytes(data)
        return target

    def render(self, request: RenderRequest) -> RenderResult:
        workflow = self._bound_workflow(request)
        queued = self._json("/prompt", {"prompt": workflow})
        prompt_id = queued["prompt_id"]
        deadline = time.monotonic() + float(request.metadata.get("render_timeout_s", 900))
        preferred_node = request.metadata.get("comfy_output_node")
        while time.monotonic() < deadline:
            history = self._json(f"/history/{prompt_id}")
            record = history.get(prompt_id)
            if record:
                candidates = self._candidates(record, str(preferred_node) if preferred_node is not None else None)
                if candidates:
                    item = candidates[0]
                    artifact_path = self._download_candidate(item, request)
                    return RenderResult(
                        renderer_id=self.renderer_id,
                        provider_id=self.provider_id,
                        model_id=self.model_id,
                        artifact_path=artifact_path,
                        seed=request.seed,
                        metadata={"prompt_id": prompt_id, "raw_output": item},
                    )
            time.sleep(1.0)
        raise TimeoutError(f"ComfyUI render timed out: {prompt_id}")
