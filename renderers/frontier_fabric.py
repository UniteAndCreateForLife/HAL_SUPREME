from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .open_source_policy import require_strict_open_source


Tier = Literal["local_8gb", "workstation_24gb", "large_gpu", "frontier_cluster"]


@dataclass(frozen=True)
class HardwareProfile:
    vram_gb: float
    ram_gb: float
    hopper_gpus: int = 0


@dataclass(frozen=True)
class VideoFabricPlan:
    tier: Tier
    primary_world_model: str
    secondary_world_model: str | None
    performance_model: str
    gesture_model: str
    longform_sync_model: str
    inference_engine: str
    native_render: str
    delivery_master: str
    notes: tuple[str, ...]


def _strict(model_id: str) -> str:
    require_strict_open_source(model_id)
    return model_id


def plan_strict_video_fabric(hw: HardwareProfile) -> VideoFabricPlan:
    if hw.vram_gb <= 0 or hw.ram_gb <= 0:
        raise ValueError("hardware memory values must be positive")

    # HAL's known local target is an 8 GB-class NVIDIA card with abundant host RAM.
    # Use model quantization + CPU/GPU offload rather than pretending full precision
    # frontier weights fit in local VRAM.
    if hw.vram_gb < 12:
        if hw.ram_gb < 32:
            raise ValueError("local_8gb video fabric requires at least 32 GB host RAM for offload")
        return VideoFabricPlan(
            tier="local_8gb",
            primary_world_model=_strict("wan2.2-ti2v-5b"),
            secondary_world_model=_strict("kandinsky-5-video-lite"),
            performance_model=_strict("wan2.2-s2v-14b"),
            gesture_model=_strict("wan2.2-animate-14b"),
            longform_sync_model=_strict("infinitetalk"),
            inference_engine="LightX2V/ComfyUI-GGUF + block/phase CPU offload",
            native_render="480p/720p shot renders, short verified clips",
            delivery_master="1080p/24 via verified upscale/interpolation/mastering",
            notes=(
                "Prefer Wan2.2 TI2V-5B Q4/Q5 GGUF for ordinary shots.",
                "Use LightX2V 4-step/distilled Wan lanes where compatible.",
                "Do not load full 14B specialist weights simultaneously; route one heavy job at a time.",
                "Use Blender/Godot canonical assets as reference frames, pose and continuity anchors.",
            ),
        )

    if hw.vram_gb < 48:
        return VideoFabricPlan(
            tier="workstation_24gb",
            primary_world_model=_strict("wan2.2-ti2v-5b"),
            secondary_world_model=_strict("kandinsky-5-video-lite"),
            performance_model=_strict("wan2.2-s2v-14b"),
            gesture_model=_strict("wan2.2-animate-14b"),
            longform_sync_model=_strict("infinitetalk"),
            inference_engine="LightX2V + native Diffusers/ComfyUI where memory permits",
            native_render="720p/24 prioritized",
            delivery_master="1080p/24 or higher after QC",
            notes=(
                "Use A14B Wan jobs through aggressive offload/quantization as needed.",
                "Generate multiple candidates for hero shots and select by QC.",
            ),
        )

    if hw.vram_gb < 80 and hw.hopper_gpus < 8:
        return VideoFabricPlan(
            tier="large_gpu",
            primary_world_model=_strict("kandinsky-5-video-pro"),
            secondary_world_model=_strict("wan2.2-t2v-a14b"),
            performance_model=_strict("wan2.2-s2v-14b"),
            gesture_model=_strict("wan2.2-animate-14b"),
            longform_sync_model=_strict("infinitetalk"),
            inference_engine="native multi-model workers with selective offload",
            native_render="HD hero shots plus 720p specialist shots",
            delivery_master="1080p/24+",
            notes=(
                "Kandinsky 5 Pro is the clean MIT high-quality world renderer.",
                "Wan2.2 remains the specialist for speech, pose and character animation.",
            ),
        )

    return VideoFabricPlan(
        tier="frontier_cluster",
        primary_world_model=_strict("kandinsky-5-video-pro"),
        secondary_world_model=_strict("step-video-t2v"),
        performance_model=_strict("wan2.2-s2v-14b"),
        gesture_model=_strict("wan2.2-animate-14b"),
        longform_sync_model=_strict("infinitetalk"),
        inference_engine="distributed native workers; MAGI-2 remains quarantined until dependency audit",
        native_render="HD/1080p candidate generation",
        delivery_master="1080p/24+ with per-shot A/B selection",
        notes=(
            "Do not promote MAGI-2 Preview into strict mode until its Stable Audio dependency is license-audited or replaced.",
            "MiniMax H3 remains disabled because its current community license excludes the United States.",
            "Use ensemble selection rather than assuming one foundation model wins every shot category.",
        ),
    )
