from __future__ import annotations

import argparse
import sys
import time

from .brain_bridge import (
    BrainResponse,
    decode_frame,
    encode_frame,
    request_from_dict,
)


def choose_reference_action(request) -> dict:
    """Deterministic no-model reference policy for bridge verification."""
    if "idle" in request.allowed_actions:
        return {"kind": "idle"}
    return {"kind": request.allowed_actions[0]}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="HAL Agent World JSONL stdio brain bridge reference worker."
    )
    parser.add_argument(
        "--single",
        action="store_true",
        help="Process one request then exit.",
    )
    args = parser.parse_args()

    while True:
        raw = sys.stdin.buffer.readline()
        if not raw:
            break

        started = time.perf_counter_ns()
        try:
            request = request_from_dict(decode_frame(raw))
            action = choose_reference_action(request)
            elapsed_us = (time.perf_counter_ns() - started) // 1_000
            response = BrainResponse(
                request_id=request.request_id,
                episode_id=request.episode_id,
                tick=request.tick,
                slot_id=request.slot_id,
                action=action,
                diagnostics={
                    "worker": "reference-idle-v0",
                    "elapsed_us": int(elapsed_us),
                },
            )
            response.validate_against(request)
            sys.stdout.buffer.write(encode_frame(response.to_dict()))
            sys.stdout.buffer.flush()
        except Exception as exc:
            # Fail closed without echoing raw request content or hidden runtime data.
            sys.stderr.write(f"brain-bridge-error:{type(exc).__name__}\n")
            sys.stderr.flush()
            return 2

        if args.single:
            break

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
