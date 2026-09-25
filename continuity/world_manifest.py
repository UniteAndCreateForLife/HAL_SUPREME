from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


SCHEMA_VERSION = "hal.cinematic-world/v1"
REQUIRED_AUTHORITIES = {
    "history": "EventStore",
    "work": "WorkGraph",
    "control": "Supervisor",
    "routing": "ProviderMesh",
    "stage": "Godot",
}

ENVIRONMENT_POLICIES = {
    "blockout",
    "photoreal_from_capture",
    "generated_photoreal",
}
ENVIRONMENT_SOURCE_MODES = {
    "single_image",
    "multi_image",
    "video",
    "panorama",
    "photogrammetry",
    "generated_multiview",
}
FINAL_CAPTURE_SOURCE_MODES = {"multi_image", "video", "photogrammetry"}
VISUAL_REPRESENTATIONS = {"gaussian_splat", "textured_mesh", "hybrid"}
GEOMETRY_CONFIDENCE = {"measured", "reconstructed", "inferred"}


class ContinuityManifestError(ValueError):
    """Raised when a cinematic world manifest violates HAL continuity rules."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ContinuityManifestError(message)


def _index(items: list[Mapping[str, Any]], key: str, label: str) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for item in items:
        value = item.get(key)
        _require(isinstance(value, str) and value.strip(), f"{label} missing {key}")
        _require(value not in result, f"duplicate {label} {key}={value!r}")
        result[value] = item
    return result


def _validate_environment_profile(asset_id: str, asset: Mapping[str, Any]) -> None:
    profile = asset.get("environment_profile")
    if profile is None:
        return
    _require(
        asset.get("kind") in {"set", "environment"},
        f"asset {asset_id!r} environment_profile is only valid for set/environment assets",
    )
    _require(
        isinstance(profile, Mapping),
        f"asset {asset_id!r} environment_profile must be a mapping",
    )
    fidelity = profile.get("fidelity_target")
    _require(
        fidelity in ENVIRONMENT_POLICIES,
        f"asset {asset_id!r} has invalid environment fidelity_target",
    )
    source_mode = profile.get("source_mode")
    _require(
        source_mode in ENVIRONMENT_SOURCE_MODES,
        f"asset {asset_id!r} has invalid environment source_mode",
    )
    source_refs = profile.get("source_refs")
    _require(
        isinstance(source_refs, list)
        and all(isinstance(ref, str) and ref for ref in source_refs),
        f"asset {asset_id!r} environment source_refs must be a list of strings",
    )
    visual_representation = profile.get("visual_representation")
    _require(
        visual_representation in VISUAL_REPRESENTATIONS,
        f"asset {asset_id!r} has invalid visual_representation",
    )
    _require(
        isinstance(profile.get("visual_artifact_ref"), str)
        and profile["visual_artifact_ref"],
        f"asset {asset_id!r} requires environment visual_artifact_ref",
    )
    _require(
        isinstance(profile.get("collision_artifact_ref"), str)
        and profile["collision_artifact_ref"],
        f"asset {asset_id!r} requires a separate collision_artifact_ref",
    )
    confidence = profile.get("geometry_confidence")
    _require(
        confidence in GEOMETRY_CONFIDENCE,
        f"asset {asset_id!r} has invalid geometry_confidence",
    )

    if fidelity == "photoreal_from_capture":
        _require(
            source_mode in FINAL_CAPTURE_SOURCE_MODES,
            f"asset {asset_id!r} photoreal_from_capture requires multi_image, video, or photogrammetry input",
        )
        min_sources = 3 if source_mode == "multi_image" else 1
        _require(
            len(source_refs) >= min_sources,
            f"asset {asset_id!r} photoreal_from_capture has insufficient source capture",
        )
        _require(
            confidence in {"measured", "reconstructed"},
            f"asset {asset_id!r} photoreal_from_capture cannot use inferred-only geometry",
        )


def load_world_manifest(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_world_manifest(data)
    return data


def validate_world_manifest(manifest: Mapping[str, Any]) -> None:
    _require(manifest.get("schema_version") == SCHEMA_VERSION, f"schema_version must be {SCHEMA_VERSION!r}")
    _require(isinstance(manifest.get("world_id"), str) and manifest["world_id"], "world_id is required")

    authorities = manifest.get("authorities")
    _require(isinstance(authorities, Mapping), "authorities mapping is required")
    for role, expected in REQUIRED_AUTHORITIES.items():
        _require(authorities.get(role) == expected, f"authorities.{role} must remain {expected}")

    assets = _index(list(manifest.get("assets") or []), "asset_id", "asset")
    entities = _index(list(manifest.get("entities") or []), "entity_id", "entity")
    scenes = _index(list(manifest.get("scenes") or []), "scene_id", "scene")
    shots = list(manifest.get("shots") or [])
    _require(bool(assets), "at least one asset is required")
    _require(bool(scenes), "at least one scene is required")
    _require(bool(shots), "at least one shot is required")

    for asset_id, asset in assets.items():
        _require(
            asset.get("kind") in {
                "character", "wardrobe", "prop", "set",
                "environment", "vehicle", "rig", "material",
            },
            f"asset {asset_id!r} has unsupported kind",
        )
        _require(
            isinstance(asset.get("artifact_ref"), str) and asset["artifact_ref"],
            f"asset {asset_id!r} requires artifact_ref",
        )
        fingerprint = asset.get("artifact_sha256")
        if fingerprint is not None:
            _require(
                isinstance(fingerprint, str) and len(fingerprint) == 64,
                f"asset {asset_id!r} artifact_sha256 must be 64 hex characters",
            )
            try:
                int(fingerprint, 16)
            except ValueError as exc:
                raise ContinuityManifestError(
                    f"asset {asset_id!r} artifact_sha256 is not hexadecimal"
                ) from exc
        _validate_environment_profile(asset_id, asset)

    for entity_id, entity in entities.items():
        asset_id = entity.get("asset_id")
        _require(asset_id in assets, f"entity {entity_id!r} references unknown asset {asset_id!r}")
        _require(
            entity.get("persistence", "continuous") in {"continuous", "scene", "shot"},
            f"entity {entity_id!r} has invalid persistence",
        )

    for scene_id, scene in scenes.items():
        set_asset_id = scene.get("set_asset_id")
        _require(set_asset_id in assets, f"scene {scene_id!r} references unknown set asset {set_asset_id!r}")
        _require(
            assets[set_asset_id].get("kind") in {"set", "environment"},
            f"scene {scene_id!r} set_asset_id must point to set/environment",
        )
        anchors = scene.get("anchors", {})
        _require(isinstance(anchors, Mapping), f"scene {scene_id!r} anchors must be a mapping")
        environment_policy = scene.get("environment_policy")
        if environment_policy is not None:
            _require(
                environment_policy in ENVIRONMENT_POLICIES,
                f"scene {scene_id!r} has invalid environment_policy",
            )
            profile = assets[set_asset_id].get("environment_profile")
            _require(
                isinstance(profile, Mapping),
                f"scene {scene_id!r} requires an environment_profile on set asset {set_asset_id!r}",
            )
            _require(
                profile.get("fidelity_target") == environment_policy,
                f"scene {scene_id!r} environment_policy does not match set asset fidelity_target",
            )

    shot_index = _index(shots, "shot_id", "shot")
    sequence = sorted(shots, key=lambda shot: shot.get("sequence_index", -1))
    expected_indices = list(range(len(sequence)))
    actual_indices = [shot.get("sequence_index") for shot in sequence]
    _require(
        actual_indices == expected_indices,
        f"shot sequence_index values must be contiguous starting at 0; got {actual_indices!r}",
    )

    seen: set[str] = set()
    previous_by_segment: dict[str, Mapping[str, Any]] = {}
    for shot in sequence:
        shot_id = shot["shot_id"]
        scene_id = shot.get("scene_id")
        _require(scene_id in scenes, f"shot {shot_id!r} references unknown scene {scene_id!r}")
        segment = shot.get("continuity_segment")
        _require(
            isinstance(segment, str) and segment,
            f"shot {shot_id!r} requires continuity_segment",
        )

        previous_shot_id = shot.get("previous_shot_id")
        if previous_shot_id is not None:
            _require(
                previous_shot_id in shot_index,
                f"shot {shot_id!r} previous_shot_id is unknown",
            )
            _require(
                previous_shot_id in seen,
                f"shot {shot_id!r} previous_shot_id must point backward",
            )

        placements = shot.get("placements") or []
        _require(isinstance(placements, list), f"shot {shot_id!r} placements must be a list")
        placed_entities: set[str] = set()
        for placement in placements:
            entity_id = placement.get("entity_id")
            _require(
                entity_id in entities,
                f"shot {shot_id!r} references unknown entity {entity_id!r}",
            )
            _require(
                entity_id not in placed_entities,
                f"shot {shot_id!r} places entity {entity_id!r} more than once",
            )
            placed_entities.add(entity_id)
            anchor = placement.get("anchor")
            if anchor is not None:
                _require(
                    anchor in scenes[scene_id].get("anchors", {}),
                    f"shot {shot_id!r} uses unknown anchor {anchor!r} in scene {scene_id!r}",
                )

        continuity_state = shot.get("continuity_state") or {}
        _require(
            isinstance(continuity_state, Mapping),
            f"shot {shot_id!r} continuity_state must be a mapping",
        )
        inherit_keys = shot.get("inherit_keys") or []
        _require(
            isinstance(inherit_keys, list) and all(isinstance(x, str) for x in inherit_keys),
            f"shot {shot_id!r} inherit_keys must be a list of strings",
        )
        transitions = shot.get("transitions") or {}
        _require(
            isinstance(transitions, Mapping),
            f"shot {shot_id!r} transitions must be a mapping",
        )

        previous = previous_by_segment.get(segment)
        if previous is not None:
            previous_state = previous.get("continuity_state") or {}
            for key in inherit_keys:
                _require(
                    key in previous_state,
                    f"shot {shot_id!r} inherits missing key {key!r}",
                )
                _require(
                    key in continuity_state,
                    f"shot {shot_id!r} omits inherited key {key!r}",
                )
                if continuity_state[key] != previous_state[key]:
                    transition = transitions.get(key)
                    _require(
                        isinstance(transition, Mapping),
                        f"shot {shot_id!r} changes locked continuity key {key!r} without transition",
                    )
                    _require(
                        transition.get("from") == previous_state[key]
                        and transition.get("to") == continuity_state[key],
                        f"shot {shot_id!r} transition for {key!r} does not match state change",
                    )
                    _require(
                        isinstance(transition.get("reason"), str)
                        and transition["reason"].strip(),
                        f"shot {shot_id!r} transition for {key!r} requires reason",
                    )

            previous_entities = {
                p["entity_id"] for p in previous.get("placements") or []
            }
            current_entities = placed_entities
            for entity_id in previous_entities - current_entities:
                if entities[entity_id].get("persistence", "continuous") == "continuous":
                    removal_key = f"entity:{entity_id}:presence"
                    transition = transitions.get(removal_key)
                    _require(
                        isinstance(transition, Mapping)
                        and transition.get("to") is False,
                        f"shot {shot_id!r} drops persistent entity {entity_id!r} "
                        "without explicit exit transition",
                    )

        previous_by_segment[segment] = shot
        seen.add(shot_id)


def continuity_fingerprint(manifest: Mapping[str, Any], shot_id: str) -> str:
    validate_world_manifest(manifest)
    shot = next(
        (item for item in manifest["shots"] if item["shot_id"] == shot_id),
        None,
    )
    _require(shot is not None, f"unknown shot_id {shot_id!r}")
    payload = {
        "schema_version": manifest["schema_version"],
        "world_id": manifest["world_id"],
        "shot_id": shot_id,
        "scene_id": shot["scene_id"],
        "continuity_segment": shot["continuity_segment"],
        "placements": shot.get("placements", []),
        "continuity_state": shot.get("continuity_state", {}),
        "inherit_keys": shot.get("inherit_keys", []),
    }
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_render_binding(
    manifest: Mapping[str, Any],
    shot_id: str,
    expected_fingerprint: str | None = None,
) -> str:
    fingerprint = continuity_fingerprint(manifest, shot_id)
    if expected_fingerprint is not None:
        _require(
            fingerprint == expected_fingerprint,
            f"continuity fingerprint mismatch for shot {shot_id!r}: "
            f"expected {expected_fingerprint}, got {fingerprint}",
        )
    return fingerprint
