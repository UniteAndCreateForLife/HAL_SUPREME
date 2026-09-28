"""Provider-neutral multi-agent simulation contracts for HAL Agent World Arena."""

from .adapters import AgentAdapter, ScriptedAdapter
from .meta_muse import MetaMuseAdapter
from .protocol import Action, Observation, ProviderDescriptor, PROTOCOL_VERSION
from .runner import EpisodeRunner, assign_providers, build_arena
from .scenario import AgentSlot, ResourceSpec, ScenarioManifest
from .session import EpisodeSession, SessionStatus
from .sim import Arena, ArenaConfig

__all__ = [
    "Action",
    "Observation",
    "ProviderDescriptor",
    "PROTOCOL_VERSION",
    "MetaMuseAdapter",
    "AgentAdapter",
    "ScriptedAdapter",
    "EpisodeRunner",
    "assign_providers",
    "build_arena",
    "AgentSlot",
    "ResourceSpec",
    "ScenarioManifest",
    "EpisodeSession",
    "SessionStatus",
    "Arena",
    "ArenaConfig",
]
