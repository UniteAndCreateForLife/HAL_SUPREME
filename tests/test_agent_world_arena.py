from __future__ import annotations

import unittest

from examples.agent_world_arena import Action, Arena, ArenaConfig


class AgentWorldArenaTests(unittest.TestCase):
    def test_action_contract_rejects_unbounded_motion(self) -> None:
        with self.assertRaises(ValueError):
            Action("move", dx=4, dy=0).validate()

    def test_same_episode_replays_to_same_state_hash(self) -> None:
        def run_once() -> str:
            arena = Arena(ArenaConfig(max_ticks=4), episode_id="replay")
            arena.register_agent("alpha", "meta-muse", position=(0, 0))
            arena.register_agent("beta", "hal-local", position=(2, 0))
            arena.add_resource("r1", (1, 0), value=3)
            arena.step({"alpha": Action("move", dx=1), "beta": Action("idle")})
            receipt = arena.step({"alpha": Action("gather"), "beta": Action("move", dx=-1)})
            return receipt["state_sha256"]

        self.assertEqual(run_once(), run_once())

    def test_agents_can_communicate_without_direct_provider_connections(self) -> None:
        arena = Arena(ArenaConfig(max_ticks=3), episode_id="comms")
        arena.register_agent("muse", "meta-muse", position=(0, 0))
        arena.register_agent("hal", "hal", position=(1, 0))

        arena.step({"muse": Action("say", target="hal", message="meet at resource")})
        observation = arena.observe("hal")

        self.assertEqual(len(observation.inbox), 1)
        self.assertEqual(observation.inbox[0]["from"], "muse")
        self.assertEqual(observation.inbox[0]["message"], "meet at resource")

    def test_contention_is_deterministic_and_receipted(self) -> None:
        arena = Arena(ArenaConfig(max_ticks=2), episode_id="contest")
        arena.register_agent("a", "provider-a", position=(1, 1))
        arena.register_agent("b", "provider-b", position=(1, 1))
        arena.add_resource("token", (1, 1), value=5)

        receipt = arena.step({"a": Action("gather"), "b": Action("gather")})

        self.assertEqual(arena.agents["a"].score, 5)
        self.assertEqual(arena.agents["b"].score, 0)
        self.assertEqual(len(receipt["state_sha256"]), 64)
        self.assertNotIn("token", arena.resources)

    def test_broadcast_is_delivered_to_every_other_agent(self) -> None:
        arena = Arena(ArenaConfig(max_ticks=2), episode_id="broadcast")
        for agent_id in ("a", "b", "c"):
            arena.register_agent(agent_id, f"provider-{agent_id}")

        arena.step({"a": Action("say", target="*", message="team up")})

        self.assertEqual(arena.observe("a").inbox, ())
        self.assertEqual(arena.observe("b").inbox[0]["message"], "team up")
        self.assertEqual(arena.observe("c").inbox[0]["message"], "team up")


if __name__ == "__main__":
    unittest.main()
