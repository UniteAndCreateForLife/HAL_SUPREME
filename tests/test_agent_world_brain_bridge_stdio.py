from __future__ import annotations

import subprocess
import sys
import unittest

from examples.agent_world_arena.brain_bridge import (
    BrainRequest,
    decode_frame,
    encode_frame,
    response_from_dict,
)


class AgentWorldBrainBridgeStdioTests(unittest.TestCase):
    def test_reference_worker_runs_out_of_process_and_echoes_identity(self) -> None:
        request = BrainRequest(
            request_id="req-stdio-1",
            episode_id="episode-stdio",
            tick=3,
            slot_id="slot-external",
            deadline_ms=20,
            allowed_actions=("idle", "move"),
            observation={"position": [0, 0], "visible_objects": []},
        )

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "examples.agent_world_arena.brain_bridge_stdio",
                "--single",
            ],
            input=encode_frame(request.to_dict()),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=5,
        )

        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8"))
        response = response_from_dict(decode_frame(result.stdout))
        response.validate_against(request)
        self.assertEqual(response.action, {"kind": "idle"})
        self.assertEqual(response.diagnostics["worker"], "reference-idle-v0")
        self.assertIsInstance(response.diagnostics["elapsed_us"], int)

    def test_malformed_frame_fails_closed_without_echoing_input(self) -> None:
        marker = b"PRIVATE-MARKER-SHOULD-NOT-ECHO"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "examples.agent_world_arena.brain_bridge_stdio",
                "--single",
            ],
            input=b"{not-json:" + marker + b"}\n",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=5,
        )

        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b"")
        self.assertNotIn(marker, result.stderr)
        self.assertIn(b"brain-bridge-error:", result.stderr)


if __name__ == "__main__":
    unittest.main()
