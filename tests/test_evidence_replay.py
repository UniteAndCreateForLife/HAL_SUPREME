import unittest

from scripts.build_evidence_replay import _sanitize_replay


class EvidenceReplayTests(unittest.TestCase):
    def test_masks_local_paths(self):
        data = {
            "source_path": r"C:\Users\alice\HAL_SUPREME\output.mp4",
            "cwd": "/home/alice/HAL_SUPREME",
            "message": r"loaded C:\Users\alice\HAL_SUPREME\config.json",
            "stored_path": "artifacts/output.mp4",
        }
        safe = _sanitize_replay(data)
        self.assertEqual(safe["source_path"], "[LOCAL_PATH]/output.mp4")
        self.assertEqual(safe["cwd"], "[LOCAL_PATH]/HAL_SUPREME")
        self.assertNotIn("alice", safe["message"])
        self.assertEqual(safe["stored_path"], "artifacts/output.mp4")


if __name__ == "__main__":
    unittest.main()
