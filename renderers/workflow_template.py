from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from .base import RenderRequest


@dataclass(frozen=True)
class WorkflowBindings:
    prompt_node: str
    prompt_field: str = "text"
    seed_node: str | None = None
    seed_field: str = "seed"
    width_node: str | None = None
    width_field: str = "width"
    height_node: str | None = None
    height_field: str = "height"
    frames_node: str | None = None
    frames_field: str = "length"


class WorkflowTemplate:
    """Safe mutation of a known-good ComfyUI API workflow.

    HAL deliberately does not guess arbitrary node graphs. A model-specific
    template is validated once, then shot parameters are injected deterministically.
    """

    def __init__(self, workflow: dict[str, Any], bindings: WorkflowBindings):
        self.workflow = workflow
        self.bindings = bindings

    @staticmethod
    def _set(workflow: dict[str, Any], node: str | None, field: str, value: Any) -> None:
        if node is None:
            return
        if node not in workflow:
            raise KeyError(f"workflow binding node missing: {node}")
        inputs = workflow[node].get("inputs")
        if not isinstance(inputs, dict):
            raise ValueError(f"workflow node {node} has no inputs mapping")
        if field not in inputs:
            raise KeyError(f"workflow binding field missing: {node}.{field}")
        inputs[field] = value

    def build(self, request: RenderRequest) -> dict[str, Any]:
        result = copy.deepcopy(self.workflow)
        b = self.bindings
        self._set(result, b.prompt_node, b.prompt_field, request.prompt)
        self._set(result, b.seed_node, b.seed_field, request.seed)
        self._set(result, b.width_node, b.width_field, request.width)
        self._set(result, b.height_node, b.height_field, request.height)
        self._set(result, b.frames_node, b.frames_field, request.frames)
        return result
