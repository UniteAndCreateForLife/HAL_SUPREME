from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import subprocess
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib import error, parse, request

from twilio.request_validator import RequestValidator

from services.twilio_searchlight_demo.app import MAX_FORM_BYTES, Handler


class RehearsalDecisionHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        self.server.last_payload = payload
        self.server.call_count += 1
        response = json.dumps(
            {
                "reply": "HAL accepted the signed Twilio message for bounded review.",
                "decision_id": "decision-rehearsal-1",
            }
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def log_message(self, fmt: str, *args: object) -> None:
        return


@contextmanager
def temporary_environment(values: dict[str, str]):
    previous = {key: os.environ.get(key) for key in values}
    os.environ.update(values)
    try:
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def current_source_sha() -> str:
    repo_root = Path(__file__).resolve().parents[2]
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repo_root, text=True
    ).strip()


def _http_post_raw(
    url: str, payload: bytes, content_type: str, signature: str = "invalid"
) -> tuple[int, str]:
    req = request.Request(
        url,
        data=payload,
        headers={"Content-Type": content_type, "X-Twilio-Signature": signature},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=3) as response:
            return response.status, response.read().decode("utf-8")
    except error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8")


def _http_post(url: str, form: dict[str, str], signature: str) -> tuple[int, str]:
    payload = parse.urlencode(form).encode("utf-8")
    req = request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Twilio-Signature": signature,
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=3) as response:
            return response.status, response.read().decode("utf-8")
    except error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8")


def run_rehearsal(source_sha: str | None = None) -> dict[str, object]:
    source_sha = source_sha or current_source_sha()
    auth_token = "local-rehearsal-token-not-a-live-credential"
    signed_url = "https://searchlight-demo.invalid/twilio/incoming"

    decision = ThreadingHTTPServer(("127.0.0.1", 0), RehearsalDecisionHandler)
    decision.last_payload = None
    decision.call_count = 0
    decision_thread = threading.Thread(target=decision.serve_forever, daemon=True)
    decision_thread.start()

    webhook = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    webhook_thread = threading.Thread(target=webhook.serve_forever, daemon=True)
    webhook_thread.start()

    try:
        decision_url = f"http://127.0.0.1:{decision.server_address[1]}/decision"
        webhook_root = f"http://127.0.0.1:{webhook.server_address[1]}"
        local_url = f"{webhook_root}/twilio/incoming"
        health_url = f"{webhook_root}/v1/health"
        form = {
            "MessageSid": "SMREHEARSAL0001",
            "Body": "Route this bounded Searchlight demo through HAL",
        }
        signature = RequestValidator(auth_token).compute_signature(signed_url, form)

        with temporary_environment(
            {
                "TWILIO_AUTH_TOKEN": auth_token,
                "HAL_TWILIO_WEBHOOK_URL": signed_url,
                "HAL_SEARCHLIGHT_DECISION_URL": decision_url,
            }
        ):
            with request.urlopen(health_url, timeout=3) as response:
                health_status = response.status
                health = json.loads(response.read().decode("utf-8"))

            valid_status, valid_twiml = _http_post(local_url, form, signature)
            calls_after_valid = decision.call_count
            invalid_status, invalid_twiml = _http_post(local_url, form, "invalid")
            calls_after_invalid = decision.call_count
            unsupported_status, unsupported_twiml = _http_post_raw(
                local_url, b"{}", "application/json"
            )
            oversized_status, oversized_twiml = _http_post_raw(
                local_url,
                b"x" * (MAX_FORM_BYTES + 1),
                "application/x-www-form-urlencoded",
            )
            calls_after_envelope_rejections = decision.call_count

        forwarded = dict(decision.last_payload or {})
        checks = {
            "source_sha_is_git_sha": len(source_sha) == 40
            and all(c in "0123456789abcdef" for c in source_sha.lower()),
            "health_http_200": health_status == 200,
            "health_disclaims_live_account": health.get("live_twilio_account_verified")
            is False,
            "valid_signed_request_http_200": valid_status == 200,
            "valid_signed_request_returns_twiml": "<Response>" in valid_twiml
            and "HAL accepted the signed Twilio message" in valid_twiml,
            "valid_request_calls_hal_once": calls_after_valid == 1,
            "forwarded_payload_is_minimized": set(forwarded)
            == {"channel", "message_sid", "body"},
            "forwarded_channel_is_twilio_sms": forwarded.get("channel") == "twilio_sms",
            "invalid_signature_http_403": invalid_status == 403,
            "invalid_signature_does_not_call_hal": calls_after_invalid
            == calls_after_valid,
            "invalid_signature_returns_rejection_twiml": "Request rejected."
            in invalid_twiml,
            "unsupported_content_type_http_415": unsupported_status == 415,
            "unsupported_content_type_returns_twiml": "Unsupported content type."
            in unsupported_twiml,
            "oversized_request_http_413": oversized_status == 413,
            "oversized_request_returns_twiml": "Request body too large."
            in oversized_twiml,
            "envelope_rejections_do_not_call_hal": calls_after_envelope_rejections
            == calls_after_valid,
        }
        passed = all(checks.values())
        return {
            "schema_version": 1,
            "captured_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_sha": source_sha,
            "twilio_sdk": importlib.metadata.version("twilio"),
            "scope": "local signed-webhook rehearsal with mock HAL decision service; not a live Twilio account or Searchlight submission receipt",
            "boundaries": {
                "live_twilio_account_verified": False,
                "external_twilio_api_call": False,
                "money_spent": False,
                "application_submitted": False,
                "honoree_selected": False,
                "credits_awarded": False,
                "payment_received": False,
            },
            "health": health,
            "valid_request": {
                "http_status": valid_status,
                "twiml_contains_reply": checks["valid_signed_request_returns_twiml"],
                "hal_call_count": calls_after_valid,
            },
            "invalid_signature": {
                "http_status": invalid_status,
                "hal_call_count_after_attempt": calls_after_invalid,
            },
            "request_envelope": {
                "max_form_bytes": MAX_FORM_BYTES,
                "unsupported_content_type_http_status": unsupported_status,
                "oversized_request_http_status": oversized_status,
                "hal_call_count_after_rejections": calls_after_envelope_rejections,
            },
            "forwarded_payload": forwarded,
            "checks": checks,
            "passed": passed,
        }
    finally:
        webhook.shutdown()
        webhook.server_close()
        decision.shutdown()
        decision.server_close()


def write_receipt(path: Path, receipt: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(receipt, handle, indent=2, sort_keys=True)
        handle.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a local source-bound Twilio/HAL Searchlight rehearsal."
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = run_rehearsal()
    write_receipt(args.output, receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
