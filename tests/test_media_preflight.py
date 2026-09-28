import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from qc.media_preflight import (
    MediaPreflightError,
    evaluate_probe,
    probe_media,
    require_media_preflight,
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


if __name__ == "__main__":
    unittest.main()
