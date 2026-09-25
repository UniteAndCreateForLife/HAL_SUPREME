import copy
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from continuity.render_binding import resolve_render_binding
from continuity.world_manifest import (
    ContinuityManifestError,
    continuity_fingerprint,
    validate_world_manifest,
)
from provenance.receipts import RenderReceipt
from qc.continuity import ContinuityQCError, require_continuity_audit


def manifest_fixture():
    return {
        "schema_version": "hal.cinematic-world/v1",
        "world_id": "world:test-film",
        "authorities": {
            "history": "EventStore",
            "work": "WorkGraph",
            "control": "Supervisor",
            "routing": "ProviderMesh",
            "stage": "Godot",
        },
        "assets": [
            {
                "asset_id": "asset:hero:v1",
                "kind": "character",
                "artifact_ref": "artifact://hero.glb",
            },
            {
                "asset_id": "asset:shirt:black",
                "kind": "wardrobe",
                "artifact_ref": "artifact://black-shirt.glb",
            },
            {
                "asset_id": "asset:corridor:v1",
                "kind": "set",
                "artifact_ref": "artifact://corridor.glb",
            },
            {
                "asset_id": "asset:mic:v1",
                "kind": "prop",
                "artifact_ref": "artifact://mic.glb",
            },
        ],
        "entities": [
            {
                "entity_id": "hero",
                "asset_id": "asset:hero:v1",
                "persistence": "continuous",
            },
            {
                "entity_id": "mic",
                "asset_id": "asset:mic:v1",
                "persistence": "continuous",
            },
        ],
        "scenes": [
            {
                "scene_id": "corridor",
                "set_asset_id": "asset:corridor:v1",
                "anchors": {
                    "door": [0, 0, 0],
                    "mark_a": [1, 0, 2],
                },
            },
        ],
        "shots": [
            {
                "shot_id": "FL01",
                "sequence_index": 0,
                "previous_shot_id": None,
                "continuity_segment": "seg-1",
                "scene_id": "corridor",
                "placements": [
                    {"entity_id": "hero", "anchor": "door"},
                    {"entity_id": "mic", "anchor": "mark_a"},
                ],
                "continuity_state": {
                    "hero.identity": "asset:hero:v1",
                    "hero.wardrobe": "asset:shirt:black",
                    "set.geometry": "asset:corridor:v1",
                    "atmosphere.time_of_day": "night",
                },
                "inherit_keys": [],
                "transitions": {},
            },
            {
                "shot_id": "FL02",
                "sequence_index": 1,
                "previous_shot_id": "FL01",
                "continuity_segment": "seg-1",
                "scene_id": "corridor",
                "placements": [
                    {"entity_id": "hero", "anchor": "mark_a"},
                    {"entity_id": "mic", "anchor": "mark_a"},
                ],
                "continuity_state": {
                    "hero.identity": "asset:hero:v1",
                    "hero.wardrobe": "asset:shirt:black",
                    "set.geometry": "asset:corridor:v1",
                    "atmosphere.time_of_day": "night",
                },
                "inherit_keys": [
                    "hero.identity",
                    "hero.wardrobe",
                    "set.geometry",
                    "atmosphere.time_of_day",
                ],
                "transitions": {},
            },
        ],
    }


class ManifestTests(unittest.TestCase):
    def test_valid_manifest_and_fingerprint_are_stable(self):
        manifest = manifest_fixture()
        validate_world_manifest(manifest)
        self.assertEqual(
            continuity_fingerprint(manifest, "FL02"),
            continuity_fingerprint(copy.deepcopy(manifest), "FL02"),
        )

    def test_character_or_set_drift_fails_without_transition(self):
        manifest = manifest_fixture()
        manifest["shots"][1]["continuity_state"]["hero.identity"] = "asset:hero:mutated"
        with self.assertRaisesRegex(ContinuityManifestError, "without transition"):
            validate_world_manifest(manifest)

    def test_time_of_day_drift_fails_without_transition(self):
        manifest = manifest_fixture()
        manifest["shots"][1]["continuity_state"]["atmosphere.time_of_day"] = "day"
        with self.assertRaisesRegex(ContinuityManifestError, "without transition"):
            validate_world_manifest(manifest)

    def test_persistent_prop_cannot_disappear_silently(self):
        manifest = manifest_fixture()
        manifest["shots"][1]["placements"] = [
            {"entity_id": "hero", "anchor": "mark_a"}
        ]
        with self.assertRaisesRegex(ContinuityManifestError, "drops persistent entity"):
            validate_world_manifest(manifest)

    def test_explicit_transition_allows_visible_change(self):
        manifest = manifest_fixture()
        manifest["shots"][1]["continuity_state"]["atmosphere.time_of_day"] = "dawn"
        manifest["shots"][1]["transitions"]["atmosphere.time_of_day"] = {
            "from": "night",
            "to": "dawn",
            "reason": "on-screen sunrise time jump",
        }
        validate_world_manifest(manifest)


class AuditTests(unittest.TestCase):
    def test_visual_audit_passes_only_all_required_domains(self):
        domains = (
            "identity",
            "wardrobe",
            "set_geometry",
            "props",
            "lighting",
            "atmosphere",
        )
        audit = {
            "shot_id": "FL02",
            "checks": {
                domain: {"status": "pass", "confidence": 0.91}
                for domain in domains
            },
        }
        self.assertEqual(require_continuity_audit(audit)["status"], "pass")

    def test_fl06_style_drift_fails_closed(self):
        audit = {
            "shot_id": "FL06",
            "checks": {
                "identity": {"status": "fail", "confidence": 0.96},
                "wardrobe": {"status": "fail", "confidence": 0.98},
                "set_geometry": {"status": "fail", "confidence": 0.99},
                "props": {"status": "fail", "confidence": 0.94},
                "lighting": {"status": "fail", "confidence": 0.88},
                "atmosphere": {"status": "fail", "confidence": 0.97},
            },
        }
        with self.assertRaises(ContinuityQCError):
            require_continuity_audit(audit)


class RenderBindingTests(unittest.TestCase):
    def _manifest_file(self, root: Path) -> Path:
        path = root / "world.json"
        path.write_text(json.dumps(manifest_fixture()), encoding="utf-8")
        return path

    def test_required_manifest_fails_closed_when_missing(self):
        request = SimpleNamespace(
            shot_id="FL02",
            metadata={"require_continuity_manifest": True},
        )
        with self.assertRaisesRegex(
            ContinuityManifestError,
            "requires continuity_manifest_path",
        ):
            resolve_render_binding(request)

    def test_binding_hashes_manifest_and_checks_fingerprint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path = self._manifest_file(root)
            expected = continuity_fingerprint(manifest_fixture(), "FL02")
            request = SimpleNamespace(
                shot_id="FL02",
                metadata={
                    "require_continuity_manifest": True,
                    "continuity_manifest_path": str(manifest_path),
                    "continuity_fingerprint": expected,
                },
            )
            binding = resolve_render_binding(request)
            self.assertEqual(binding.fingerprint, expected)
            self.assertEqual(len(binding.manifest_sha256), 64)

    def test_receipt_preserves_continuity_binding(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "render.mp4"
            artifact.write_bytes(b"moving-video-placeholder-for-hash")
            receipt = RenderReceipt.create(
                task_id="t1",
                shot_id="FL02",
                renderer_id="fake",
                provider_id="fake",
                model_id="fake",
                artifact_path=artifact,
                motion_evidence={"status": "pass"},
                seed=7,
                continuity_fingerprint="a" * 64,
                continuity_manifest_sha256="b" * 64,
            )
            self.assertEqual(receipt.continuity_fingerprint, "a" * 64)
            self.assertEqual(receipt.continuity_manifest_sha256, "b" * 64)


if __name__ == "__main__":
    unittest.main()
