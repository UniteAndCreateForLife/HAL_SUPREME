import unittest

from qc.video import _extract_durations, _fraction, evaluate_video_evidence


class VideoQualityTests(unittest.TestCase):
    def test_fraction(self):
        self.assertAlmostEqual(_fraction("24000/1001"), 23.976023976, places=6)
        self.assertEqual(_fraction("0/0"), 0.0)

    def test_extract_lavfi_durations(self):
        text = "black_duration:0.75\nfreeze_duration:2.25\nfreeze_duration=1.5"
        self.assertEqual(_extract_durations(text, "freeze_duration"), [2.25, 1.5])

    def test_evaluate_passes_nominal_video(self):
        result = evaluate_video_evidence(
            {"duration_s": 5.02, "width": 1280, "height": 720, "fps": 24.0, "audio_streams": 0},
            expected_duration_s=5.0,
            minimum_width=1280,
            minimum_height=720,
            minimum_fps=23.0,
        )
        self.assertTrue(result["passed"])
        self.assertEqual(result["failures"], [])

    def test_evaluate_rejects_freeze_and_missing_audio(self):
        result = evaluate_video_evidence(
            {"duration_s": 5.0, "width": 1920, "height": 1080, "fps": 24.0, "audio_streams": 0},
            require_audio=True,
            freeze={"max_duration_s": 2.2},
            max_freeze_s=1.5,
        )
        self.assertFalse(result["passed"])
        self.assertIn("audio_stream_required", result["failures"])
        self.assertTrue(any(x.startswith("freeze_too_long") for x in result["failures"]))


if __name__ == "__main__":
    unittest.main()
