from __future__ import annotations

import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from engine import analyze_case, analyze_case_with_model, load_cases
from live_model import provider_status

BASE = Path(__file__).resolve().parent
CASES = {case["id"]: case for case in load_cases()}


def _json_bytes(data: object) -> bytes:
    return json.dumps(data, indent=2).encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    server_version = "HALCampusEvidenceDesk/0.2"

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self'")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/status":
            return self._send(200, _json_bytes({
                "service": "HAL Campus Evidence Desk",
                "version": "0.2",
                "data_class": "synthetic_demo_only",
                "human_review_required": True,
                "providers": provider_status(),
            }), "application/json; charset=utf-8")
        if parsed.path == "/api/cases":
            rows = [
                {"id": c["id"], "title": c["title"], "question": c["question"], "evidence": c["evidence"]}
                for c in CASES.values()
            ]
            return self._send(200, _json_bytes(rows), "application/json; charset=utf-8")
        if parsed.path == "/api/analyze":
            query = parse_qs(parsed.query)
            case_id = query.get("id", [""])[0]
            mode = query.get("mode", ["deterministic"])[0]
            provider = query.get("provider", ["nvidia"])[0]
            case = CASES.get(case_id)
            if not case:
                return self._send(404, _json_bytes({"error": "case_not_found"}), "application/json; charset=utf-8")
            if mode == "live":
                report = analyze_case_with_model(case, provider=provider)
            elif mode == "deterministic":
                report = analyze_case(case)
                report["mode"] = "deterministic"
            else:
                return self._send(400, _json_bytes({"error": "unsupported_mode"}), "application/json; charset=utf-8")
            return self._send(200, _json_bytes(report), "application/json; charset=utf-8")
        if parsed.path in {"/", "/index.html"}:
            body = (BASE / "index.html").read_bytes()
            return self._send(200, body, "text/html; charset=utf-8")
        candidate = (BASE / parsed.path.lstrip("/")).resolve()
        if BASE not in candidate.parents or not candidate.is_file():
            return self._send(404, b"not found", "text/plain; charset=utf-8")
        mime = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        return self._send(200, candidate.read_bytes(), mime)

    def log_message(self, fmt: str, *args: object) -> None:
        print("HAL Campus Evidence Desk:", fmt % args)


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8789), Handler)
    print("HAL Campus Evidence Desk MVP: http://127.0.0.1:8789")
    print("Synthetic/public test data only. Human review is mandatory.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
