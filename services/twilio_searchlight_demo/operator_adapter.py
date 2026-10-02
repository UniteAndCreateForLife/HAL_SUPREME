"""Bounded, private adapter to HAL's existing operator.conversation gateway."""

from __future__ import annotations

import hashlib
import json
import re
import time
from urllib import parse, request


MAX_GATEWAY_RESPONSE_BYTES = 512 * 1024
MAX_OPERATOR_WAIT_SECONDS = 8.0
POLL_INTERVAL_SECONDS = 0.15
PENDING_STATES = {"ACCEPTED", "VALIDATING", "EXECUTING", "VERIFYING"}
OPERATION_ID = re.compile(r"op_[A-Za-z0-9_-]{1,64}\Z")


def _gateway_origin(commands_url: str) -> str:
    """Restrict the HAL control-plane hop to the local operator gateway."""
    url = parse.urlsplit(commands_url)
    if (
        url.scheme != "http"
        or url.hostname not in {"127.0.0.1", "::1"}
        or url.path != "/operator/commands"
        or url.query
        or url.fragment
        or url.username
        or url.password
        or url.port is None
    ):
        raise ValueError("HAL operator gateway must be an exact loopback commands URL")
    return f"{url.scheme}://{url.netloc}"


def _json_request(url: str, timeout: float, payload: dict | None = None) -> dict:
    body = (
        json.dumps(payload, separators=(",", ":")).encode("utf-8") if payload else None
    )
    req = request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"} if body is not None else {},
        method="POST" if body is not None else "GET",
    )
    with request.urlopen(req, timeout=max(0.05, timeout)) as response:
        raw = response.read(MAX_GATEWAY_RESPONSE_BYTES + 1)
    if len(raw) > MAX_GATEWAY_RESPONSE_BYTES:
        raise ValueError("HAL operator gateway response too large")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("HAL operator gateway response must be an object")
    return value


def call_operator_conversation(
    commands_url: str,
    message_sid: str,
    body: str,
    timeout_seconds: float,
    max_reply_chars: int,
    max_wait_seconds: float = MAX_OPERATOR_WAIT_SECONDS,
) -> dict[str, str]:
    """Accept only a verified, real provider reply from canonical HAL."""
    origin = _gateway_origin(commands_url)
    if not message_sid or not body or timeout_seconds <= 0 or max_wait_seconds <= 0:
        raise ValueError("HAL operator conversation needs a message and timeout")
    deadline = time.monotonic() + min(timeout_seconds, max_wait_seconds)
    conversation_id = (
        "twilio_sms_" + hashlib.sha256(message_sid.encode()).hexdigest()[:24]
    )
    command = {
        "capability_id": "operator.conversation",
        "input": {
            "conversation_id": conversation_id,
            "text": body,
            "provider_mode": "private_local",
            "conversation_profile": "FAST_PRIVATE_CHOICE",
            "max_tokens": 192,
            "present_on_oracle": False,
        },
    }
    submission = _json_request(commands_url, deadline - time.monotonic(), command)
    operation_id = submission.get("operation_id")
    if (
        submission.get("capability_id") != "operator.conversation"
        or not isinstance(operation_id, str)
        or not OPERATION_ID.fullmatch(operation_id)
    ):
        raise ValueError("HAL operator gateway did not return a valid operation")

    operation_url = f"{origin}/operator/operations/{operation_id}"
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("HAL operator conversation exceeded webhook budget")
        operation = _json_request(operation_url, remaining)
        if (
            operation.get("operation_id") != operation_id
            or operation.get("capability_id") != "operator.conversation"
        ):
            raise ValueError("HAL operator operation identity mismatch")
        state = operation.get("state")
        if state == "VERIFIED":
            verification = operation.get("verification") or {}
            after = operation.get("after") or {}
            if not isinstance(verification, dict) or not isinstance(after, dict):
                raise ValueError("HAL operator verification is malformed")
            reply = after.get("reply")
            if (
                verification.get("verified") is not True
                or after.get("ok") is not True
                or after.get("response_state") != "PROVIDER_RESPONSE"
                or not isinstance(after.get("model"), str)
                or not after["model"].strip()
                or not isinstance(reply, str)
                or not reply.strip()
            ):
                raise ValueError("HAL operator reply lacks verified model evidence")
            return {
                "reply": reply.strip()[:max_reply_chars],
                "decision_id": operation_id,
                "model": after["model"].strip(),
            }
        if state not in PENDING_STATES:
            raise ValueError("HAL operator conversation did not verify")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("HAL operator conversation exceeded webhook budget")
        time.sleep(min(POLL_INTERVAL_SECONDS, remaining))
