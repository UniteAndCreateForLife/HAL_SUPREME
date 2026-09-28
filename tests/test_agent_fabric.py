from __future__ import annotations

import unittest

from services.agent_fabric.contract import validate_task_packet


REVISION = "abc123"
DIGEST = "a" * 64


def base_packet(status: str = "planned") -> dict:
    return {
        "schema": "hal.agent_task.v1",
        "task_id": "agent-fabric-test",
        "objective": "Prove the promotion contract.",
        "scope": ["services/agent_fabric"],
        "constraints": ["offline"],
        "protected_actions": ["merge"],
        "acceptance": ["All contract tests pass."],
        "status": status,
        "revision": None,
        "implementer": None,
        "verification": [],
        "review": None,
        "receipt_sha256": None,
        "promotion": None,
    }


def verified_packet(status: str) -> dict:
    packet = base_packet(status)
    packet["revision"] = REVISION
    packet["implementer"] = "worker-a"
    packet["verification"] = [
        {
            "kind": "focused",
            "command": "python -m unittest -v tests.test_agent_fabric",
            "outcome": "passed",
            "revision": REVISION,
            "worker": "ci-focused",
            "evidence_sha256": DIGEST,
        },
        {
            "kind": "regression",
            "command": "python -m unittest discover -v",
            "outcome": "passed",
            "revision": REVISION,
            "worker": "ci-regression",
            "evidence_sha256": DIGEST,
        },
    ]
    packet["review"] = {
        "reviewer": "worker-b",
        "outcome": "passed",
        "revision": REVISION,
    }
    packet["receipt_sha256"] = DIGEST
    return packet


class AgentFabricContractTests(unittest.TestCase):
    def test_planned_packet_is_valid_without_execution_claims(self) -> None:
        self.assertEqual(validate_task_packet(base_packet()), [])

    def test_focused_verification_is_required_before_claiming_it(self) -> None:
        packet = base_packet("focused_verified")
        packet["revision"] = REVISION
        packet["implementer"] = "worker-a"
        errors = validate_task_packet(packet)
        self.assertTrue(any("passing focused verification" in error for error in errors))

    def test_verification_must_match_revision(self) -> None:
        packet = verified_packet("focused_verified")
        packet["verification"][0]["revision"] = "wrong"
        errors = validate_task_packet(packet)
        self.assertTrue(any("passing focused verification" in error for error in errors))

    def test_review_must_be_independent(self) -> None:
        packet = verified_packet("reviewed")
        packet["review"]["reviewer"] = packet["implementer"]
        errors = validate_task_packet(packet)
        self.assertIn("independent review requires reviewer != implementer", errors)

    def test_promotion_ready_requires_receipt_digest(self) -> None:
        packet = verified_packet("promotion_ready")
        packet["receipt_sha256"] = None
        errors = validate_task_packet(packet)
        self.assertIn("promotion_ready or later requires receipt_sha256", errors)

    def test_promoted_packet_requires_explicit_authorized_event(self) -> None:
        packet = verified_packet("promoted")
        packet["promotion"] = {
            "action": "merge",
            "authorized": False,
            "revision": REVISION,
            "event_id": "merge-123",
        }
        errors = validate_task_packet(packet)
        self.assertIn("promoted requires promotion.authorized=true", errors)

    def test_fully_evidenced_promoted_packet_is_valid(self) -> None:
        packet = verified_packet("promoted")
        packet["promotion"] = {
            "action": "merge",
            "authorized": True,
            "revision": REVISION,
            "event_id": "merge-123",
        }
        self.assertEqual(validate_task_packet(packet), [])

    def test_unknown_protected_action_is_rejected(self) -> None:
        packet = base_packet()
        packet["protected_actions"] = ["teleport"]
        errors = validate_task_packet(packet)
        self.assertIn("unknown protected_actions: teleport", errors)


if __name__ == "__main__":
    unittest.main()
