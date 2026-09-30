import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.claude_session_mirror import (
    backfill,
    load_index,
    mirror_hook,
    redact_text,
)


class ClaudeSessionMirrorTests(unittest.TestCase):
    def test_redacts_common_secrets_and_home_paths(self):
        text = r"Bearer abcdefghijklmnop C:\Users\alice\work sk-abcdefghijklmnop"
        safe = redact_text(text)
        self.assertNotIn("abcdefghijklmnop", safe)
        self.assertNotIn(r"C:\Users\alice", safe)
        self.assertIn("[REDACTED]", safe)
        self.assertIn("[LOCAL_HOME]", safe)

    def test_hook_mirrors_transcript_and_latest_message(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source.jsonl"
            source.write_text('{"message":"hello","authorization":"Bearer abcdefghijklmnop"}\n', encoding="utf-8")
            payload = {
                "session_id": "session-1",
                "transcript_path": str(source),
                "cwd": str(root / "HAL_SUPREME"),
                "hook_event_name": "Stop",
                "last_assistant_message": "finished the task",
            }
            state = mirror_hook(payload, root / "mirror")
            target = root / "mirror" / state["mirror_relative_path"]
            body = target.read_text(encoding="utf-8")
            self.assertNotIn("abcdefghijklmnop", body)
            self.assertEqual(state["last_assistant_message"], "finished the task")
            index = load_index(root / "mirror")
            self.assertIn("session-1", index["sessions"])

    def test_backfill_uses_recent_transcripts(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            p1 = root / "one.jsonl"
            p2 = root / "two.jsonl"
            p1.write_text('{"x":1}\n', encoding="utf-8")
            p2.write_text('{"x":2}\n', encoding="utf-8")
            with patch(
                "scripts.claude_session_mirror.discover_recent_transcripts",
                return_value=[p2, p1],
            ):
                rows = backfill(root / "mirror", limit=2, project_substring="HAL")
            self.assertEqual(len(rows), 2)
            self.assertTrue((root / "mirror" / "latest_sessions.md").is_file())


if __name__ == "__main__":
    unittest.main()
