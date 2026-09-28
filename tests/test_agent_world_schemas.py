from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = {
    "action": REPO_ROOT / "schemas" / "agent_world_action_v0.schema.json",
    "observation": REPO_ROOT / "schemas" / "agent_world_observation_v0.schema.json",
    "scenario": REPO_ROOT / "schemas" / "agent_world_scenario_v0.schema.json",
}


class AgentWorldSchemaTests(unittest.TestCase):
    def test_schemas_are_valid_json_objects_with_unique_ids(self) -> None:
        ids = []
        for path in SCHEMAS.values():
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["$schema"], "https://json-schema.org/draft/2020-12/schema")
            self.assertEqual(payload["type"], "object")
            self.assertTrue(payload["required"])
            ids.append(payload["$id"])
        self.assertEqual(len(ids), len(set(ids)))

    def test_action_schema_is_fail_closed(self) -> None:
        payload = json.loads(SCHEMAS["action"].read_text(encoding="utf-8"))
        self.assertFalse(payload["additionalProperties"])
        self.assertEqual(
            set(payload["properties"]["kind"]["enum"]),
            {"idle", "move", "gather", "say"},
        )
        self.assertIn("target", payload["required"])
        self.assertIn("message", payload["required"])

    def test_observation_schema_marks_protocol_version(self) -> None:
        payload = json.loads(SCHEMAS["observation"].read_text(encoding="utf-8"))
        self.assertEqual(
            payload["properties"]["protocol_version"]["const"],
            "hal.agent_world.v0",
        )

    def test_scenario_schema_has_reproducibility_fields(self) -> None:
        payload = json.loads(SCHEMAS["scenario"].read_text(encoding="utf-8"))
        required = set(payload["required"])
        for field in ("seed", "max_ticks", "mode", "slots"):
            self.assertIn(field, required)


if __name__ == "__main__":
    unittest.main()
