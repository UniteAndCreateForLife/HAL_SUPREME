from __future__ import annotations

import unittest

from examples.agent_world_arena.service import ArenaService, decode_json_object


def scenario() -> dict:
    return {
        "schema": "hal.agent_world.scenario.v0",
        "scenario_id": "service-test",
        "description": "service contract test",
        "seed": 17,
        "width": 4,
        "height": 3,
        "max_ticks": 3,
        "mode": "hybrid",
        "slots": [
            {"slot_id": "s0", "start": [0, 1], "team": None, "role": None},
            {"slot_id": "s1", "start": [3, 1], "team": None, "role": None},
        ],
        "resources": [
            {"resource_id": "r0", "position": [1, 1], "value": 2},
        ],
    }


class ArenaServiceTests(unittest.TestCase):
    def test_create_observe_submit_advance_and_replay(self) -> None:
        service = ArenaService()
        created = service.create_episode(
            scenario(),
            ["provider-a", "provider-b"],
            episode_id="episode-fixed",
        )

        self.assertEqual(created["episode_id"], "episode-fixed")
        self.assertEqual(
            set(created["provider_assignment"].values()),
            {"provider-a", "provider-b"},
        )

        observation = service.observe("episode-fixed", "s0")
        self.assertEqual(observation["episode_id"], "episode-fixed")
        self.assertEqual(observation["tick"], 0)

        service.submit_action(
            "episode-fixed",
            "s0",
            {"kind": "move", "dx": 1, "dy": 0},
        )
        service.submit_action(
            "episode-fixed",
            "s1",
            {"kind": "move", "dx": -1, "dy": 0},
        )
        receipt = service.advance("episode-fixed")

        self.assertEqual(receipt["tick"], 1)
        self.assertEqual(service.status("episode-fixed")["replay_steps"], 1)
        replay = service.replay("episode-fixed")
        self.assertEqual(len(replay["steps"]), 1)
        self.assertEqual(replay["steps"][0]["state_sha256"], receipt["state_sha256"])

    def test_service_preserves_simultaneous_commit_boundary(self) -> None:
        service = ArenaService()
        service.create_episode(
            scenario(),
            ["provider-a", "provider-b"],
            episode_id="episode-wait",
        )
        status = service.submit_action(
            "episode-wait",
            "s0",
            {"kind": "idle"},
        )

        self.assertEqual(status["waiting_for"], ["s1"])
        with self.assertRaises(RuntimeError):
            service.advance("episode-wait")

    def test_deadline_can_idle_only_missing_provider(self) -> None:
        service = ArenaService()
        service.create_episode(
            scenario(),
            ["provider-a", "provider-b"],
            episode_id="episode-timeout",
        )
        service.submit_action(
            "episode-timeout",
            "s0",
            {"kind": "move", "dx": 1, "dy": 0},
        )

        receipt = service.advance_with_idle_for_missing(
            "episode-timeout",
            reason="network-timeout",
        )

        self.assertEqual(receipt["session_commit"]["idled_agents"], ["s1"])
        self.assertEqual(receipt["session_commit"]["reason"], "network-timeout")

    def test_decode_json_object_is_fail_closed(self) -> None:
        self.assertEqual(decode_json_object('{"kind":"idle"}', label="action"), {"kind": "idle"})
        with self.assertRaises(ValueError):
            decode_json_object("[]", label="action")
        with self.assertRaises(ValueError):
            decode_json_object("{not-json}", label="action")


if __name__ == "__main__":
    unittest.main()
