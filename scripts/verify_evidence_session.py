from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evidence.runtime import verify_session


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the hash chain for a HAL evidence session.")
    parser.add_argument("session_dir", type=Path)
    args = parser.parse_args()
    result = verify_session(args.session_dir)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
