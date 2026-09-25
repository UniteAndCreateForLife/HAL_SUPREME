import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from renderers.base import RenderRequest
from renderers.lightx2v_wan import LightX2VSettings, LightX2VWanRenderer


class LightX2VWanTests(unittest.TestCase):
    def test_command_uses_official_lightx2v_wan22_entrypoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model = root / "model"
            model.mkdir()
            cfg = root / "config.json"
            cfg.write_text("{}", encoding="utf-8")
            renderer = LightX2VWanRenderer(LightX2VSettings(sys.executable, model, cfg))
            request = RenderRequest(
                task_id="t", shot_id="s", prompt="cinematic corridor",
                output_dir=root, width=832, height=480, fps=24, frames=81, seed=731,
            )
            command = renderer.build_command(request)
            self.assertEqual(command[1:3], ["-m", "lightx2v.infer"])
            self.assertIn("wan2.2", command)
            self.assertIn("t2v", command)
            self.assertIn("832", command)
            self.assertIn("480", command)
            self.assertIn("81", command)
            self.assertIn("731", command)

    def test_health_degrades_when_assets_missing_but_runtime_imports(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            renderer = LightX2VWanRenderer(
                LightX2VSettings(sys.executable, root / "missing-model", root / "missing-config.json")
            )
            fake = mock.Mock(returncode=0, stdout="1.2.3\n", stderr="")
            with mock.patch("renderers.lightx2v_wan.subprocess.run", return_value=fake):
                health = renderer.health()
            self.assertEqual(health["health"], "degraded")
            self.assertIn("model_path", health["missing"])
            self.assertIn("config_json", health["missing"])

    def test_render_refuses_unhealthy_runtime_before_submitting_work(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            renderer = LightX2VWanRenderer(
                LightX2VSettings(sys.executable, root / "missing-model", root / "missing-config.json")
            )
            with mock.patch.object(renderer, "health", return_value={"health": "offline"}):
                with self.assertRaises(RuntimeError):
                    renderer.render(RenderRequest(task_id="t", shot_id="s", prompt="x", output_dir=root))


if __name__ == "__main__":
    unittest.main()
