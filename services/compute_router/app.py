from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

HOST = "0.0.0.0"
PORT = int(os.getenv("PORT", "8080"))
QUALITY_GATE = os.getenv("HAL_QUALITY_GATE", "V11")
FAILOVER = os.getenv("HAL_FAILOVER_ENABLED", "true").lower() == "true"


def env_enabled(name: str, default: bool = False) -> bool:
    """Return a strict boolean feature flag from the environment."""
    fallback = "true" if default else "false"
    return os.getenv(name, fallback).strip().lower() == "true"


def build_providers() -> dict[str, dict[str, Any]]:
    """Build the provider inventory without exposing credentials."""
    return {
        "huggingface": {
            "enabled": env_enabled("HAL_PROVIDER_HUGGINGFACE_ENABLED"),
            "kind": "remote-compute",
            "capabilities": ["model_registry", "inference", "jobs"],
            "priority": 60,
            "budget_policy": "zero_gpu_or_verified_free_only",
            "requires_zero_spend_ready": True,
            "zero_spend_ready": env_enabled(
                "HAL_PROVIDER_HUGGINGFACE_ZERO_SPEND_READY"
            ),
        },
        "openrouter_free": {
            "enabled": env_enabled("HAL_PROVIDER_OPENROUTER_FREE_ENABLED"),
            "kind": "hosted-free-inference",
            "capabilities": [
                "inference",
                "coding",
                "classification",
                "agent_microtask",
            ],
            "priority": 10,
            "budget_policy": "free_models_only",
            "requires_zero_spend_ready": True,
            "zero_spend_ready": env_enabled(
                "HAL_PROVIDER_OPENROUTER_FREE_ZERO_SPEND_READY"
            ),
        },
        "github_actions": {
            "enabled": env_enabled("HAL_PROVIDER_GITHUB_ACTIONS_ENABLED"),
            "kind": "ci-compute",
            "capabilities": ["build", "test", "benchmark", "packaging"],
            "priority": 15,
            "budget_policy": "public_standard_runners_only",
            "requires_zero_spend_ready": True,
            "zero_spend_ready": env_enabled(
                "HAL_PROVIDER_GITHUB_ACTIONS_ZERO_SPEND_READY"
            ),
        },
        "cloudflare_workers_ai": {
            "enabled": env_enabled("HAL_PROVIDER_CLOUDFLARE_ENABLED"),
            "kind": "serverless-edge-inference",
            "capabilities": [
                "inference",
                "embeddings",
                "speech_to_text",
                "text_to_speech",
                "image_generation",
                "vision",
                "edge_api",
            ],
            "priority": 20,
            "budget_policy": "free_allocation_only",
            "requires_zero_spend_ready": True,
            "zero_spend_ready": env_enabled("HAL_PROVIDER_CLOUDFLARE_ZERO_SPEND_READY"),
        },
        "nvidia_nim": {
            "enabled": env_enabled("HAL_PROVIDER_NVIDIA_NIM_ENABLED"),
            "kind": "developer-hosted-inference",
            "capabilities": ["inference", "coding", "rag", "agent_eval"],
            "priority": 30,
            "budget_policy": "verified_developer_access_only",
            "requires_zero_spend_ready": True,
            "zero_spend_ready": env_enabled("HAL_PROVIDER_NVIDIA_NIM_ZERO_SPEND_READY"),
        },
        "modal": {
            "enabled": env_enabled("HAL_PROVIDER_MODAL_ENABLED"),
            "kind": "serverless-gpu",
            "capabilities": [
                "inference",
                "training",
                "fine_tuning",
                "scientific_compute",
                "media",
                "sandbox",
            ],
            "priority": 40,
            "budget_policy": "free_credit_only",
            "requires_zero_spend_ready": True,
            "zero_spend_ready": env_enabled("HAL_PROVIDER_MODAL_ZERO_SPEND_READY"),
        },
        "livepeer_creative": {
            "enabled": env_enabled("HAL_PROVIDER_LIVEPEER_CREATIVE_ENABLED"),
            "kind": "remote-media-worker",
            "capabilities": [
                "image_generation",
                "video",
                "audio",
                "media",
                "media_finishing",
            ],
            "priority": 45,
            "budget_policy": "registered_hacker_balance_only",
            "requires_zero_spend_ready": True,
            "zero_spend_ready": env_enabled(
                "HAL_PROVIDER_LIVEPEER_CREATIVE_ZERO_SPEND_READY"
            ),
        },
        "lightning_ai": {
            "enabled": env_enabled("HAL_PROVIDER_LIGHTNING_AI_ENABLED"),
            "kind": "gpu-studio-jobs",
            "capabilities": [
                "inference",
                "training",
                "fine_tuning",
                "scientific_compute",
                "media",
                "sandbox",
            ],
            "priority": 50,
            "budget_policy": "verified_free_credit_only",
            "requires_zero_spend_ready": True,
            "zero_spend_ready": env_enabled(
                "HAL_PROVIDER_LIGHTNING_AI_ZERO_SPEND_READY"
            ),
        },
        "local_hal": {
            "enabled": env_enabled("HAL_PROVIDER_LOCAL_ENABLED"),
            "kind": "private-worker",
            "capabilities": ["audio", "video", "comfyui", "media"],
            "priority": 5,
            "budget_policy": "local_operator_managed",
        },
    }


def choose_route(
    capability: str, providers: dict[str, dict[str, Any]] | None = None
) -> dict[str, Any] | None:
    """Choose an enabled capability only when any zero-spend gate is satisfied."""
    inventory = providers if providers is not None else build_providers()
    eligible = sorted(
        [
            name
            for name, provider in inventory.items()
            if provider.get("enabled")
            and capability in provider.get("capabilities", [])
            and (
                not provider.get("requires_zero_spend_ready", False)
                or provider.get("zero_spend_ready") is True
            )
        ],
        key=lambda name: (int(inventory[name].get("priority", 100)), name),
    )
    if not eligible:
        return None
    primary = inventory[eligible[0]]
    return {
        "capability": capability,
        "provider": eligible[0],
        "fallbacks": eligible[1:] if FAILOVER else [],
        "provider_kind": primary.get("kind", "unknown"),
        "budget_policy": primary.get("budget_policy", "operator_managed"),
        "quality_gate": QUALITY_GATE,
    }


def snapshot() -> dict[str, Any]:
    return {
        "service": "hal-compute-router",
        "health": "healthy",
        "quality_gate": QUALITY_GATE,
        "failover": FAILOVER,
        "providers": build_providers(),
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "HALComputeRouter/0.4"

    def _send(self, status: int, body: dict[str, Any]) -> None:
        payload = json.dumps(body, sort_keys=True).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:
        providers = build_providers()
        if self.path in ("/", "/v1/health"):
            self._send(200, snapshot())
            return
        if self.path == "/v1/capabilities":
            self._send(
                200,
                {
                    "route": True,
                    "health": True,
                    "provenance_required": env_enabled("HAL_REQUIRE_PROVENANCE", True),
                    "providers": providers,
                },
            )
            return
        self._send(404, {"error": "not_found"})

    def do_POST(self) -> None:
        if self.path != "/v1/route":
            self._send(404, {"error": "not_found"})
            return
        length = int(self.headers.get("Content-Length", "0"))
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self._send(400, {"error": "invalid_json"})
            return
        capability = str(body.get("capability", "")).strip()
        if not capability:
            self._send(400, {"error": "capability_required"})
            return
        decision = choose_route(capability)
        if decision is None:
            self._send(503, {"error": "no_eligible_provider", "capability": capability})
            return
        self._send(200, decision)

    def log_message(self, fmt: str, *args: Any) -> None:
        print(json.dumps({"component": "http", "message": fmt % args}))


if __name__ == "__main__":
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
