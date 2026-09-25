from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .world_manifest import ContinuityManifestError, load_world_manifest, validate_render_binding


@dataclass(frozen=True)
class ContinuityBinding:
    manifest_path: Path
    manifest_sha256: str
    fingerprint: str


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_render_binding(request: Any) -> ContinuityBinding | None:
    """Resolve and validate a render request's optional cinematic-world binding.

    Providers receive only a derived binding. EventStore/WorkGraph remain the
    authorities that produce the manifest; this helper merely fails closed when
    a render request claims continuity but cannot prove the exact shot state.
    """
    metadata: Mapping[str, Any] = getattr(request, "metadata", {}) or {}
    manifest_value = metadata.get("continuity_manifest_path")
    required = bool(metadata.get("require_continuity_manifest", False))

    if not manifest_value:
        if required:
            raise ContinuityManifestError(
                "render request requires continuity_manifest_path but none was supplied"
            )
        return None

    path = Path(str(manifest_value)).expanduser()
    if not path.is_file():
        raise ContinuityManifestError(f"continuity manifest does not exist: {path}")

    shot_id = getattr(request, "shot_id", None)
    if not isinstance(shot_id, str) or not shot_id:
        raise ContinuityManifestError("render request requires shot_id for continuity binding")

    expected = metadata.get("continuity_fingerprint")
    if expected is not None and not isinstance(expected, str):
        raise ContinuityManifestError("continuity_fingerprint must be a string when supplied")

    manifest = load_world_manifest(path)
    fingerprint = validate_render_binding(manifest, shot_id, expected)
    return ContinuityBinding(path, _sha256(path), fingerprint)
