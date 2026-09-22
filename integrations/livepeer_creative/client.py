from __future__ import annotations

import json
import os
import re
import uuid
from dataclasses import dataclass
from typing import Any, Callable, Mapping
from urllib import error as urlerror
from urllib import request as urlrequest


DEFAULT_ENDPOINT = "https://agent.livepeer.org/api/mcp/creative"
PROTOCOL_VERSION = "2025-03-26"


class McpError(RuntimeError):
    """Safe MCP client error. Secrets are redacted before messages escape."""


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    input_schema: dict[str, Any]


@dataclass
class TransportResponse:
    status: int
    headers: Mapping[str, str]
    body: str


Transport = Callable[[str, dict[str, str], str], TransportResponse]


class LivepeerCreativeClient:
    """Minimal Streamable HTTP MCP client for HAL.

    The client intentionally discovers tool schemas at runtime instead of
    hard-coding Livepeer's creative surface. That keeps HAL compatible as the
    creative profile grows and prevents stale tool signatures from becoming
    production behavior.
    """

    def __init__(
        self,
        endpoint: str | None = None,
        bearer: str | None = None,
        transport: Transport | None = None,
        client_name: str = "hal-supreme-livepeer-creative",
        client_version: str = "0.1.0",
    ) -> None:
        self.endpoint = (endpoint or os.getenv("LIVEPEER_CREATIVE_MCP_URL") or DEFAULT_ENDPOINT).strip()
        self.bearer = bearer if bearer is not None else os.getenv("LIVEPEER_MCP_BEARER", "")
        self.transport = transport or _http_transport
        self.client_name = client_name
        self.client_version = client_version
        self.session_id = ""
        self.initialized = False
        self._tools: dict[str, ToolDefinition] = {}

    def initialize(self) -> dict[str, Any]:
        if self.initialized:
            return {"already_initialized": True}
        payload = self._rpc(
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": self.client_name, "version": self.client_version},
            },
        )
        if payload.get("error"):
            raise McpError(f"Livepeer MCP initialize failed: {_safe(payload['error'])}")
        self.initialized = True
        # Streamable HTTP servers may accept this as a no-response notification.
        try:
            self._notify("notifications/initialized", {})
        except McpError:
            # The validated HAL Science Director transport works without the
            # notification, so a server that rejects it is still usable.
            pass
        return payload

    def list_tools(self, refresh: bool = False) -> list[ToolDefinition]:
        self.initialize()
        if self._tools and not refresh:
            return list(self._tools.values())
        payload = self._rpc("tools/list", {})
        if payload.get("error"):
            raise McpError(f"Livepeer MCP tools/list failed: {_safe(payload['error'])}")
        raw_tools = payload.get("result", {}).get("tools", [])
        tools: dict[str, ToolDefinition] = {}
        for item in raw_tools if isinstance(raw_tools, list) else []:
            name = str(item.get("name", "")).strip()
            if not name:
                continue
            tools[name] = ToolDefinition(
                name=name,
                description=str(item.get("description", "")).strip(),
                input_schema=item.get("inputSchema") if isinstance(item.get("inputSchema"), dict) else {},
            )
        self._tools = tools
        return list(tools.values())

    def get_tool(self, name: str) -> ToolDefinition:
        tools = {tool.name: tool for tool in self.list_tools()}
        if name not in tools:
            raise McpError(f"Livepeer creative tool not found: {name}")
        return tools[name]

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        self.initialize()
        # Discover first so callers fail before spending credits on a typo.
        self.get_tool(name)
        payload = self._rpc("tools/call", {"name": name, "arguments": arguments or {}})
        if payload.get("error") or payload.get("result", {}).get("isError"):
            detail = payload.get("error") or _collect_text(payload) or "unknown tool error"
            raise McpError(f"{name} failed: {_safe(detail)}")
        return payload

    def tool_names(self, refresh: bool = False) -> list[str]:
        return sorted(tool.name for tool in self.list_tools(refresh=refresh))

    def auth_mode(self) -> str:
        return "bearer" if self.bearer else "server-managed-or-keyless"

    def _rpc(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        request_id = str(uuid.uuid4())
        body = json.dumps(
            {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params},
            separators=(",", ":"),
        )
        response = self.transport(self.endpoint, self._headers(), body)
        self._capture_session(response.headers)
        if response.status < 200 or response.status >= 300:
            hint = ""
            if response.status in {401, 403}:
                hint = " Authentication is required; connect Livepeer in an MCP-capable client or supply an authorized bearer/session."
            raise McpError(
                f"Livepeer MCP HTTP {response.status}: {_safe(response.body[:500])}.{hint}".rstrip(".")
            )
        return _parse_rpc_body(response.body, request_id=request_id)

    def _notify(self, method: str, params: dict[str, Any]) -> None:
        body = json.dumps({"jsonrpc": "2.0", "method": method, "params": params}, separators=(",", ":"))
        response = self.transport(self.endpoint, self._headers(), body)
        self._capture_session(response.headers)
        if response.status < 200 or response.status >= 300:
            raise McpError(f"Livepeer MCP notification HTTP {response.status}: {_safe(response.body[:300])}")

    def _headers(self) -> dict[str, str]:
        headers = {
            "content-type": "application/json",
            "accept": "application/json, text/event-stream",
            "user-agent": f"{self.client_name}/{self.client_version}",
        }
        if self.session_id:
            headers["mcp-session-id"] = self.session_id
        if self.bearer:
            headers["authorization"] = f"Bearer {self.bearer}"
        return headers

    def _capture_session(self, headers: Mapping[str, str]) -> None:
        for key, value in headers.items():
            if key.lower() == "mcp-session-id" and value:
                self.session_id = str(value)
                return


def _http_transport(endpoint: str, headers: dict[str, str], body: str) -> TransportResponse:
    req = urlrequest.Request(endpoint, data=body.encode("utf-8"), headers=headers, method="POST")
    try:
        with urlrequest.urlopen(req, timeout=120) as resp:
            return TransportResponse(
                status=int(getattr(resp, "status", 200)),
                headers=dict(resp.headers.items()),
                body=resp.read().decode("utf-8", errors="replace"),
            )
    except urlerror.HTTPError as exc:
        return TransportResponse(
            status=int(exc.code),
            headers=dict(exc.headers.items()) if exc.headers else {},
            body=exc.read().decode("utf-8", errors="replace"),
        )
    except urlerror.URLError as exc:
        raise McpError(f"Livepeer MCP network error: {_safe(exc.reason)}") from exc


def _parse_rpc_body(text: str, request_id: str | None = None) -> dict[str, Any]:
    source = str(text or "").strip()
    if not source:
        # Valid for notifications, not for request/response RPC.
        raise McpError("Livepeer MCP returned an empty response.")
    if source.startswith("{"):
        return json.loads(source)

    payloads: list[dict[str, Any]] = []
    for frame in re.split(r"\r?\n\r?\n+", source):
        data_lines = []
        for line in frame.splitlines():
            if line.startswith("data:"):
                data_lines.append(line[5:].strip())
        if not data_lines:
            continue
        raw = "\n".join(data_lines)
        try:
            candidate = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict):
            payloads.append(candidate)

    if request_id:
        for payload in reversed(payloads):
            if str(payload.get("id", "")) == request_id:
                return payload
    if payloads:
        return payloads[-1]
    raise McpError("Livepeer MCP returned an unsupported response format.")


def _collect_text(payload: dict[str, Any]) -> str:
    content = payload.get("result", {}).get("content", [])
    if not isinstance(content, list):
        return ""
    return "\n".join(
        str(item.get("text"))
        for item in content
        if isinstance(item, dict) and isinstance(item.get("text"), str)
    )


def _safe(value: Any) -> str:
    text = value if isinstance(value, str) else json.dumps(value, default=str)
    text = re.sub(r"Bearer\s+[A-Za-z0-9._~+/-]+", "Bearer [redacted]", text, flags=re.I)
    text = re.sub(r"\b(sk[-_][A-Za-z0-9_-]{8,})\b", "sk_[redacted]", text)
    text = re.sub(r"(?i)(access[_ -]?code[=: ]+)[0-9]{6}", r"\1[redacted]", text)
    return text[:1000]
