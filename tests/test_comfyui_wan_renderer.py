import tempfile
import unittest
from pathlib import Path

from renderers.base import RenderRequest
from renderers.comfyui_wan import ComfyUIWanRenderer


class FakeComfy(ComfyUIWanRenderer):
    def __init__(self):
        super().__init__(endpoint="http://invalid")
        self.queued = None

    def _json(self, path, payload=None):
        if path == "/prompt":
            self.queued = payload
            return {"prompt_id": "p1"}
        if path == "/history/p1":
            return {
                "p1": {
                    "outputs": {
                        "9": {"images": [{"filename": "still.png"}]},
                        "10": {"videos": [{"filename": "final.mp4", "type": "output"}]},
                    }
                }
            }
        raise AssertionError(path)

    def _download_candidate(self, item, request):
        target = request.output_dir / item["filename"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"video")
        return target


class ComfyRendererTests(unittest.TestCase):
    def test_binds_request_and_prefers_video(self):
        workflow = {
            "1": {"inputs": {"text": "old"}},
            "2": {"inputs": {"seed": 1}},
            "3": {"inputs": {"width": 1, "height": 1, "length": 1}},
        }
        bindings = {
            "prompt_node": "1",
            "seed_node": "2",
            "width_node": "3",
            "height_node": "3",
            "frames_node": "3",
        }
        with tempfile.TemporaryDirectory() as td:
            renderer = FakeComfy()
            request = RenderRequest(
                task_id="t",
                shot_id="s",
                prompt="new prompt",
                output_dir=Path(td),
                width=1280,
                height=720,
                frames=121,
                seed=42,
                metadata={"comfy_workflow": workflow, "comfy_bindings": bindings},
            )
            result = renderer.render(request)
            queued = renderer.queued["prompt"]
            self.assertEqual(queued["1"]["inputs"]["text"], "new prompt")
            self.assertEqual(queued["2"]["inputs"]["seed"], 42)
            self.assertEqual(queued["3"]["inputs"]["width"], 1280)
            self.assertEqual(queued["3"]["inputs"]["height"], 720)
            self.assertEqual(queued["3"]["inputs"]["length"], 121)
            self.assertEqual(result.artifact_path.name, "final.mp4")

    def test_output_node_is_enforced(self):
        record = {"outputs": {"1": {"videos": [{"filename": "a.mp4"}]}}}
        with self.assertRaises(RuntimeError):
            ComfyUIWanRenderer._candidates(record, "missing")


if __name__ == "__main__":
    unittest.main()
