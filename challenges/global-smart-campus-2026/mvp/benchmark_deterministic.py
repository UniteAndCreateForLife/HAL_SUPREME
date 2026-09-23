from __future__ import annotations

import argparse
import hashlib
import json
import platform
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

from engine import analyze_case, load_cases

BASE = Path(__file__).resolve().parent


def sha256_normalized_text(path: Path) -> str:
    """Hash UTF-8 text after normalizing line endings for cross-platform receipts."""
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def percentile(values: list[float], pct: float) -> float:
    if not values:
        raise ValueError("values must not be empty")
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * pct)))
    return ordered[index]


def run(iterations: int) -> dict:
    cases = load_cases()
    latencies_ms: list[float] = []
    failures: list[dict] = []
    started = time.perf_counter()
    for iteration in range(iterations):
        for case in cases:
            t0 = time.perf_counter_ns()
            report = analyze_case(case)
            latencies_ms.append((time.perf_counter_ns() - t0) / 1_000_000)
            validation = report["validation"]
            if not (
                validation["citation_validity"] == 1.0
                and validation["conflict_detection"] is True
                and validation["unsupported_material_claims"] == 0
                and report["review_gate"]["status"] == "PENDING_HUMAN_REVIEW"
            ):
                failures.append({"iteration": iteration, "case_id": case["id"], "validation": validation})
    elapsed = time.perf_counter() - started
    total_reports = iterations * len(cases)
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "benchmark": "HAL Campus Evidence Desk deterministic acceptance engine",
        "iterations": iterations,
        "case_count": len(cases),
        "reports": total_reports,
        "elapsed_seconds": round(elapsed, 6),
        "reports_per_second": round(total_reports / elapsed, 2),
        "latency_ms": {
            "mean": round(statistics.fmean(latencies_ms), 6),
            "p50": round(percentile(latencies_ms, 0.50), 6),
            "p95": round(percentile(latencies_ms, 0.95), 6),
            "p99": round(percentile(latencies_ms, 0.99), 6),
            "max": round(max(latencies_ms), 6),
        },
        "acceptance_failures": failures,
        "all_acceptance_invariants_passed": not failures,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "source_sha256": {
            "engine.py": sha256_normalized_text(BASE / "engine.py"),
            "cases.json": sha256_normalized_text(BASE / "cases.json"),
        },
        "source_hash_policy": "UTF-8 text with CRLF/CR normalized to LF",
        "external_model_calls": 0,
        "paid_compute_used": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=10000)
    parser.add_argument("--output", default="BENCHMARK_RECEIPT.json")
    args = parser.parse_args()
    if args.iterations < 1:
        raise SystemExit("--iterations must be >= 1")
    receipt = run(args.iterations)
    output = BASE / args.output
    output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    if not receipt["all_acceptance_invariants_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
