from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .base import RenderRequest, RenderResult, Renderer


DEFAULT_NEGATIVE_PROMPT = (
    "camera shake, overexposure, static frame, frozen motion, low quality, "
    "blurred details, subtitles, watermark, malformed hands, malformed face, "
    "duplicate limbs, fused fingers, broken anatomy"
)


@dataclass(frozen=True)
class LightX2VSettings:
    python_executable: str
    model_path: Path
    config_json: Path
    lightx2v_root: Path | None = None
    timeout_s: float = 7200.0
    model_id: str = "wan2.2-ti2v-5b"

    @classmethod
    def from_env(cls) -> "LightX2VSettings":
        python_executable = os.environ.get("HAL_LIGHTX2V_PYTHON", "python")
        model_raw = os.environ.get("HAL_WAN22_TI2V5B_MODEL", "").strip()
        model_path = Path(model_raw).expanduser() if model_raw else Path("__HAL_WAN22_MODEL_NOT_CONFIGURED__")
        config_json = Path(
            os.environ.get(
                "HAL_LIGHTX2V_CONFIG",
                "configs/lightx2v/wan22_ti2v_5b_turing_8gb.json",
            )
        ).expanduser()
        root = os.environ.get("HAL_LIGHTX2V_ROOT")
        return cls(
            python_executable=python_executable,
            model_path=model_path,
            config_json=config_json,
            lightx2v_root=Path(root).expanduser() if root else None,
            timeout_s=float(os.environ.get("HAL_LIGHTX2V_TIMEOUT_S", "7200")),
        )


class LightX2VWanRenderer(Renderer):
    """HAL adapter for LightX2V's official Wan2.2 TI2V inference entrypoint."""

    renderer_id = "lightx2v_wan22"
    provider_id = "local"
    model_id = "wan2.2-ti2v-5b"

    def __init__(self, settings: LightX2VSettings | None = None):
        self.settings = settings or LightX2VSettings.from_env()
        self.model_id = self.settings.model_id

    def _resolve_config(self) -> Path:
        path = self.settings.config_json
        if path.is_absolute():
            return path
        return Path(__file__).resolve().parents[1] / path

    def health(self) -> Mapping[str, Any]:
        config = self._resolve_config()
        missing: list[str] = []
        if self.settings.model_path.name == "__HAL_WAN22_MODEL_NOT_CONFIGURED__" or not self.settings.model_path.exists():
            missing.append("model_path")
        if not config.exists():
            missing.append("config_json")
        try:
            probe = subprocess.run(
                [self.settings.python_executable, "-c", "import lightx2v; print(lightx2v.__version__)"],
                cwd=str(self.settings.lightx2v_root) if self.settings.lightx2v_root else None,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
        except Exception as exc:
            return {"health": "offline", "reason": "python_or_lightx2v_probe_failed", "error": str(exc), "missing": missing}
        if probe.returncode != 0:
            return {"health": "offline", "reason": "lightx2v_import_failed", "stderr": probe.stderr[-2000:], "missing": missing}
        if missing:
            return {"health": "degraded", "reason": "runtime_present_but_assets_missing", "missing": missing, "lightx2v_version": probe.stdout.strip()}
        return {"health": "healthy", "model_path": str(self.settings.model_path), "config_json": str(config), "lightx2v_version": probe.stdout.strip()}

    def capabilities(self) -> Mapping[str, Any]:
        return {
            "text_to_video": True,
            "image_to_video": False,
            "video_to_video": False,
            "reference_identity": False,
            "control_video": False,
            "low_vram_offload": True,
            "strict_open_source": True,
        }

    def output_path_for(self, request: RenderRequest) -> Path:
        return request.output_dir / request.task_id / request.shot_id / "lightx2v_raw.mp4"

    def build_command(self, request: RenderRequest) -> list[str]:
        output = self.output_path_for(request)
        command = [
            self.settings.python_executable,
            "-m", "lightx2v.infer",
            "--model_cls", "wan2.2",
            "--task", "t2v",
            "--model_path", str(self.settings.model_path),
            "--config_json", str(self._resolve_config()),
            "--prompt", request.prompt,
            "--num_frames", str(request.frames),
            "--size", str(request.height), str(request.width),
            "--seed", str(request.seed),
            "--save_result_path", str(output),
        ]
        negative = request.metadata.get("negative_prompt", DEFAULT_NEGATIVE_PROMPT)
        if negative:
            command += ["--negative_prompt", str(negative)]
        return command

    def render(self, request: RenderRequest) -> RenderResult:
        health = self.health()
        if health.get("health") != "healthy":
            raise RuntimeError(f"LightX2V runtime is not healthy: {health}")

        output = self.output_path_for(request)
        output.parent.mkdir(parents=True, exist_ok=True)
        log_path = output.with_suffix(".log")
        env = os.environ.copy()
        env.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
        command = self.build_command(request)

        completed = subprocess.run(
            command,
            cwd=str(self.settings.lightx2v_root) if self.settings.lightx2v_root else None,
            env=env,
            capture_output=True,
            text=True,
            timeout=float(request.metadata.get("render_timeout_s", self.settings.timeout_s)),
            check=False,
        )
        log_path.write_text(
            "COMMAND\n" + subprocess.list2cmdline(command) + "\n\nSTDOUT\n" +
            completed.stdout + "\n\nSTDERR\n" + completed.stderr,
            encoding="utf-8",
        )
        if completed.returncode != 0:
            raise RuntimeError(f"LightX2V failed rc={completed.returncode}; see {log_path}")
        if not output.exists() or output.stat().st_size == 0:
            raise FileNotFoundError(f"LightX2V reported success without output: {output}")

        return RenderResult(
            renderer_id=self.renderer_id,
            provider_id=self.provider_id,
            model_id=self.model_id,
            artifact_path=output,
            seed=request.seed,
            metadata={
                "command": command,
                "config_json": str(self._resolve_config()),
                "model_path": str(self.settings.model_path),
                "log_path": str(log_path),
            },
        )
