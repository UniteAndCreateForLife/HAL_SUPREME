from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from continuity.render_binding import resolve_render_binding
from provenance.receipts import RenderReceipt
from qc.motion import require_temporal_motion
from .base import RenderRequest
from .router import CapabilityRouter


@dataclass(frozen=True)
class AcceptedRender:
    artifact_path: Path
    receipt_path: Path
    receipt: RenderReceipt


def render_and_accept(
    request: RenderRequest,
    router: CapabilityRouter,
    capability: str = "text_to_video",
) -> AcceptedRender:
    """Bind world state, render, verify motion, then commit a provenance receipt."""
    continuity = resolve_render_binding(request)
    decision = router.choose(capability)
    result = decision.renderer.render(request)

    source = result.artifact_path
    if not source.exists():
        raise FileNotFoundError(f"renderer result does not exist locally: {source}")

    artifact_dir = request.output_dir / request.task_id / request.shot_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    target = artifact_dir / "render.mp4"
    if source.resolve() != target.resolve():
        shutil.copy2(source, target)

    motion = require_temporal_motion(target)
    receipt = RenderReceipt.create(
        task_id=request.task_id,
        shot_id=request.shot_id,
        renderer_id=result.renderer_id,
        provider_id=result.provider_id,
        model_id=result.model_id,
        artifact_path=target,
        motion_evidence=motion,
        seed=result.seed,
        continuity_fingerprint=continuity.fingerprint if continuity else None,
        continuity_manifest_sha256=continuity.manifest_sha256 if continuity else None,
    )
    receipt_path = artifact_dir / "render.receipt.json"
    receipt.write(receipt_path)
    return AcceptedRender(target, receipt_path, receipt)
