from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path

from renderers.frontier_fabric import HardwareProfile, plan_strict_video_fabric
from renderers.lightx2v_wan import LightX2VSettings, LightX2VWanRenderer


def _run(command: list[str], timeout: float = 30.0) -> dict:
    try:
        p = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
        return {"ok": p.returncode == 0, "returncode": p.returncode, "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def _nvidia() -> dict:
    if not shutil.which("nvidia-smi"):
        return {"ok": False, "reason": "nvidia-smi_not_found"}
    query = _run(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader,nounits"])
    if not query.get("ok"):
        return query
    first = query["stdout"].splitlines()[0]
    parts = [p.strip() for p in first.split(",")]
    if len(parts) < 3:
        return {"ok": False, "reason": "unexpected_nvidia_smi_output", "raw": query["stdout"]}
    try:
        vram_gb = float(parts[1]) / 1024.0
    except ValueError:
        vram_gb = 0.0
    return {"ok": True, "name": parts[0], "vram_gb": round(vram_gb, 2), "driver": parts[2], "raw": query["stdout"]}


def _ram_gb() -> float:
    try:
        import psutil
        return round(psutil.virtual_memory().total / (1024**3), 2)
    except Exception:
        if os.name == "nt":
            q = _run(["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory"])
            if q.get("ok"):
                try:
                    return round(float(q["stdout"]) / (1024**3), 2)
                except ValueError:
                    pass
    return 0.0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", type=Path)
    parser.add_argument("--config-json", type=Path)
    parser.add_argument("--python", dest="python_executable")
    args = parser.parse_args()

    settings = LightX2VSettings.from_env()
    if args.model_path or args.config_json or args.python_executable:
        settings = LightX2VSettings(
            python_executable=args.python_executable or settings.python_executable,
            model_path=args.model_path or settings.model_path,
            config_json=args.config_json or settings.config_json,
            lightx2v_root=settings.lightx2v_root,
            timeout_s=settings.timeout_s,
        )

    gpu = _nvidia()
    ram = _ram_gb()
    plan = None
    if gpu.get("ok") and gpu.get("vram_gb", 0) > 0 and ram > 0:
        try:
            p = plan_strict_video_fabric(HardwareProfile(vram_gb=float(gpu["vram_gb"]), ram_gb=ram))
            plan = {
                "tier": p.tier,
                "primary_world_model": p.primary_world_model,
                "secondary_world_model": p.secondary_world_model,
                "inference_engine": p.inference_engine,
                "native_render": p.native_render,
                "delivery_master": p.delivery_master,
            }
        except Exception as exc:
            plan = {"error": str(exc)}

    renderer = LightX2VWanRenderer(settings)
    health = dict(renderer.health())
    report = {
        "schema": "hal.nightmare-runtime-doctor.v1",
        "gpu": gpu,
        "ram_gb": ram,
        "lightx2v": health,
        "fabric_plan": plan,
        "environment": {
            "HAL_LIGHTX2V_PYTHON": os.environ.get("HAL_LIGHTX2V_PYTHON"),
            "HAL_LIGHTX2V_ROOT": os.environ.get("HAL_LIGHTX2V_ROOT"),
            "HAL_WAN22_TI2V5B_MODEL": os.environ.get("HAL_WAN22_TI2V5B_MODEL"),
            "HAL_LIGHTX2V_CONFIG": os.environ.get("HAL_LIGHTX2V_CONFIG"),
        },
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if gpu.get("ok") and health.get("health") == "healthy" else 2


if __name__ == "__main__":
    raise SystemExit(main())
