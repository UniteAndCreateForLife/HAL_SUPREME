from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class RenderRequest:
    task_id: str
    shot_id: str
    prompt: str
    output_dir: Path
    width: int = 1280
    height: int = 720
    fps: float = 24.0
    frames: int = 121
    seed: int = 0
    image_path: Path | None = None
    control_video_path: Path | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RenderResult:
    renderer_id: str
    provider_id: str
    model_id: str
    artifact_path: Path
    seed: int
    metadata: Mapping[str, Any] = field(default_factory=dict)


class Renderer(ABC):
    renderer_id: str
    provider_id: str
    model_id: str

    @abstractmethod
    def health(self) -> Mapping[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def capabilities(self) -> Mapping[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def render(self, request: RenderRequest) -> RenderResult:
        raise NotImplementedError
