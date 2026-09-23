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
            "budget_policy": "free_allocation_only",
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
            "budget_policy": "free_credit_only",
        },
        "local_hal": {
            "enabled": env_enabled("HAL_PROVIDER_LOCAL_ENABLED"),
            "kind": "private-worker",
            "capabilities": ["audio", "video", "comfyui"],
        },
    }


def choose_route(capability: str, providers: dict[str, dict[str, Any]] | None = None) -> dict[str, Any] | None:
    """Choose only enabled providers that explicitly advertise a capability."""
    inventory = providers if providers is not None else build_providers()
    eligible = [
        name
        for name, provider in inventory.items()
        if provider.get("enabled") and capability in provider.get("capabilities", [])
    ]
    if not eligible:
        return None
    return {
        "capability": capability,
        "provider": eligible[0],
        "fallbacks": eligible[1:] if FAILOVER else [],
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
    server_version = "HALComputeRouter/0.2"

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
