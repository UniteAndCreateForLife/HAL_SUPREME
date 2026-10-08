from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "hal.plan_inventory.v1"
AUTHORITY = "DERIVED_NON_AUTHORITATIVE"

_FIELD_PATTERNS = {
    "status": re.compile(
        r"^\s*(?:\*\*)?Status\s*:(?:\*\*)?\s*(.+?)\s*$",
        re.IGNORECASE,
    ),
    "owner": re.compile(
        r"^\s*(?:\*\*)?Owner\s*:(?:\*\*)?\s*(.+?)\s*$",
        re.IGNORECASE,
    ),
    "workgraph": re.compile(
        r"^\s*(?:\*\*)?(?:Canonical\s+)?WorkGraph(?:\s+task)?\s*:(?:\*\*)?\s*(.+?)\s*$",
        re.IGNORECASE,
    ),
}


class PlanInventoryError(ValueError):
    pass


def _extract_metadata(text: str) -> dict[str, str]:
    title = ""
    fields = {"status": "", "owner": "", "workgraph": ""}
    for line in text.splitlines()[:120]:
        stripped = line.strip()
        if not title and stripped.startswith("# "):
            title = stripped[2:].strip()
        for key, pattern in _FIELD_PATTERNS.items():
            if fields[key]:
                continue
            match = pattern.match(line)
            if match:
                fields[key] = match.group(1).strip()
    return {"title": title, **fields}


def inspect_plan(path: Path, now: datetime | None = None) -> dict[str, Any]:
    if not path.is_file():
        raise PlanInventoryError(f"plan is not a file: {path}")
    now = now or datetime.now(timezone.utc)
    modified = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    age_days = max(0.0, (now - modified).total_seconds() / 86400.0)
    metadata = _extract_metadata(path.read_text(encoding="utf-8", errors="replace"))
    return {
        "path": path.as_posix(),
        "title": metadata["title"] or path.stem,
        "status": metadata["status"],
        "owner": metadata["owner"],
        "workgraph": metadata["workgraph"],
        "modified_utc": modified.isoformat(timespec="seconds"),
        "filesystem_mtime_age_days": round(age_days, 1),
        "age_basis": "filesystem_mtime",
        "has_status": bool(metadata["status"]),
        "has_workgraph_link": bool(metadata["workgraph"]),
    }


def scan_plans(
    root: Path,
    *,
    wip_limit: int = 5,
    stale_days: float = 21.0,
    now: datetime | None = None,
) -> dict[str, Any]:
    if isinstance(wip_limit, bool) or not isinstance(wip_limit, int) or wip_limit < 1:
        raise PlanInventoryError("wip_limit must be an integer >= 1")
    if stale_days < 0:
        raise PlanInventoryError("stale_days must be >= 0")
    if not root.is_dir():
        raise PlanInventoryError(f"plan directory does not exist: {root}")

    plans = [inspect_plan(path, now=now) for path in sorted(root.glob("*.md"))]
    missing_status = [plan["path"] for plan in plans if not plan["has_status"]]
    missing_workgraph = [plan["path"] for plan in plans if not plan["has_workgraph_link"]]
    stale = [
        plan["path"]
        for plan in plans
        if plan["filesystem_mtime_age_days"] >= stale_days
    ]
    warnings: list[str] = []
    if len(plans) > wip_limit:
        warnings.append(
            f"active-plan count {len(plans)} exceeds derived WIP limit {wip_limit}"
        )
    if missing_status:
        warnings.append(f"{len(missing_status)} active plans have no explicit Status field")
    if missing_workgraph:
        warnings.append(
            f"{len(missing_workgraph)} active plans have no explicit WorkGraph linkage"
        )
    if stale:
        warnings.append(
            f"{len(stale)} active-plan files have filesystem mtime age >= {stale_days:g} days"
        )

    return {
        "schema": SCHEMA,
        "authority": AUTHORITY,
        "root": root.as_posix(),
        "policy": {
            "wip_limit": wip_limit,
            "filesystem_mtime_warning_days": stale_days,
            "mtime_is_plan_age": False,
        },
        "counts": {
            "plans": len(plans),
            "missing_status": len(missing_status),
            "missing_workgraph_link": len(missing_workgraph),
            "stale": len(stale),
        },
        "warnings": warnings,
        "missing_status": missing_status,
        "missing_workgraph_link": missing_workgraph,
        "stale": stale,
        "plans": plans,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inventory active plan documents without mutating them."
    )
    parser.add_argument("root", type=Path)
    parser.add_argument("--wip-limit", type=int, default=5)
    parser.add_argument("--stale-days", type=float, default=21.0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = scan_plans(
        args.root, wip_limit=args.wip_limit, stale_days=args.stale_days
    )
    encoded = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(encoded + "\n", encoding="utf-8")
    else:
        print(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
