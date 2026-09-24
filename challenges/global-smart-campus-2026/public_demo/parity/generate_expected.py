"""Generate parity/gate_expected.json from the Python reference implementation.

Run from challenges/global-smart-campus-2026/public_demo after export_fixtures.js:

    node parity/export_fixtures.js
    python parity/generate_expected.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MVP = HERE.parents[1] / "mvp"
sys.path.insert(0, str(MVP))

from engine import analyze_case, load_cases  # noqa: E402
from live_model import normalize_synthesis  # noqa: E402


def expected() -> dict:
    cases = {case["id"]: case for case in load_cases()}
    fixtures = json.loads((HERE / "gate_fixtures.json").read_text(encoding="utf-8"))
    return {
        "reports": {case_id: analyze_case(case) for case_id, case in cases.items()},
        "normalized": [
            {"name": f["name"], "case_id": f["case_id"], "result": normalize_synthesis(cases[f["case_id"]], f["payload"])}
            for f in fixtures
        ],
    }


if __name__ == "__main__":
    out = HERE / "gate_expected.json"
    out.write_text(json.dumps(expected(), indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {out.name}")
