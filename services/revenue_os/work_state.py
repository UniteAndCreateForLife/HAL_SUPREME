from __future__ import annotations
from dataclasses import dataclass, field
from .models import WorkState

# Revenue OS is a projection, not a second HAL WorkGraph authority.
GATES = {
    WorkState.VERIFIED: {"reward_verified", "eligibility_verified", "submission_route_verified"},
    WorkState.READY: {"scope_understood", "contention_checked", "repo_rules_checked"},
    WorkState.IMPLEMENTING: {"reproduction_receipt"},
    WorkState.TESTING: {"implementation_complete", "targeted_tests_added"},
    WorkState.REVIEWING: {"targeted_tests_pass", "full_tests_pass", "lint_or_static_pass"},
    WorkState.SUBMISSION_READY: {"independent_review_pass", "security_review_pass", "tested_sha_verified", "evidence_receipt"},
    WorkState.SUBMITTED: {"human_submission_receipt"},
    WorkState.WON: {"sponsor_acceptance_receipt"},
    WorkState.PAID: {"payment_receipt"},
}


@dataclass
class EvidenceGateProjection:
    state: WorkState = WorkState.DISCOVERED
    gates: set[str] = field(default_factory=set)

    def mark(self, gate: str) -> None:
        self.gates.add(gate)

    def can_transition(self, target: WorkState) -> tuple[bool, list[str]]:
        missing = sorted(GATES.get(target, set()) - self.gates)
        return not missing, missing
