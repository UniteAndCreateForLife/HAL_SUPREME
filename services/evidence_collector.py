from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evidence.runtime import EvidenceSession


MAX_BODY_BYTES = 1024 * 1024


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True) + "\n").encode("utf-8")


class EvidenceHandler(BaseHTTPRequestHandler):
    server_version = "HALEvidenceCollector/1"

    @property
    def session(self) -> EvidenceSession:
        return self.server.session  # type: ignore[attr-defined]

    def _send(self, status: int, payload: Any) -> None:
        body = _json_bytes(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        raw_length = self.headers.get("Content-Length")
        if raw_length is None:
            raise ValueError("Content-Length required")
        length = int(raw_length)
        if length < 0 or length > MAX_BODY_BYTES:
            raise ValueError("request body too large")
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("JSON body must be an object")
        return payload

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send(200, {
                "status": "ok",
                "session_id": self.session.session_id,
                "session_dir": str(self.session.session_dir),
            })
            return
        self._send(404, {"error": "not_found"})

    def do_POST(self) -> None:
        try:
            payload = self._read_json()
            if self.path == "/v1/event":
                kind = str(payload.get("kind") or "").strip()
                if not kind:
                    raise ValueError("kind is required")
                data = payload.get("data") or {}
                if not isinstance(data, dict):
                    raise ValueError("data must be an object")
                event = self.session.emit(
                    kind,
                    message=str(payload.get("message") or ""),
                    phase=str(payload["phase"]) if payload.get("phase") is not None else None,
                    data=data,
                    source=str(payload["source"]) if payload.get("source") else None,
                )
                self._send(201, {
                    "seq": event["seq"],
                    "event_hash": event["event_hash"],
                    "session_id": event["session_id"],
                })
                return

            if self.path == "/v1/artifact":
                raw_path = payload.get("path")
                if not raw_path:
                    raise ValueError("path is required")
                record = self.session.register_artifact(
                    Path(str(raw_path)),
                    role=str(payload.get("role") or "output"),
                    copy_into_session=bool(payload.get("copy", True)),
                )
                self._send(201, record)
                return

            self._send(404, {"error": "not_found"})
        except (ValueError, json.JSONDecodeError) as exc:
            self._send(400, {"error": "bad_request", "detail": str(exc)})
        except FileNotFoundError as exc:
            self._send(404, {"error": "artifact_not_found", "detail": str(exc)})
        except Exception as exc:
            self._send(500, {"error": "internal_error", "detail": type(exc).__name__})

    def log_message(self, fmt: str, *args: Any) -> None:
        self.session.emit(
            "collector.http",
            phase="observe",
            message=fmt % args,
            data={"client": self.client_address[0]},
            source="evidence-collector",
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Local-only HTTP collector for HAL headless evidence events."
    )
    parser.add_argument("--session", required=True, type=Path)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9912)
    args = parser.parse_args()

    if args.host not in {"127.0.0.1", "::1", "localhost"}:
        parser.error("the built-in collector is intentionally loopback-only")

    session = EvidenceSession.open_existing(args.session)
    server = ThreadingHTTPServer((args.host, args.port), EvidenceHandler)
    server.session = session  # type: ignore[attr-defined]
    session.emit(
        "collector.started",
        phase="observe",
        message=f"http://{args.host}:{args.port}",
        data={"host": args.host, "port": args.port},
        source="evidence-collector",
    )
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        session.emit(
            "collector.stopped",
            phase="observe",
            message="collector stopped",
            source="evidence-collector",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
