from __future__ import annotations

from dataclasses import dataclass
import socket
from typing import Callable

from .brain_bridge import (
    BrainRequest,
    BrainResponse,
    decode_frame,
    encode_frame,
    request_from_dict,
)


BrainPolicy = Callable[[BrainRequest], BrainResponse]


@dataclass(frozen=True)
class TCPBridgeConfig:
    host: str = "127.0.0.1"
    port: int = 9909
    connect_timeout_seconds: float = 5.0
    max_requests: int | None = None

    def validate(self) -> None:
        if self.host not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("development TCP brain bridge is loopback-only")
        if not (1 <= self.port <= 65535):
            raise ValueError("port must be between 1 and 65535")
        if self.connect_timeout_seconds <= 0:
            raise ValueError("connect_timeout_seconds must be positive")
        if self.max_requests is not None and self.max_requests < 1:
            raise ValueError("max_requests must be positive when provided")


def _read_jsonl_frame(reader) -> dict:
    raw = reader.readline()
    if not raw:
        raise EOFError("brain bridge peer closed the connection")
    return decode_frame(raw)


def run_tcp_brain_client(
    policy: BrainPolicy,
    *,
    config: TCPBridgeConfig,
) -> int:
    """Connect to a loopback arena bridge and answer JSONL brain requests.

    The arena remains authoritative. This client only receives one request,
    returns one validated response, and never mutates world state directly.
    """

    config.validate()
    handled = 0

    with socket.create_connection(
        (config.host, config.port),
        timeout=config.connect_timeout_seconds,
    ) as sock:
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        reader = sock.makefile("rb")

        while True:
            try:
                payload = _read_jsonl_frame(reader)
            except EOFError:
                break

            request = request_from_dict(payload)
            response = policy(request)
            response.validate_against(request)
            sock.sendall(encode_frame(response.to_dict()))

            handled += 1
            if config.max_requests is not None and handled >= config.max_requests:
                break

    return handled
