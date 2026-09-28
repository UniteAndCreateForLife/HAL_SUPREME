"""Provider-neutral multi-agent simulation contracts for HAL Agent World Arena."""

from .adapters import AgentAdapter, ScriptedAdapter
from .protocol import Action, Observation, ProviderDescriptor, PROTOCOL_VERSION
from .runner import EpisodeRunner, assign_providers, build_arena
from .scenario import AgentSlot, ResourceSpec, ScenarioManifest
from .sim import Arena, ArenaConfig

__all__ = [
    "Action",
    "Observation",
    "ProviderDescriptor",
    "PROTOCOL_VERSION",
    "AgentAdapter",
    "ScriptedAdapter",
    "EpisodeRunner",
    "assign_providers",
    "build_arena",
    "AgentSlot",
    "ResourceSpec",
    "ScenarioManifest",
    "Arena",
    "ArenaConfig",
]
