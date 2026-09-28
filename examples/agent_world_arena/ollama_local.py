from __future__ import annotations

import os

from .http_action_adapter import JSONTransport, OpenAICompatibleActionAdapter


class OllamaActionAdapter(OpenAICompatibleActionAdapter):
    """Local Ollama profile using its OpenAI-compatible Chat Completions API."""

    def __init__(
        self,
        *,
        model: str,
        provider_id: str = "hal-local-ollama",
        base_url: str = "http://127.0.0.1:11434/v1",
        timeout_seconds: float = 30.0,
        max_completion_tokens: int = 256,
        transport: JSONTransport | None = None,
    ) -> None:
        if not model:
            raise ValueError("Ollama model is required")
        super().__init__(
            provider_id=provider_id,
            model=model,
            base_url=base_url,
            api_key="",
            timeout_seconds=timeout_seconds,
            max_completion_tokens=max_completion_tokens,
            reasoning_effort=None,
            structured_output=True,
            transport_label="ollama-openai-compatible",
            transport=transport,
        )

    @classmethod
    def from_environment(
        cls,
        *,
        provider_id: str = "hal-local-ollama",
        timeout_seconds: float = 30.0,
        max_completion_tokens: int = 256,
        transport: JSONTransport | None = None,
    ) -> "OllamaActionAdapter":
        model = os.environ.get("HAL_AGENT_WORLD_LOCAL_MODEL", "")
        if not model:
            raise RuntimeError("HAL_AGENT_WORLD_LOCAL_MODEL is not set")
        base_url = os.environ.get(
            "HAL_AGENT_WORLD_LOCAL_BASE_URL",
            "http://127.0.0.1:11434/v1",
        )
        return cls(
            model=model,
            provider_id=provider_id,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            max_completion_tokens=max_completion_tokens,
            transport=transport,
        )
