from __future__ import annotations

import argparse
import json
from pathlib import Path

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
