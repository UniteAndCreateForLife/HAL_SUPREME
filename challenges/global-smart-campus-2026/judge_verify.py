from __future__ import annotations
import argparse, hashlib, json, pathlib, shutil, subprocess, sys, tempfile
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent
MVP = ROOT / "mvp"

def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def load_json(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))

def run(cmd: list[str], cwd: pathlib.Path) -> dict:
    cp = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    return {"command": cmd, "returncode": cp.returncode,
            "stdout_tail": cp.stdout[-4000:], "stderr_tail": cp.stderr[-4000:]}

def main() -> int:
    ap = argparse.ArgumentParser(description="Reproduce judge-facing HAL Campus acceptance gates.")
    ap.add_argument("--output", default="", help="Optional JSON receipt path")
    args = ap.parse_args()
    required = [ROOT / "APPLICATION_PACKET.md",
                ROOT / "HAL_CAMPUS_EVIDENCE_DESK_PROPOSAL_2026-09-23.pdf",
                ROOT / "HAL_CAMPUS_EVIDENCE_DESK_PITCH_2026-09-23.pdf",
                ROOT / "PRIVACY_THREAT_MODEL.md",
                ROOT / "MULTIARCH_CI_RECEIPT.json"]
    required += [MVP / "VALIDATION_RECEIPT.json", MVP / "LIVE_VALIDATION_RECEIPT.json",
                 MVP / "engine.py", MVP / "cases.json",
                 ROOT / "public_demo" / "src" / "worker.js"]
    missing = [str(p.relative_to(ROOT)) for p in required if not p.is_file()]
    validation = load_json(MVP / "VALIDATION_RECEIPT.json") if not missing else {}
    live = load_json(MVP / "LIVE_VALIDATION_RECEIPT.json") if not missing else {}
    multi = load_json(ROOT / "MULTIARCH_CI_RECEIPT.json") if not missing else {}
    static_checks = {
        "required_artifacts_present": not missing,
        "canonical_cases": validation.get("cases") == 3,
        "citation_validity_all": validation.get("citation_validity_all") is True,
        "zero_unsupported_material_claims": validation.get("unsupported_material_claims_total") == 0,
        "human_review_required": validation.get("human_review_required_all") is True,
        "live_cases_without_provider_error": live.get("aggregate", {}).get("cases_without_transport_or_model_error") == 3,
        "live_items_grounded": live.get("aggregate", {}).get("all_live_accepted_items_grounded") is True,
        "live_conflicts_match_seeded_truth": live.get("aggregate", {}).get("all_live_conflict_relations_match_seeded_truth") is True,
        "multiarch_ci_success": multi.get("conclusion") == "success",
        "multiarch_source_hash_match": multi.get("cross_platform_source_hash_match") is True,
        "multiarch_no_paid_compute": multi.get("paid_compute_used") is False,
    }
    unit = run([sys.executable, "-m", "unittest", "-q"], MVP)
    with tempfile.TemporaryDirectory(prefix="hal_judge_verify_") as td:
        bench_path = pathlib.Path(td) / "benchmark.json"
        bench = run([sys.executable, "benchmark_deterministic.py", "--iterations", "30",
                     "--output", str(bench_path)], MVP)
        bench_json = load_json(bench_path) if bench["returncode"] == 0 and bench_path.exists() else {}
    node = shutil.which("node")
    worker = run([node, "--check", str(ROOT / "public_demo" / "src" / "worker.js")], ROOT) if node else {"returncode": None, "skipped": "node unavailable"}
    dynamic_checks = {
        "unit_tests_pass": unit["returncode"] == 0,
        "benchmark_pass": bench["returncode"] == 0 and not bench_json.get("acceptance_failures"),
        "benchmark_external_model_calls_zero": bench_json.get("external_model_calls") == 0,
        "benchmark_paid_compute_false": bench_json.get("paid_compute_used") is False,
        "worker_syntax_pass_or_unavailable": worker.get("returncode") in (0, None),
    }
    passed = all(static_checks.values()) and all(dynamic_checks.values())
    receipt = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "project": "HAL Campus Evidence Desk",
        "verdict": "HAL_JUDGE_VERIFY_OK" if passed else "HAL_JUDGE_VERIFY_FAILED",
        "static_checks": static_checks,
        "dynamic_checks": dynamic_checks,
        "missing_artifacts": missing,
        "source_sha256": {
            "engine.py": sha256(MVP / "engine.py") if (MVP / "engine.py").exists() else None,
            "cases.json": sha256(MVP / "cases.json") if (MVP / "cases.json").exists() else None,
            "worker.js": sha256(ROOT / "public_demo" / "src" / "worker.js") if (ROOT / "public_demo" / "src" / "worker.js").exists() else None,
        },
        "benchmark": bench_json,
        "execution": {"unit_tests": unit, "worker_syntax": worker},
        "safety": {
            "external_model_calls_during_verification": 0,
            "paid_compute_required": False,
            "real_student_or_employee_data_required": False,
            "final_decision_automation": False,
        },
    }
    if args.output:
        out = pathlib.Path(args.output)
        if not out.is_absolute():
            out = ROOT / out
        out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(receipt["verdict"])
    print(json.dumps({"static_checks": static_checks, "dynamic_checks": dynamic_checks}, sort_keys=True))
    return 0 if passed else 1

if __name__ == "__main__":
    raise SystemExit(main())
