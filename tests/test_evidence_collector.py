import json
import tempfile
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from evidence.runtime import EvidenceSession, verify_session
from services.evidence_collector import EvidenceHandler


class EvidenceCollectorTests(unittest.TestCase):
    def test_loopback_event_ingest(self):
        with tempfile.TemporaryDirectory() as td:
            session = EvidenceSession(Path(td), title="collector", source="test")
            server = ThreadingHTTPServer(("127.0.0.1", 0), EvidenceHandler)
            server.session = session
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                url = f"http://127.0.0.1:{server.server_address[1]}/v1/event"
                payload = json.dumps({
                    "kind": "agent.step",
                    "message": "planned",
                    "phase": "plan",
                    "source": "agent-zero",
                    "data": {"step": 1},
                }).encode("utf-8")
                req = urllib.request.Request(
                    url,
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=5) as response:
                    body = json.loads(response.read().decode("utf-8"))
                    self.assertEqual(response.status, 201)
                    self.assertEqual(body["session_id"], session.session_id)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)

            session.finalize(status="completed", exit_code=0)
            verification = verify_session(session.session_dir)
            self.assertTrue(verification["passed"])
            events = [
                json.loads(line)
                for line in session.events_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            ingested = next(event for event in events if event["kind"] == "agent.step")
            self.assertEqual(ingested["source"], "agent-zero")
            self.assertEqual(ingested["data"]["step"], 1)


if __name__ == "__main__":
    unittest.main()
