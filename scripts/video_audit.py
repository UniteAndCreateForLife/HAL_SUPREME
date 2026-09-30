from __future__ import annotations

import argparse
import json
from pathlib import Path

from qc.motion import require_temporal_motion
from qc.video import audit_video


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a HAL video artifact before review or release")
    parser.add_argument("video", type=Path)
    parser.add_argument("--expected-duration", type=float)
    parser.add_argument("--duration-tolerance", type=float, default=0.75)
    parser.add_argument("--min-width", type=int)
    parser.add_argument("--min-height", type=int)
    parser.add_argument("--min-fps", type=float)
    parser.add_argument("--require-audio", action="store_true")
    parser.add_argument("--deep", action="store_true", help="Run freeze and black-segment detection")
    parser.add_argument("--max-freeze", type=float)
    parser.add_argument("--max-black", type=float)
    args = parser.parse_args()

    technical = audit_video(
        args.video,
        expected_duration_s=args.expected_duration,
        duration_tolerance_s=args.duration_tolerance,
        minimum_width=args.min_width,
        minimum_height=args.min_height,
        minimum_fps=args.min_fps,
        require_audio=args.require_audio,
        deep_scan=args.deep,
        max_freeze_s=args.max_freeze,
        max_black_s=args.max_black,
    )
    try:
        motion = require_temporal_motion(args.video)
    except Exception as exc:
        motion = {"passed": False, "error": str(exc)}

    report = {"video": str(args.video), "technical": technical, "motion": motion}
    report["passed"] = bool(technical["passed"] and motion.get("passed"))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
