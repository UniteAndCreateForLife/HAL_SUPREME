from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from continuity.world_manifest import load_world_manifest, validate_render_binding
from qc.continuity import require_continuity_audit


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a HAL persistent cinematic-world shot before/after rendering"
    )
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--shot", required=True)
    parser.add_argument("--expect-fingerprint")
    parser.add_argument(
        "--audit",
        type=Path,
        help="Optional VLM/deterministic continuity audit JSON",
    )
    args = parser.parse_args()

    manifest = load_world_manifest(args.manifest)
    fingerprint = validate_render_binding(
        manifest,
        args.shot,
        args.expect_fingerprint,
    )
    result = {
        "shot_id": args.shot,
        "continuity_fingerprint": fingerprint,
        "manifest": "pass",
    }
    if args.audit:
        audit = json.loads(args.audit.read_text(encoding="utf-8"))
        result["visual_audit"] = require_continuity_audit(audit)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
