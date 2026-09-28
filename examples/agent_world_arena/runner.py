from __future__ import annotations

import random
from typing import Mapping, Sequence

from .adapters import AgentAdapter
from .protocol import Action
from .scenario import ScenarioManifest
from .sim import Arena


def assign_providers(
    provider_ids: Sequence[str],
    slot_ids: Sequence[str],
    *,
    seed: int,
) -> dict[str, str]:
    """Assign providers to slots reproducibly without trusting caller ordering."""

    providers = sorted(str(item) for item in provider_ids)
    slots = list(str(item) for item in slot_ids)

    if len(providers) != len(slots):
        raise ValueError("provider count must match slot count")
    if len(providers) != len(set(providers)):
        raise ValueError("provider ids must be unique")
    if len(slots) != len(set(slots)):
        raise ValueError("slot ids must be unique")

    random.Random(seed).shuffle(providers)
    return dict(zip(slots, providers, strict=True))


def build_arena(
    manifest: ScenarioManifest,
    provider_ids: Sequence[str],
) -> tuple[Arena, dict[str, str]]:
    manifest.validate()
    assignment = assign_providers(
        provider_ids,
        [slot.slot_id for slot in manifest.slots],
        seed=manifest.seed,
    )

    arena = Arena(manifest.arena_config(), episode_id=manifest.scenario_id)
    for slot in manifest.slots:
        arena.register_agent(
            slot.slot_id,
            assignment[slot.slot_id],
            position=slot.start,
        )
    for resource in manifest.resources:
        arena.add_resource(
            resource.resource_id,
            resource.position,
            value=resource.value,
        )
    return arena, assignment


class EpisodeRunner:
    """Runs adapters against one authoritative Arena.

    Provider exceptions are reduced to a bounded status code and an idle action.
    Raw provider error text is intentionally excluded from replay evidence.
    """

    def __init__(
        self,
        arena: Arena,
        adapters_by_provider: Mapping[str, AgentAdapter],
    ) -> None:
        self.arena = arena
        self.adapters_by_provider = dict(adapters_by_provider)

        missing = sorted(
            {
                agent.provider_id
                for agent in self.arena.agents.values()
                if agent.provider_id not in self.adapters_by_provider
            }
        )
        if missing:
            raise ValueError(f"missing adapters for providers: {missing}")

    def step(self) -> dict:
        actions: dict[str, Action] = {}
        adapter_status: list[dict[str, str]] = []

        for agent_id in sorted(self.arena.agents):
            agent = self.arena.agents[agent_id]
            observation = self.arena.observe(agent_id)
            adapter = self.adapters_by_provider[agent.provider_id]

            try:
                action = adapter.decide(observation)
                if not isinstance(action, Action):
                    raise TypeError("adapter returned non-Action")
                action.validate(max_message_chars=self.arena.config.max_message_chars)
                status = "ok"
            except Exception as exc:  # boundary intentionally catches provider failures
                action = Action("idle")
                status = f"fallback:{type(exc).__name__}"

            actions[agent_id] = action
            adapter_status.append(
                {
                    "agent_id": agent_id,
                    "provider_id": agent.provider_id,
                    "status": status,
                }
            )

        receipt = self.arena.step(actions)
        receipt["adapter_status"] = adapter_status
        return receipt

    def run(self, *, max_steps: int | None = None) -> list[dict]:
        receipts: list[dict] = []
        while not self.arena.done:
            if max_steps is not None and len(receipts) >= max_steps:
                break
            receipts.append(self.step())
        return receipts
