from __future__ import annotations

import unittest

from examples.agent_world_arena.bridge_lifecycle import (
    ConnectionState,
    FaultLedger,
    RequestOutcome,
    SlotConnection,
)


class FaultLedgerTests(unittest.TestCase):
    def test_transport_retries_do_not_inflate_fault_count(self) -> None:
        ledger = FaultLedger()
        for index in range(700):
            ledger.record_transport_event(
                event="poll-no-data",
                detail=str(index),
            )

        ledger.record_outcome(
            RequestOutcome(
                request_id="req-1",
                outcome="timeout",
                fault_class="deadline",
                fallback="idle",
            )
        )

        self.assertEqual(len(ledger.transport_events), 700)
        self.assertEqual(ledger.fault_count, 1)

    def test_same_terminal_outcome_is_idempotent(self) -> None:
        ledger = FaultLedger()
        outcome = RequestOutcome(
            request_id="req-1",
            outcome="malformed",
            fault_class="invalid-json",
            fallback="idle",
        )
        ledger.record_outcome(outcome)
        ledger.record_outcome(outcome)
        self.assertEqual(len(ledger.outcomes), 1)
        self.assertEqual(ledger.fault_count, 1)

    def test_conflicting_second_terminal_outcome_is_rejected(self) -> None:
        ledger = FaultLedger()
        ledger.record_outcome(
            RequestOutcome(
                request_id="req-1",
                outcome="timeout",
                fault_class="deadline",
            )
        )
        with self.assertRaises(RuntimeError):
            ledger.record_outcome(
                RequestOutcome(
                    request_id="req-1",
                    outcome="accepted",
                )
            )


class SlotConnectionTests(unittest.TestCase):
    def test_timeout_quarantines_and_requires_close_before_rebind(self) -> None:
        slot = SlotConnection("slot-a")
        generation_1 = slot.bind(peer_id="worker-a")
        slot.begin_request("req-1")
        slot.timeout("req-1")

        self.assertEqual(slot.state, ConnectionState.QUARANTINED)
        with self.assertRaises(RuntimeError):
            slot.bind(peer_id="worker-b")

        slot.close_quarantined()
        generation_2 = slot.bind(peer_id="worker-b")

        self.assertEqual(slot.state, ConnectionState.ACTIVE)
        self.assertGreater(generation_2, generation_1)
        self.assertEqual(slot.active_peer_id, "worker-b")

    def test_old_generation_cannot_submit_after_reconnect(self) -> None:
        slot = SlotConnection("slot-a")
        old_generation = slot.bind(peer_id="worker-a")
        slot.begin_request("req-1")
        slot.timeout("req-1")
        slot.close_quarantined()

        new_generation = slot.bind(peer_id="worker-a")
        slot.begin_request("req-2")

        with self.assertRaises(RuntimeError):
            slot.accept_response(
                peer_id="worker-a",
                generation=old_generation,
                request_id="req-2",
            )

        slot.accept_response(
            peer_id="worker-a",
            generation=new_generation,
            request_id="req-2",
        )
        self.assertIsNone(slot.outstanding_request_id)

    def test_worker_swap_is_explicit_close_then_bind(self) -> None:
        slot = SlotConnection("slot-a")
        first_generation = slot.bind(peer_id="worker-a")
        slot.close()
        second_generation = slot.bind(peer_id="worker-b")

        self.assertEqual(slot.active_peer_id, "worker-b")
        self.assertGreater(second_generation, first_generation)


if __name__ == "__main__":
    unittest.main()
