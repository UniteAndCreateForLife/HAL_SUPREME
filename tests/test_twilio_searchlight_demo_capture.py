from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from services.twilio_searchlight_demo.demo_capture import (
    SCENES,
    build_ffmpeg_command,
    render_scene_html,
    render_srt,
    validate_html,
    write_manifest,
)


class TwilioDemoCaptureTests(unittest.TestCase):
    def test_plan_is_bounded_and_covers_judge_evidence(self) -> None:
        self.assertGreaterEqual(len(SCENES), 5)
        self.assertLessEqual(sum(scene.duration_seconds for scene in SCENES), 300)
        anchors = {scene.anchor for scene in SCENES}
        self.assertIn("boundary-title", anchors)
        self.assertIn("architecture-title", anchors)
        self.assertIn("criteria-title", anchors)
        self.assertIn("state-title", anchors)

    def test_html_must_be_source_bound_and_fail_closed(self) -> None:
        sha = "a" * 40
        anchors = "".join(
            f'<h2 id="{scene.anchor}"></h2>' for scene in SCENES if scene.anchor
        )
        valid = (
            f"<html><code>{sha}</code>{anchors}"
            "LIVE TWILIO NOT VERIFIED NOT VERIFIED</html>"
        )
        validate_html(valid, sha)
        with self.assertRaisesRegex(ValueError, "source SHA"):
            validate_html(valid, "b" * 40)
        with self.assertRaisesRegex(ValueError, "live boundary"):
            validate_html(f"<html><code>{sha}</code></html>", sha)

    def test_ffmpeg_command_is_silent_h264_and_bounded(self) -> None:
        paths = [Path(f"shot-{index}.png") for index in range(len(SCENES))]
        command = build_ffmpeg_command(Path("ffmpeg"), paths, Path("demo.mp4"))
        rendered = " ".join(str(part) for part in command)
        self.assertIn("libx264", rendered)
        self.assertIn("yuv420p", rendered)
        self.assertIn("-an", command)
        self.assertIn("concat=n=", rendered)
        self.assertNotIn("http://", rendered)
        self.assertNotIn("https://", rendered)

    def test_scene_html_isolates_the_requested_evidence_section(self) -> None:
        html = (
            "<html><head></head><body><header>hero</header><main>"
            '<section aria-labelledby="story-title">story</section>'
            '<section aria-labelledby="criteria-title">criteria</section>'
            "</main><footer>footer</footer></body></html>"
        )
        rendered = render_scene_html(html, SCENES[2])
        self.assertIn('main>section[aria-labelledby="story-title"]', rendered)
        self.assertIn("header,footer,main>section{display:none!important}", rendered)
        self.assertIn(">story</section>", rendered)

    def test_srt_has_monotonic_scene_timing(self) -> None:
        text = render_srt(SCENES)
        self.assertIn("1\n00:00:00,000 -->", text)
        self.assertEqual(text.count("-->"), len(SCENES))
        self.assertIn("Local technical rehearsal", text)
        self.assertIn("not a live Twilio interaction", text)

    def test_manifest_hashes_only_materialized_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "demo.mp4").write_bytes(b"video")
            (root / "captions.srt").write_text("captions", encoding="utf-8")
            manifest_path = root / "manifest.json"
            manifest = write_manifest(
                root,
                manifest_path,
                "c" * 40,
                [root / "demo.mp4", root / "captions.srt"],
            )

            stored = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(stored, manifest)
            self.assertEqual(stored["source_sha"], "c" * 40)
            self.assertFalse(stored["boundaries"]["live_twilio_interaction"])
            self.assertEqual(set(stored["files"]), {"captions.srt", "demo.mp4"})


if __name__ == "__main__":
    unittest.main()
