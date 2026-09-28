from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .adapters import AgentAdapter
from .baselines import greedy_resource_policy
from .participant import ParticipantManifest, negotiate_capabilities
from .protocol import ProviderDescriptor
from .runner import EpisodeRunner, build_arena
from .scenario import AgentSlot, ResourceSpec, ScenarioManifest
from .adapters import ScriptedAdapter


CONFORMANCE_VERSION = "hal.agent_world.conformance.v0"


@dataclass(frozen=True)
class ConformanceReceipt:
    participant_id: str
    framework: str
    transport: str
    scenario_id: str
    steps: int
    final_state_sha256: str
    adapter_failures: int
    schema: str = CONFORMANCE_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "participant_id": self.participant_id,
            "framework": self.framework,
            "transport": self.transport,
            "scenario_id": self.scenario_id,
            "steps": self.steps,
            "final_state_sha256": self.final_state_sha256,
            "adapter_failures": self.adapter_failures,
        }


def conformance_scenario(*, seed: int = 20260928) -> ScenarioManifest:
    """Small public scenario for adapter conformance, not model ranking."""

    return ScenarioManifest(
        scenario_id=f"interop-conformance-{seed}",
        seed=seed,
        width=5,
        height=3,
        max_ticks=4,
        mode="hybrid",
        slots=(
            AgentSlot("entrant", (0, 1), role="entrant"),
            AgentSlot("baseline", (4, 1), role="baseline"),
        ),
        resources=(
            ResourceSpec("center", (2, 1), value=3),
        ),
        description=(
            "Adapter conformance scenario. It checks bounded actions, isolation, "
            "deterministic replay, and shared contract compatibility; it is not a "
            "quality benchmark."
        ),
    )


def run_adapter_conformance(
    participant: ParticipantManifest,
    adapter: AgentAdapter,
    *,
    seed: int = 20260928,
) -> ConformanceReceipt:
    """Run one external adapter against the deterministic scripted baseline."""

    participant.validate()
    negotiate_capabilities(participant, ("observe", "act"))

    if adapter.provider.provider_id != participant.participant_id:
        raise ValueError(
            "adapter provider_id must match participant participant_id"
        )

    manifest = conformance_scenario(seed=seed)
    baseline_id = "hal-scripted-baseline"
    arena, assignment = build_arena(
        manifest,
        [participant.participant_id, baseline_id],
    )

    baseline = ScriptedAdapter(
        provider=ProviderDescriptor(
            provider_id=baseline_id,
            model="greedy-resource-v0",
            transport="local-python",
            capabilities=("agent-world-action",),
        ),
        policy=greedy_resource_policy,
    )

    runner = EpisodeRunner(
        arena,
        {
            participant.participant_id: adapter,
            baseline_id: baseline,
        },
    )
    receipts = runner.run()

    adapter_failures = sum(
        1
        for receipt in receipts
        for status in receipt.get("adapter_status", [])
        if status["provider_id"] == participant.participant_id
        and status["status"] != "ok"
    )

    if not receipts:
        raise RuntimeError("conformance run produced no receipts")

    return ConformanceReceipt(
        participant_id=participant.participant_id,
        framework=participant.framework,
        transport=participant.transport,
        scenario_id=manifest.scenario_id,
        steps=len(receipts),
        final_state_sha256=receipts[-1]["state_sha256"],
        adapter_failures=adapter_failures,
    )
