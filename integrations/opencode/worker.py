from __future__ import annotations

import argparse
import base64
import ipaddress
import json
import os
import re
from pathlib import PurePosixPath, PureWindowsPath
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "http://127.0.0.1:4096"
DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_MAX_RESPONSE_BYTES = 4 * 1024 * 1024
MAX_PROMPT_CHARS = 100_000
HAL_MODES = frozenset({"plan", "fix", "review", "verify"})
SESSION_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,255}$")


class OpenCodeError(RuntimeError):
    """Base error for the HAL OpenCode adapter."""


class OpenCodeSecurityError(OpenCodeError):
    """Raised when an adapter call violates the bounded transport policy."""


class OpenCodeProtocolError(OpenCodeError):
    """Raised when OpenCode returns an unexpected protocol response."""


def _is_loopback_host(host: str | None) -> bool:
    if not host:
        return False
    normalized = host.rstrip(".").lower()
    if normalized == "localhost":
        return True
    try:
        return ipaddress.ip_address(normalized).is_loopback
    except ValueError:
        return False


def _is_absolute_directory(value: str) -> bool:
    return PurePosixPath(value).is_absolute() or PureWindowsPath(value).is_absolute()


def _require_session_id(session_id: str) -> str:
    if not isinstance(session_id, str) or not SESSION_ID_RE.fullmatch(session_id):
        raise OpenCodeProtocolError("invalid OpenCode session id")
    return session_id


def _unwrap_data(payload: object, *, context: str) -> Any:
    if not isinstance(payload, dict) or "data" not in payload:
        raise OpenCodeProtocolError(f"{context} response missing data field")
    return payload["data"]


class OpenCodeClient:
    """Small, fail-closed client for OpenCode V2 session APIs.

    The adapter intentionally exposes session creation, prompt admission, wait,
    context reads, health, active-session reads, and interrupt. It does not
    expose OpenCode shell execution or permission-approval endpoints.
    """

    def __init__(
        self,
        base_url: str | None = None,
        *,
        username: str | None = None,
        password: str | None = None,
        allow_remote: bool = False,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        max_response_bytes: int = DEFAULT_MAX_RESPONSE_BYTES,
    ) -> None:
        raw_url = (base_url or os.getenv("HAL_OPENCODE_URL") or DEFAULT_BASE_URL).rstrip("/")
        parsed = urlparse(raw_url)

        if parsed.scheme not in {"http", "https"}:
            raise OpenCodeSecurityError("OpenCode base URL must use http or https")
        if parsed.username or parsed.password:
            raise OpenCodeSecurityError("credentials must not be embedded in the OpenCode base URL")
        if parsed.path not in {"", "/"} or parsed.params or parsed.query or parsed.fragment:
            raise OpenCodeSecurityError("OpenCode base URL must not contain a path, query, or fragment")
        is_loopback = _is_loopback_host(parsed.hostname)
        if not allow_remote and not is_loopback:
            raise OpenCodeSecurityError(
                "remote OpenCode endpoints are disabled; use loopback or explicitly opt in with allow_remote=True"
            )
        if allow_remote and not is_loopback and parsed.scheme != "https":
            raise OpenCodeSecurityError("remote OpenCode endpoints require https")
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        if max_response_bytes < 1:
            raise ValueError("max_response_bytes must be positive")

        self.base_url = raw_url
        self.username = username or os.getenv("OPENCODE_SERVER_USERNAME") or "opencode"
        self.password = password if password is not None else os.getenv("OPENCODE_SERVER_PASSWORD")
        self.timeout = float(timeout)
        self.max_response_bytes = int(max_response_bytes)

    def _headers(self, *, has_body: bool) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if has_body:
            headers["Content-Type"] = "application/json"
        if self.password:
            token = base64.b64encode(f"{self.username}:{self.password}".encode("utf-8")).decode("ascii")
            headers["Authorization"] = f"Basic {token}"
        return headers

    def _request(
        self,
        method: str,
        path: str,
        *,
        payload: object | None = None,
        expected_status: tuple[int, ...] = (200,),
    ) -> object | None:
        if not path.startswith("/"):
            raise OpenCodeProtocolError("request path must be absolute")

        data = None
        if payload is not None:
            data = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

        request = Request(
            f"{self.base_url}{path}",
            data=data,
            method=method,
            headers=self._headers(has_body=payload is not None),
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                status = int(response.status)
                if status not in expected_status:
                    raise OpenCodeProtocolError(f"OpenCode returned unexpected HTTP {status} for {method} {path}")
                if status == 204:
                    return None
                raw = response.read(self.max_response_bytes + 1)
        except HTTPError as exc:
            raise OpenCodeProtocolError(
                f"OpenCode returned HTTP {exc.code} for {method} {path}"
            ) from None
        except URLError as exc:
            reason = type(exc.reason).__name__ if getattr(exc, "reason", None) is not None else "network error"
            raise OpenCodeProtocolError(
                f"OpenCode request failed for {method} {path}: {reason}"
            ) from None

        if len(raw) > self.max_response_bytes:
            raise OpenCodeProtocolError("OpenCode response exceeded the configured byte limit")
        if not raw:
            return None
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise OpenCodeProtocolError("OpenCode returned a non-JSON response") from None

    def health(self) -> dict[str, Any]:
        payload = self._request("GET", "/global/health")
        if not isinstance(payload, dict) or payload.get("healthy") is not True:
            raise OpenCodeProtocolError("OpenCode health response is not healthy")
        version = payload.get("version")
        if version is not None and not isinstance(version, str):
            raise OpenCodeProtocolError("OpenCode health version must be a string")
        return payload

    def active_sessions(self) -> dict[str, Any]:
        payload = self._request("GET", "/api/session/active")
        data = _unwrap_data(payload, context="active sessions")
        if not isinstance(data, dict):
            raise OpenCodeProtocolError("active sessions data must be an object")
        return data

    def create_session(self, directory: str, *, agent: str | None = None) -> dict[str, Any]:
        if not isinstance(directory, str) or not _is_absolute_directory(directory):
            raise OpenCodeSecurityError("OpenCode session directory must be an absolute path")

        body: dict[str, Any] = {"location": {"directory": directory}}
        if agent is not None:
            if not isinstance(agent, str) or not agent.strip():
                raise OpenCodeProtocolError("agent must be a non-empty string")
            body["agent"] = agent.strip()

        payload = self._request("POST", "/api/session", payload=body)
        data = _unwrap_data(payload, context="session create")
        if not isinstance(data, dict):
            raise OpenCodeProtocolError("session create data must be an object")
        _require_session_id(data.get("id"))
        return data

    def prompt(self, session_id: str, text: str, *, resume: bool = True) -> dict[str, Any]:
        session = quote(_require_session_id(session_id), safe="")
        if not isinstance(text, str) or not text.strip():
            raise OpenCodeProtocolError("prompt text must be non-empty")
        if len(text) > MAX_PROMPT_CHARS:
            raise OpenCodeSecurityError(f"prompt exceeds {MAX_PROMPT_CHARS} characters")

        payload = self._request(
            "POST",
            f"/api/session/{session}/prompt",
            payload={"prompt": {"text": text}, "resume": bool(resume)},
        )
        data = _unwrap_data(payload, context="prompt")
        if not isinstance(data, dict):
            raise OpenCodeProtocolError("prompt admission data must be an object")
        return data

    def wait(self, session_id: str) -> None:
        session = quote(_require_session_id(session_id), safe="")
        self._request(
            "POST",
            f"/api/session/{session}/wait",
            expected_status=(200, 204),
        )

    def context(self, session_id: str) -> list[dict[str, Any]]:
        session = quote(_require_session_id(session_id), safe="")
        payload = self._request("GET", f"/api/session/{session}/context")
        data = _unwrap_data(payload, context="session context")
        if not isinstance(data, list) or any(not isinstance(item, dict) for item in data):
            raise OpenCodeProtocolError("session context data must be an array of objects")
        return data

    def interrupt(self, session_id: str) -> None:
        session = quote(_require_session_id(session_id), safe="")
        self._request(
            "POST",
            f"/api/session/{session}/interrupt",
            expected_status=(200, 204),
        )

    def run_hal_task(
        self,
        *,
        directory: str,
        mode: str,
        task: str,
        agent: str | None = None,
    ) -> dict[str, Any]:
        normalized_mode = mode.strip().lower() if isinstance(mode, str) else ""
        if normalized_mode not in HAL_MODES:
            raise OpenCodeSecurityError(
                f"unsupported HAL mode {mode!r}; expected one of: {', '.join(sorted(HAL_MODES))}"
            )
        if not isinstance(task, str) or not task.strip():
            raise OpenCodeProtocolError("task must be a non-empty string")

        session = self.create_session(directory, agent=agent)
        session_id = session["id"]
        instruction = (
            "Read AGENTS.md first. Then read "
            f".opencode/commands/hal-{normalized_mode}.md and follow that project command's "
            f"instructions for this task.\n\nTASK:\n{task.strip()}"
        )
        admitted = self.prompt(session_id, instruction)
        self.wait(session_id)
        context = self.context(session_id)
        return {
            "schema": "hal.opencode_worker_result.v1",
            "session_id": session_id,
            "mode": normalized_mode,
            "admitted": admitted,
            "context": context,
        }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bounded HAL adapter for an OpenCode V2 server")
    parser.add_argument("--base-url", default=None, help="Defaults to HAL_OPENCODE_URL or http://127.0.0.1:4096")

    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("health", help="Check the OpenCode server")

    run = sub.add_parser("run", help="Run one HAL engineering task through OpenCode")
    run.add_argument("--directory", required=True)
    run.add_argument("--mode", required=True, choices=sorted(HAL_MODES))
    run.add_argument("--task", required=True)
    run.add_argument("--agent", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    client = OpenCodeClient(base_url=args.base_url)

    if args.command == "health":
        print(json.dumps(client.health(), indent=2))
        return 0

    result = client.run_hal_task(
        directory=args.directory,
        mode=args.mode,
        task=args.task,
        agent=args.agent,
    )
    print(
        json.dumps(
            {
                "schema": result["schema"],
                "session_id": result["session_id"],
                "mode": result["mode"],
                "context_messages": len(result["context"]),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
