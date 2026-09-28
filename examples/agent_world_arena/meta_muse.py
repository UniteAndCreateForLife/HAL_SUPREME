from __future__ import annotations

import os

from .http_action_adapter import JSONTransport, OpenAICompatibleActionAdapter


class MetaMuseAdapter(OpenAICompatibleActionAdapter):
    """Meta Model API profile for the generic Agent World chat adapter."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str = "muse-spark-1.3",
        base_url: str = "https://api.meta.ai/v1",
        timeout_seconds: float = 30.0,
        max_completion_tokens: int = 256,
        reasoning_effort: str = "low",
        transport: JSONTransport | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("Meta Model API key is required")
        super().__init__(
            provider_id="meta-muse",
            model=model,
            base_url=base_url,
            api_key=api_key,
            timeout_seconds=timeout_seconds,
            max_completion_tokens=max_completion_tokens,
            reasoning_effort=reasoning_effort,
            structured_output=True,
            transport_label="meta-model-api",
            transport=transport,
        )

    @classmethod
    def from_environment(
        cls,
        *,
        model: str = "muse-spark-1.3",
        base_url: str = "https://api.meta.ai/v1",
        timeout_seconds: float = 30.0,
        max_completion_tokens: int = 256,
        reasoning_effort: str = "low",
        transport: JSONTransport | None = None,
    ) -> "MetaMuseAdapter":
        api_key = os.environ.get("MODEL_API_KEY", "")
        if not api_key:
            raise RuntimeError("MODEL_API_KEY is not set")
        return cls(
            api_key=api_key,
            model=model,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            max_completion_tokens=max_completion_tokens,
            reasoning_effort=reasoning_effort,
            transport=transport,
        )
