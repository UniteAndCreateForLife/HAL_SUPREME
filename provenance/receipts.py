from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class RenderReceipt:
    task_id: str
    shot_id: str
    renderer_id: str
    provider_id: str
    model_id: str
    artifact_sha256: str
    motion_evidence: dict[str, Any]
    seed: int
    committed_at: str
    continuity_fingerprint: str | None = None
    continuity_manifest_sha256: str | None = None

    @classmethod
    def create(
        cls,
        *,
        task_id: str,
        shot_id: str,
        renderer_id: str,
        provider_id: str,
        model_id: str,
        artifact_path: Path,
        motion_evidence: dict[str, Any],
        seed: int,
        continuity_fingerprint: str | None = None,
        continuity_manifest_sha256: str | None = None,
    ) -> "RenderReceipt":
        return cls(
            task_id=task_id,
            shot_id=shot_id,
            renderer_id=renderer_id,
            provider_id=provider_id,
            model_id=model_id,
            artifact_sha256=sha256_file(artifact_path),
            motion_evidence=motion_evidence,
            seed=seed,
            committed_at=datetime.now(timezone.utc).isoformat(),
            continuity_fingerprint=continuity_fingerprint,
            continuity_manifest_sha256=continuity_manifest_sha256,
        )

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(asdict(self), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
