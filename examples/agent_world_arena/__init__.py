"""Provider-neutral multi-agent simulation contracts for HAL Agent World Arena."""

from .a2a_card import A2A_PROTOCOL_VERSION, build_agent_world_a2a_card
from .adapters import AgentAdapter, ScriptedAdapter
from .brain_bridge import BrainRequest, BrainResponse, BRIDGE_PROTOCOL_VERSION
from .conformance import ConformanceReceipt, run_adapter_conformance
from .http_action_adapter import OpenAICompatibleActionAdapter
from .meta_muse import MetaMuseAdapter
from .ollama_local import OllamaActionAdapter
from .participant import ParticipantManifest, negotiate_capabilities
from .protocol import Action, Observation, ProviderDescriptor, PROTOCOL_VERSION
from .runner import EpisodeRunner, assign_providers, build_arena
from .scenario import AgentSlot, ResourceSpec, ScenarioManifest
from .session import EpisodeSession, SessionStatus
from .sim import Arena, ArenaConfig

__all__ = [
    "Action",
    "A2A_PROTOCOL_VERSION",
    "build_agent_world_a2a_card",
    "Observation",
    "ProviderDescriptor",
    "ParticipantManifest",
    "negotiate_capabilities",
    "PROTOCOL_VERSION",
    "MetaMuseAdapter",
    "OpenAICompatibleActionAdapter",
    "OllamaActionAdapter",
    "AgentAdapter",
    "ScriptedAdapter",
    "BrainRequest",
    "BrainResponse",
    "BRIDGE_PROTOCOL_VERSION",
    "ConformanceReceipt",
    "run_adapter_conformance",
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
