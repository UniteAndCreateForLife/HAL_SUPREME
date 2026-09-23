from __future__ import annotations

import hashlib
import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib import parse

from twilio.request_validator import RequestValidator
from twilio.twiml.messaging_response import MessagingResponse

from services.twilio_searchlight_demo.interaction_receipt import (
    write_interaction_receipt,
)
from services.twilio_searchlight_demo.operator_adapter import (
    call_operator_conversation,
)

HOST = "127.0.0.1"
PORT = int(os.getenv("PORT", "8091"))
MAX_BODY_CHARS = 1600
MAX_REPLY_CHARS = 1200
MAX_FORM_BYTES = 16_384


def validate_twilio_request(
    webhook_url: str,
    form: dict[str, str],
    signature: str,
    auth_token: str,
) -> bool:
    """Validate an inbound Twilio form using Twilio's official SDK."""
    if not webhook_url or not signature or not auth_token:
        return False
    return RequestValidator(auth_token).validate(webhook_url, form, signature)


def call_hal_decision(
    decision_url: str,
    message_sid: str,
    body: str,
    timeout_seconds: float = 8.0,
) -> dict[str, str]:
    """Forward only the minimum message payload to HAL's decision service."""
    if not decision_url:
        raise ValueError("HAL_SEARCHLIGHT_DECISION_URL is required")
    return call_operator_conversation(
        decision_url,
        message_sid,
        body[:MAX_BODY_CHARS],
        timeout_seconds,
        MAX_REPLY_CHARS,
    )


def build_twiml(reply: str) -> str:
    response = MessagingResponse()
    response.message(reply)
    return str(response)


def process_incoming(
    webhook_url: str,
    form: dict[str, str],
    signature: str,
    auth_token: str,
    decision_url: str,
) -> tuple[int, str, dict[str, str]]:
    if not validate_twilio_request(webhook_url, form, signature, auth_token):
        return 403, build_twiml("Request rejected."), {"status": "invalid_signature"}
    message_sid = form.get("MessageSid", "").strip()
    body = form.get("Body", "").strip()
    if not message_sid or not body:
        return (
            400,
            build_twiml("MessageSid and Body are required."),
            {"status": "invalid_form"},
        )
    started = time.perf_counter()
    decision = call_hal_decision(decision_url, message_sid, body)
    elapsed_ms = (time.perf_counter() - started) * 1000
    event = {
        "status": "ok",
        "message_ref": hashlib.sha256(message_sid.encode()).hexdigest()[:12],
        "decision_id": decision["decision_id"],
        "elapsed_ms": f"{elapsed_ms:.1f}",
    }
    return 200, build_twiml(decision["reply"]), event


class Handler(BaseHTTPRequestHandler):
    server_version = "HALTwilioSearchlight/0.1"

    def _send(self, status: int, body: str, content_type: str) -> None:
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:
        if self.path == "/v1/health":
            body = json.dumps(
                {
                    "service": "hal-twilio-searchlight-demo",
                    "health": "healthy",
                    "signature_validation": "twilio_sdk",
                    "live_twilio_account_verified": False,
                    "receipt_capture_configured": bool(
                        os.getenv("HAL_SEARCHLIGHT_RECEIPT_DIR", "").strip()
                    ),
                    "source_sha_configured": bool(
                        os.getenv("HAL_SEARCHLIGHT_SOURCE_SHA", "").strip()
                    ),
                },
                sort_keys=True,
            )
            self._send(200, body, "application/json")
            return
        self._send(404, json.dumps({"error": "not_found"}), "application/json")

    def do_POST(self) -> None:
        if self.path != "/twilio/incoming":
            self._send(404, json.dumps({"error": "not_found"}), "application/json")
            return
        content_type = self.headers.get("Content-Type", "")
        if not content_type.lower().startswith("application/x-www-form-urlencoded"):
            self._send(415, build_twiml("Unsupported content type."), "text/xml")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send(400, build_twiml("Invalid content length."), "text/xml")
            return
        if length <= 0:
            self._send(400, build_twiml("Empty request body."), "text/xml")
            return
        if length > MAX_FORM_BYTES:
            self._send(413, build_twiml("Request body too large."), "text/xml")
            return

        auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        webhook_url = os.getenv("HAL_TWILIO_WEBHOOK_URL", "")
        decision_url = os.getenv("HAL_SEARCHLIGHT_DECISION_URL", "")
        if not auth_token or not webhook_url or not decision_url:
            self._send(
                503, build_twiml("Demo integration is not configured."), "text/xml"
            )
            return
        raw = self.rfile.read(length).decode("utf-8")
        form = {
            key: values[-1]
            for key, values in parse.parse_qs(raw, keep_blank_values=True).items()
        }
        signature = self.headers.get("X-Twilio-Signature", "")
        try:
            status, body, event = process_incoming(
                webhook_url, form, signature, auth_token, decision_url
            )
        except Exception as exc:
            event = {"status": "decision_unavailable", "error_type": type(exc).__name__}
            status, body = (
                503,
                build_twiml("HAL is temporarily unavailable. Please retry."),
            )
        if status == 200:
            receipt_dir = os.getenv("HAL_SEARCHLIGHT_RECEIPT_DIR", "").strip()
            source_sha = os.getenv("HAL_SEARCHLIGHT_SOURCE_SHA", "").strip()
            if receipt_dir:
                event = dict(event)
                try:
                    receipt_path = write_interaction_receipt(
                        Path(receipt_dir), event, source_sha, webhook_url, body
                    )
                    event["receipt_status"] = "written"
                    event["receipt_file"] = receipt_path.name
                except Exception as exc:
                    event["receipt_status"] = "error"
                    event["receipt_error_type"] = type(exc).__name__
        print(json.dumps(event, sort_keys=True))
        self._send(status, body, "text/xml")

    def log_message(self, fmt: str, *args: object) -> None:
        return


if __name__ == "__main__":
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
