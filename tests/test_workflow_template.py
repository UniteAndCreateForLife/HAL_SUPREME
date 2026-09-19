import unittest

from pathlib import Path

from renderers.base import RenderRequest
from renderers.workflow_template import WorkflowBindings, WorkflowTemplate


class WorkflowTemplateTests(unittest.TestCase):
    def test_injects_shot_parameters_without_mutating_template(self):
        raw = {
            "1": {"inputs": {"text": "old"}},
            "2": {"inputs": {"seed": 1}},
            "3": {"inputs": {"width": 512, "height": 512, "length": 17}},
        }
        template = WorkflowTemplate(raw, WorkflowBindings(
            prompt_node="1", seed_node="2",
            width_node="3", height_node="3", frames_node="3",
        ))
        request = RenderRequest(
            task_id="t", shot_id="s", prompt="new prompt", output_dir=Path("."),
            width=1280, height=720, frames=121, seed=99,
        )
        built = template.build(request)
        self.assertEqual(built["1"]["inputs"]["text"], "new prompt")
        self.assertEqual(built["2"]["inputs"]["seed"], 99)
        self.assertEqual(built["3"]["inputs"]["width"], 1280)
        self.assertEqual(built["3"]["inputs"]["height"], 720)
        self.assertEqual(built["3"]["inputs"]["length"], 121)
        self.assertEqual(raw["1"]["inputs"]["text"], "old")

    def test_missing_bound_node_fails_closed(self):
        template = WorkflowTemplate({"1": {"inputs": {"text": "x"}}}, WorkflowBindings(prompt_node="missing"))
        request = RenderRequest("t", "s", "p", Path("."))
        with self.assertRaises(KeyError):
            template.build(request)


if __name__ == "__main__":
    unittest.main()
