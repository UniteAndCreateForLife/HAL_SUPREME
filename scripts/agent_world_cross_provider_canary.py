from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from examples.agent_world_arena import (
    EpisodeRunner,
    MetaMuseAdapter,
    OllamaActionAdapter,
    ScenarioManifest,
    build_arena,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIO = (
    REPO_ROOT
    / "examples"
    / "agent_world_arena"
    / "scenarios"
    / "resource_rush_v0.json"
)


def load_manifest(path: Path) -> ScenarioManifest:
    return ScenarioManifest.from_dict(
        json.loads(path.read_text(encoding="utf-8"))
    )


def build_runner() -> tuple[EpisodeRunner, dict[str, str]]:
    manifest = load_manifest(DEFAULT_SCENARIO)
    muse = MetaMuseAdapter.from_environment()
    local = OllamaActionAdapter.from_environment()

    provider_ids = [muse.provider.provider_id, local.provider.provider_id]
    arena, assignment = build_arena(manifest, provider_ids)
    runner = EpisodeRunner(
        arena,
        {
            muse.provider.provider_id: muse,
            local.provider.provider_id: local,
        },
    )
    return runner, assignment


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run a bounded Muse Spark vs local Ollama Agent World canary "
            "through the exact same simulation contract."
        )
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Required before any live provider call is allowed.",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=4,
        choices=range(1, 9),
        metavar="1..8",
        help="Maximum world ticks. Each active provider gets at most one decision per tick.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for the sanitized replay summary.",
    )
    args = parser.parse_args()

    if not args.live:
        print(
            "Refusing provider calls without --live. "
            "Required private environment: MODEL_API_KEY for Meta and "
            "HAL_AGENT_WORLD_LOCAL_MODEL for Ollama. "
            f"Configured maximum would be {args.max_steps} ticks."
        )
        return 2

    runner, assignment = build_runner()
    receipts = runner.run(max_steps=args.max_steps)

    summary = {
        "schema": "hal.agent_world.cross_provider_canary.v0",
        "scenario_id": runner.arena.episode_id,
        "provider_assignment": assignment,
        "steps_executed": len(receipts),
        "final_state": runner.arena.state_payload(),
        "receipts": receipts,
        "notes": [
            "Live execution was explicitly enabled with --live.",
            "Provider credentials are excluded from this artifact.",
            "Both providers receive the same Agent World observation/action contract.",
            "This bounded canary is not a statistically meaningful benchmark.",
        ],
    }

    rendered = json.dumps(summary, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
        print(f"Wrote sanitized cross-provider canary to {args.output}")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
