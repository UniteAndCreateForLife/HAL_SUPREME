from __future__ import annotations

from typing import Any, Callable, Mapping

from .base import RenderRequest, RenderResult, Renderer


class LTXRenderer(Renderer):
    renderer_id = "ltx"
    provider_id = "local"

    def __init__(self, runner: Callable[[RenderRequest], RenderResult] | None = None, model_id: str = "ltx-video"):
        self._runner = runner
        self.model_id = model_id

    def health(self) -> Mapping[str, Any]:
        return {"health": "healthy" if self._runner else "offline", "reason": None if self._runner else "runner_not_configured"}

    def capabilities(self) -> Mapping[str, Any]:
        return {
            "text_to_video": True,
            "image_to_video": True,
            "video_to_video": False,
            "reference_identity": False,
            "control_video": False,
        }

    def render(self, request: RenderRequest) -> RenderResult:
        if self._runner is None:
            raise RuntimeError("LTX runner is not configured")
        result = self._runner(request)
        if result.renderer_id != self.renderer_id:
            raise ValueError("LTX runner returned mismatched renderer_id")
        return result
