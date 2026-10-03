import json
import tempfile
import unittest
from pathlib import Path

from evidence.runtime import EvidenceSession, redact, verify_session


class EvidenceRuntimeTests(unittest.TestCase):
    def test_hash_chain_artifact_and_finalize(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            session = EvidenceSession(root, title="test", source="unit")
            session.emit(
                "process.stdout",
                message="hello",
                data={"authorization": "Bearer secret-value", "url": "https://x.test/?token=abc123"},
            )
            artifact = root / "result.txt"
            artifact.write_text("proof", encoding="utf-8")
            record = session.register_artifact(artifact, role="proof")
            self.assertTrue((session.session_dir / record["stored_path"]).is_file())
            session.finalize(status="completed", exit_code=0)

            verification = verify_session(session.session_dir)
            self.assertTrue(verification["passed"])
            self.assertGreaterEqual(verification["event_count"], 4)

            events = [
                json.loads(line)
                for line in session.events_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            output = next(event for event in events if event["kind"] == "process.stdout")
            self.assertEqual(output["data"]["authorization"], "[REDACTED]")
            self.assertIn("[REDACTED]", output["data"]["url"])

    def test_tampering_breaks_chain(self):
        with tempfile.TemporaryDirectory() as td:
            session = EvidenceSession(Path(td), title="test", source="unit")
            session.emit("step", message="original")
            session.finalize(status="completed", exit_code=0)
            lines = session.events_path.read_text(encoding="utf-8").splitlines()
            event = json.loads(lines[1])
            event["message"] = "tampered"
            lines[1] = json.dumps(event, sort_keys=True, separators=(",", ":"))
            session.events_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            verification = verify_session(session.session_dir)
            self.assertFalse(verification["passed"])
            self.assertTrue(any("hash_mismatch" in item for item in verification["failures"]))

    def test_redaction_preserves_normal_values(self):
        value = redact({
            "model": "wan",
            "password": "secret",
            "text": "Authorization: Bearer abcdefghijklmnop",
        })
        self.assertEqual(value["model"], "wan")
        self.assertEqual(value["password"], "[REDACTED]")
        self.assertNotIn("abcdefghijklmnop", value["text"])


if __name__ == "__main__":
    unittest.main()
