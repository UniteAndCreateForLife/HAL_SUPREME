from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

from services.twilio_searchlight_demo.operator_adapter import call_operator_conversation

SOURCE_SHA_RE = re.compile(r"[0-9a-f]{40}\Z")
DEFAULT_PREWARM_TIMEOUT_SECONDS = 45.0


def run_prewarm(
    decision_url: str,
    timeout_seconds: float = DEFAULT_PREWARM_TIMEOUT_SECONDS,
    source_sha: str = "",
) -> dict[str, object]:
    """Warm the canonical private-local conversation path before a live demo."""
    if timeout_seconds <= 0:
        raise ValueError("prewarm timeout must be positive")
    if source_sha and not SOURCE_SHA_RE.fullmatch(source_sha):
        raise ValueError("source SHA must be 40 lowercase hexadecimal characters")

    started = time.perf_counter()
    decision = call_operator_conversation(
        decision_url,
        "HAL_SEARCHLIGHT_LOCAL_PREWARM",
        "Return a short readiness acknowledgement.",
        timeout_seconds,
        160,
        max_wait_seconds=timeout_seconds,
    )
    elapsed_ms = (time.perf_counter() - started) * 1000
    return {
        "ready": True,
        "decision_id": decision["decision_id"],
        "model": decision.get("model", ""),
        "elapsed_ms": round(elapsed_ms, 1),
        "source_sha": source_sha or None,
        "scope": "local canonical HAL prewarm only; not a live Twilio interaction",
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Warm the canonical HAL Searchlight path"
    )
    parser.add_argument("--decision-url", required=True)
    parser.add_argument(
        "--timeout", type=float, default=DEFAULT_PREWARM_TIMEOUT_SECONDS
    )
    parser.add_argument("--source-sha", default="")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_prewarm(args.decision_url, args.timeout, args.source_sha)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temp = args.output.with_suffix(args.output.suffix + ".tmp")
        temp.write_text(payload, encoding="utf-8", newline="\n")
        temp.replace(args.output)
    print(payload, end="")


if __name__ == "__main__":
    main()
