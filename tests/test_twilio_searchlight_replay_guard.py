from __future__ import annotations

import threading
import unittest

from services.twilio_searchlight_demo.replay_guard import (
    ReplayConflict,
    ReplayGuard,
)


class ReplayGuardTests(unittest.TestCase):
    def test_identical_retry_reuses_successful_result(self) -> None:
        guard = ReplayGuard()
        calls = 0

        def action() -> tuple[str, dict[str, str]]:
            nonlocal calls
            calls += 1
            return "<Response />", {"status": "ok"}

        first, first_replayed = guard.run_once("SM1", "hello", action)
        second, second_replayed = guard.run_once("SM1", "hello", action)

        self.assertEqual(first, second)
        self.assertFalse(first_replayed)
        self.assertTrue(second_replayed)
        self.assertEqual(calls, 1)

    def test_same_sid_with_different_body_fails_closed(self) -> None:
        guard = ReplayGuard()
        guard.run_once("SM1", "hello", lambda: ("ok", {"status": "ok"}))

        with self.assertRaises(ReplayConflict):
            guard.run_once("SM1", "changed", lambda: ("bad", {}))

    def test_failed_action_is_not_cached(self) -> None:
        guard = ReplayGuard()

        with self.assertRaises(RuntimeError):
            guard.run_once(
                "SM1",
                "hello",
                lambda: (_ for _ in ()).throw(RuntimeError("unavailable")),
            )

        result, replayed = guard.run_once(
            "SM1", "hello", lambda: ("retry", {"status": "ok"})
        )
        self.assertEqual(result[0], "retry")
        self.assertFalse(replayed)

    def test_concurrent_retry_waits_for_owner(self) -> None:
        guard = ReplayGuard()
        entered = threading.Event()
        release = threading.Event()
        results: list[tuple[tuple[str, dict[str, str]], bool]] = []
        errors: list[BaseException] = []
        calls = 0

        def action() -> tuple[str, dict[str, str]]:
            nonlocal calls
            calls += 1
            entered.set()
            release.wait(timeout=2)
            return "done", {"status": "ok"}

        def worker() -> None:
            try:
                results.append(guard.run_once("SM1", "hello", action))
            except BaseException as exc:
                errors.append(exc)

        first = threading.Thread(target=worker)
        second = threading.Thread(target=worker)
        first.start()
        self.assertTrue(entered.wait(timeout=1))
        second.start()
        release.set()
        first.join(timeout=2)
        second.join(timeout=2)

        self.assertEqual(errors, [])
        self.assertEqual(calls, 1)
        self.assertEqual(sorted(replayed for _, replayed in results), [False, True])

    def test_completed_entry_expires(self) -> None:
        now = [100.0]
        guard = ReplayGuard(ttl_seconds=10, clock=lambda: now[0])
        calls = 0

        def action() -> tuple[str, dict[str, str]]:
            nonlocal calls
            calls += 1
            return str(calls), {"status": "ok"}

        guard.run_once("SM1", "hello", action)
        now[0] = 111.0
        result, replayed = guard.run_once("SM1", "hello", action)

        self.assertEqual(result[0], "2")
        self.assertFalse(replayed)
        self.assertEqual(calls, 2)


if __name__ == "__main__":
    unittest.main()
