import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from qc.media_preflight import (
    MediaAuditPolicy,
    MediaPreflightError,
    evaluate_audit_evidence,
    evaluate_probe,
    probe_media,
    require_audit_preflight,
    require_media_preflight,
    require_production_preflight,
)
from qc.motion import MotionEvidenceError


def good_probe():
    return {
        "streams": [
            {
                "codec_type": "video",
                "width": 1920,
                "height": 1080,
                "avg_frame_rate": "24/1",
            },
            {"codec_type": "audio", "codec_name": "aac"},
        ],
        "format": {"duration": "5.0"},
    }


class MediaPreflightTests(unittest.TestCase):
    def test_good_probe_passes(self):
        report = evaluate_probe(good_probe())
        self.assertTrue(report["passed"])
        self.assertEqual(report["observed"]["fps"], 24.0)

    def test_missing_video_fails_closed(self):
        report = evaluate_probe(
            {"streams": [{"codec_type": "audio"}], "format": {"duration": "5"}}
        )
        self.assertFalse(report["passed"])
        self.assertFalse(report["checks"]["has_video"])

    def test_audio_can_be_required_or_optional(self):
        payload = good_probe()
        payload["streams"] = payload["streams"][:1]
        self.assertFalse(evaluate_probe(payload, require_audio=True)["passed"])
        self.assertTrue(evaluate_probe(payload, require_audio=False)["passed"])

    def test_low_resolution_or_frame_rate_fails(self):
        payload = good_probe()
        payload["streams"][0].update(
            width=160, height=90, avg_frame_rate="5/1"
        )
        report = evaluate_probe(payload)
        self.assertFalse(report["checks"]["resolution"])
        self.assertFalse(report["checks"]["frame_rate"])

    def test_probe_uses_machine_readable_ffprobe_json(self):
        seen = {}

        def runner(cmd, **kwargs):
            seen["cmd"] = cmd
            return subprocess.CompletedProcess(
                cmd, 0, json.dumps(good_probe()), ""
            )

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "x.mp4"
            path.write_bytes(b"x")
            result = probe_media(path, runner=runner)
        self.assertEqual(result["format"]["duration"], "5.0")
        self.assertEqual(seen["cmd"][0], "ffprobe")
        self.assertIn("-show_streams", seen["cmd"])
        self.assertIn("-show_format", seen["cmd"])
        self.assertIn("json", seen["cmd"])

    def test_ffprobe_error_fails_closed(self):
        def runner(cmd, **kwargs):
            return subprocess.CompletedProcess(cmd, 1, "", "broken")

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "x.mp4"
            path.write_bytes(b"x")
            with self.assertRaisesRegex(MediaPreflightError, "broken"):
                probe_media(path, runner=runner)

    def test_require_combines_structure_and_motion(self):
        def runner(cmd, **kwargs):
            return subprocess.CompletedProcess(
                cmd, 0, json.dumps(good_probe()), ""
            )

        motion = {
            "passed": True,
            "sampled_frames": 6,
            "unique_frame_hashes": 6,
        }
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "x.mp4"
            path.write_bytes(b"x")
            report = require_media_preflight(
                path,
                probe_runner=runner,
                motion_checker=lambda _: motion,
            )
        self.assertTrue(report["passed"])
        self.assertEqual(report["schema"], "hal.media_preflight.v1")
        self.assertEqual(report["motion"], motion)

    def test_motion_failure_fails_closed(self):
        def runner(cmd, **kwargs):
            return subprocess.CompletedProcess(
                cmd, 0, json.dumps(good_probe()), ""
            )

        def motion(_):
            raise MotionEvidenceError("zero-still gate failed")

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "x.mp4"
            path.write_bytes(b"x")
            with self.assertRaisesRegex(
                MediaPreflightError, "motion preflight failed"
            ):
                require_media_preflight(
                    path, probe_runner=runner, motion_checker=motion
                )

    def test_missing_file_fails_before_external_tools(self):
        with self.assertRaisesRegex(MediaPreflightError, "does not exist"):
            require_media_preflight(Path("definitely-not-here.mp4"))


def good_audits():
    return {
        "picture": {"failed_shots": 0, "minimum_text_height_px": 32},
        "audio": {
            "integrated_lufs": -16.0,
            "true_peak_dbtp": -1.2,
            "minimum_dialogue_margin_db": 8.5,
        },
        "story": {"blind_viewer_pass": True},
        "provenance": {"complete": True, "receipt_count": 4},
    }


class ProductionAuditPreflightTests(unittest.TestCase):
    def test_good_audit_evidence_passes(self):
        report = evaluate_audit_evidence(good_audits())
        self.assertTrue(report["passed"])
        self.assertEqual(report["failures"], [])

    def test_missing_audit_section_fails_closed(self):
        audits = good_audits()
        del audits["story"]
        report = evaluate_audit_evidence(audits)
        self.assertFalse(report["passed"])
        self.assertIn("story", report["failures"])

    def test_picture_and_audio_thresholds_are_enforced(self):
        audits = good_audits()
        audits["picture"]["failed_shots"] = 1
        audits["audio"]["true_peak_dbtp"] = -0.2
        failures = evaluate_audit_evidence(audits)["failures"]
        self.assertIn("picture", failures)
        self.assertIn("audio", failures)

    def test_negative_picture_failure_count_is_invalid(self):
        audits = good_audits()
        audits["picture"]["failed_shots"] = -1
        self.assertIn("picture", evaluate_audit_evidence(audits)["failures"])

    def test_story_and_provenance_fail_closed(self):
        audits = good_audits()
        audits["story"]["blind_viewer_pass"] = False
        audits["provenance"]["complete"] = False
        failures = evaluate_audit_evidence(audits)["failures"]
        self.assertIn("story", failures)
        self.assertIn("provenance", failures)

    def test_custom_phone_text_policy_and_require_gate(self):
        audits = good_audits()
        policy = MediaAuditPolicy(min_text_height_px=40)
        with self.assertRaisesRegex(MediaPreflightError, "picture"):
            require_audit_preflight(audits, policy)


    def test_production_preflight_composes_media_and_audits(self):
        def runner(*args, **kwargs):
            return subprocess.CompletedProcess(
                args[0],
                0,
                stdout=json.dumps(good_probe()),
                stderr="",
            )

        def motion(_path):
            return {"passed": True, "unique_frame_hashes": 12}

        with tempfile.TemporaryDirectory() as tmp:
            media = Path(tmp) / "candidate.mp4"
            media.write_bytes(b"fixture")
            result = require_production_preflight(
                media,
                good_audits(),
                probe_runner=runner,
                motion_checker=motion,
            )
        self.assertTrue(result["passed"])
        self.assertEqual(result["schema"], "hal.production_preflight.v1")

    def test_production_preflight_refuses_good_media_with_bad_audits(self):
        def runner(*args, **kwargs):
            return subprocess.CompletedProcess(
                args[0],
                0,
                stdout=json.dumps(good_probe()),
                stderr="",
            )

        with tempfile.TemporaryDirectory() as tmp:
            media = Path(tmp) / "candidate.mp4"
            media.write_bytes(b"fixture")
            audits = good_audits()
            audits["story"]["blind_viewer_pass"] = False
            with self.assertRaisesRegex(MediaPreflightError, "story"):
                require_production_preflight(
                    media,
                    audits,
                    probe_runner=runner,
                    motion_checker=lambda _path: {"passed": True},
                )


if __name__ == "__main__":
    unittest.main()
