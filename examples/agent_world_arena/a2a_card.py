from __future__ import annotations

from typing import Any


A2A_PROTOCOL_VERSION = "1.0"


def build_agent_world_a2a_card(
    *,
    public_base_url: str,
    documentation_url: str | None = None,
    version: str = "0.1.0",
) -> dict[str, Any]:
    """Build a minimal Agent2Agent v1.0 discovery card for HAL Agent World.

    A2A is used for discovery, delegation, and coarse-grained collaboration.
    High-frequency simulation ticks remain on the bounded Agent World action
    protocol / MCP surface so game physics are not coupled to one agent runtime.
    """

    base = public_base_url.rstrip("/")
    if not base.startswith("https://"):
        raise ValueError("A2A production discovery URL must use https")

    card: dict[str, Any] = {
        "name": "HAL Agent World",
        "description": (
            "Provider-neutral multi-agent simulation and interoperability service. "
            "Remote agents can discover scenarios, request reviewed trials, and "
            "participate through bounded Agent World contracts."
        ),
        "supportedInterfaces": [
            {
                "url": f"{base}/a2a/v1",
                "protocolBinding": "JSONRPC",
                "protocolVersion": A2A_PROTOCOL_VERSION,
            }
        ],
        "provider": {
            "organization": "UniteAndCreateForLife",
            "url": "https://halsupreme.com",
        },
        "version": version,
        "capabilities": {
            "streaming": True,
        },
        "defaultInputModes": [
            "text/plain",
            "application/json",
        ],
        "defaultOutputModes": [
            "text/plain",
            "application/json",
        ],
        "skills": [
            {
                "id": "agent-world-interoperability-trial",
                "name": "Agent World interoperability trial",
                "description": (
                    "Request or coordinate a bounded cross-provider simulation trial "
                    "with scenario, participant, budget, and evidence requirements."
                ),
                "tags": [
                    "a2a",
                    "multi-agent",
                    "simulation",
                    "interop",
                    "benchmark",
                    "mcp",
                ],
                "examples": [
                    "Run a two-agent resource-rush trial with randomized slots.",
                    "Prepare a reviewed Muse vs local-agent interoperability episode.",
                ],
                "inputModes": [
                    "text/plain",
                    "application/json",
                ],
                "outputModes": [
                    "text/plain",
                    "application/json",
                ],
            },
            {
                "id": "agent-world-capability-discovery",
                "name": "Agent World capability discovery",
                "description": (
                    "Describe supported Agent World scenario classes, transports, "
                    "action contracts, evidence surfaces, and safety boundaries."
                ),
                "tags": [
                    "discovery",
                    "capabilities",
                    "agent-world",
                ],
                "examples": [
                    "What Agent World capabilities can my remote agent use?",
                ],
                "inputModes": [
                    "text/plain",
                    "application/json",
                ],
                "outputModes": [
                    "text/plain",
                    "application/json",
                ],
            },
        ],
    }

    if documentation_url is not None:
        if not documentation_url.startswith("https://"):
            raise ValueError("documentation_url must use https")
        card["documentationUrl"] = documentation_url

    return card
