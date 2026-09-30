from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evidence.runtime import EvidenceSession


def main() -> int:
    parser = argparse.ArgumentParser(description="Append a semantic event or artifact to a HAL evidence session.")
    parser.add_argument("kind", nargs="?", default="process.note")
    parser.add_argument("message", nargs="?", default="")
    parser.add_argument("--session", type=Path)
    parser.add_argument("--phase")
    parser.add_argument("--data-json", default="{}")
    parser.add_argument("--artifact", type=Path)
    parser.add_argument("--role", default="output")
    parser.add_argument("--no-copy", action="store_true")
    args = parser.parse_args()

    session_dir = args.session
    if session_dir is None:
        value = os.environ.get("HAL_EVIDENCE_SESSION_DIR")
        if not value:
            parser.error("use --session or set HAL_EVIDENCE_SESSION_DIR")
        session_dir = Path(value)

    session = EvidenceSession.open_existing(session_dir)
    if args.artifact is not None:
        record = session.register_artifact(
            args.artifact,
            role=args.role,
            copy_into_session=not args.no_copy,
        )
        print(json.dumps(record, indent=2, sort_keys=True))
        return 0

    try:
        data = json.loads(args.data_json)
    except json.JSONDecodeError as exc:
        parser.error(f"--data-json is invalid JSON: {exc}")
    if not isinstance(data, dict):
        parser.error("--data-json must decode to an object")
    event = session.emit(args.kind, message=args.message, phase=args.phase, data=data)
    print(json.dumps(event, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
