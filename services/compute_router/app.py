from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

HOST = "0.0.0.0"
PORT = int(os.getenv("PORT", "8080"))
QUALITY_GATE = os.getenv("HAL_QUALITY_GATE", "V11")
FAILOVER = os.getenv("HAL_FAILOVER_ENABLED", "true").lower() == "true"

PROVIDERS = {
    "huggingface": {
        "enabled": os.getenv("HAL_PROVIDER_HUGGINGFACE_ENABLED", "false").lower() == "true",
        "kind": "remote-compute",
        "capabilities": ["model_registry", "inference", "jobs"],
    },
    "local_hal": {
        "enabled": os.getenv("HAL_PROVIDER_LOCAL_ENABLED", "false").lower() == "true",
        "kind": "private-worker",
        "capabilities": ["audio", "video", "comfyui"],
    },
    "livepeer_creative": {
        "enabled": os.getenv("HAL_PROVIDER_LIVEPEER_CREATIVE_ENABLED", "false").lower() == "true",
        "kind": "remote-media-worker",
        "endpoint": os.getenv(
            "LIVEPEER_CREATIVE_MCP_URL",
            "https://agent.livepeer.org/api/mcp/creative",
        ),
        "capabilities": [
            "image",
            "video",
            "audio",
            "creative_project",
            "media_finishing",
        ],
    },
}

def snapshot() -> dict[str, Any]:
    return {
        "service": "hal-compute-router",
        "health": "healthy",
        "quality_gate": QUALITY_GATE,
        "failover": FAILOVER,
        "providers": PROVIDERS,
    }

class Handler(BaseHTTPRequestHandler):
    server_version = "HALComputeRouter/0.1"

    def _send(self, status: int, body: dict[str, Any]) -> None:
        payload = json.dumps(body, sort_keys=True).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:
        if self.path in ("/", "/v1/health"):
            self._send(200, snapshot())
            return
        if self.path == "/v1/capabilities":
            self._send(200, {
                "route": True,
                "health": True,
                "provenance_required": os.getenv("HAL_REQUIRE_PROVENANCE", "true").lower() == "true",
                "providers": PROVIDERS,
            })
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
        eligible = [
            name for name, provider in PROVIDERS.items()
            if provider["enabled"] and (
                capability in provider["capabilities"]
                or capability in {"audio", "video", "inference"}
            )
        ]
        if not eligible:
            self._send(503, {"error": "no_eligible_provider", "capability": capability})
            return
        self._send(200, {
            "capability": capability,
            "provider": eligible[0],
            "fallbacks": eligible[1:] if FAILOVER else [],
            "quality_gate": QUALITY_GATE,
        })

    def log_message(self, fmt: str, *args: Any) -> None:
        print(json.dumps({"component": "http", "message": fmt % args}))

if __name__ == "__main__":
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
