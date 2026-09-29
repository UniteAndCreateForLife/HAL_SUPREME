from __future__ import annotations

import os
from typing import Any


def _env_enabled(name: str, default: bool = False) -> bool:
    fallback = "true" if default else "false"
    return os.getenv(name, fallback).strip().lower() == "true"


def _optional_int(name: str) -> int | None:
    value = os.getenv(name, "").strip()
    if not value:
        return None
    try:
        parsed = int(value)
    except ValueError:
        return None
    return parsed if parsed >= 0 else None


def _optional_float(name: str) -> float | None:
    value = os.getenv(name, "").strip()
    if not value:
        return None
    try:
        parsed = float(value)
    except ValueError:
        return None
    return parsed if parsed >= 0 else None


def _capabilities() -> list[str]:
    raw = os.getenv(
        "HAL_LOCAL_NODE_CAPABILITIES",
        "audio,video,comfyui,media",
    )
    return sorted(
        {
            item.strip().lower()
            for item in raw.split(",")
            if item.strip()
        }
    )


def build_local_node_profile() -> dict[str, Any]:
    """Build an operator-declared, public-safe profile for owned local compute."""
    return {
        "schema": "hal.local-node-profile.v1",
        "enabled": _env_enabled("HAL_PROVIDER_LOCAL_ENABLED"),
        "owner_controlled": True,
        "remote_dependency": False,
        "budget_policy": "owned_compute_only",
        "capabilities": _capabilities(),
        "capacity": {
            "cpu_cores": _optional_int("HAL_LOCAL_NODE_CPU_CORES"),
            "ram_gib": _optional_float("HAL_LOCAL_NODE_RAM_GIB"),
            "gpu_model": os.getenv("HAL_LOCAL_NODE_GPU_MODEL", "").strip() or None,
            "gpu_vram_gib": _optional_float("HAL_LOCAL_NODE_GPU_VRAM_GIB"),
        },
        "disclosure": {
            "hostname": False,
            "filesystem_paths": False,
            "account_identifiers": False,
            "credentials": False,
        },
    }
