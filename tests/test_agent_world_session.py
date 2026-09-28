from __future__ import annotations

import unittest

from examples.agent_world_arena import Action, Arena, ArenaConfig
from examples.agent_world_arena.session import EpisodeSession


class AgentWorldSessionTests(unittest.TestCase):
    def make_session(self) -> EpisodeSession:
        arena = Arena(ArenaConfig(max_ticks=3), episode_id="session")
        arena.register_agent("a", "provider-a", position=(0, 0))
        arena.register_agent("b", "provider-b", position=(2, 0))
        return EpisodeSession(arena)

    def test_world_waits_for_every_agent_before_commit(self) -> None:
        session = self.make_session()

        status = session.submit_action("b", Action("move", dx=-1))

        self.assertEqual(status.waiting_for, ("a",))
        self.assertFalse(session.can_advance())
        with self.assertRaises(RuntimeError):
            session.advance()

        session.submit_action("a", Action("move", dx=1))
        self.assertTrue(session.can_advance())
        receipt = session.advance()

        self.assertEqual(receipt["session_commit"]["policy"], "all-agents-submitted")
        self.assertEqual(session.arena.tick, 1)
        self.assertEqual(session.arena.agents["a"].position, (1, 0))
        self.assertEqual(session.arena.agents["b"].position, (1, 0))

    def test_provider_request_order_does_not_change_state_hash(self) -> None:
        def run(order):
            session = self.make_session()
            actions = {
                "a": Action("move", dx=1),
                "b": Action("move", dx=-1),
            }
            for agent_id in order:
                session.submit_action(agent_id, actions[agent_id])
            return session.advance()["state_sha256"]

        self.assertEqual(run(("a", "b")), run(("b", "a")))

    def test_duplicate_action_for_same_tick_is_rejected(self) -> None:
        session = self.make_session()
        session.submit_action("a", Action("idle"))
        with self.assertRaises(RuntimeError):
            session.submit_action("a", Action("idle"))

    def test_deadline_path_idles_only_missing_agents(self) -> None:
        session = self.make_session()
        session.submit_action("a", Action("move", dx=1))

        receipt = session.advance_with_idle_for_missing(reason="adapter-timeout")

        commit = receipt["session_commit"]
        self.assertEqual(commit["policy"], "idle-for-missing")
        self.assertEqual(commit["submitted_agents"], ["a"])
        self.assertEqual(commit["idled_agents"], ["b"])
        self.assertEqual(commit["reason"], "adapter-timeout")


if __name__ == "__main__":
    unittest.main()
