from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from examples.agent_world_arena import (
    EpisodeRunner,
    MetaMuseAdapter,
    ProviderDescriptor,
    ScenarioManifest,
    ScriptedAdapter,
    build_arena,
)
from examples.agent_world_arena.baselines import greedy_resource_policy

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIO = (
    REPO_ROOT
    / "examples"
    / "agent_world_arena"
    / "scenarios"
    / "resource_rush_v0.json"
)


def load_manifest(path: Path) -> ScenarioManifest:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return ScenarioManifest.from_dict(payload)


def build_canary(max_steps: int) -> tuple[EpisodeRunner, dict[str, str]]:
    manifest = load_manifest(DEFAULT_SCENARIO)
    arena, assignment = build_arena(
        manifest,
        ["meta-muse", "scripted-baseline"],
    )

    muse = MetaMuseAdapter.from_environment()
    baseline = ScriptedAdapter(
        provider=ProviderDescriptor(
            provider_id="scripted-baseline",
            model="greedy-resource-v0",
            transport="local-python",
            capabilities=("agent-world-action",),
        ),
        policy=greedy_resource_policy,
    )
    runner = EpisodeRunner(
        arena,
        {
            "meta-muse": muse,
            "scripted-baseline": baseline,
        },
    )
    return runner, assignment


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a tightly bounded live Muse Spark Agent World connectivity canary."
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Required to make live Meta Model API calls.",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=4,
        choices=range(1, 9),
        metavar="1..8",
        help="Maximum simulation steps and therefore maximum Muse decisions.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for the sanitized replay summary.",
    )
    args = parser.parse_args()

    if not args.live:
        print(
            "Refusing live provider calls without --live. "
            "This canary would run resource-rush-v0 with at most "
            f"{args.max_steps} Muse decisions."
        )
        return 2

    runner, assignment = build_canary(args.max_steps)
    receipts = runner.run(max_steps=args.max_steps)

    summary = {
        "schema": "hal.agent_world.live_canary.v0",
        "scenario_id": runner.arena.episode_id,
        "provider_assignment": assignment,
        "steps_executed": len(receipts),
        "final_state": runner.arena.state_payload(),
        "receipts": receipts,
        "notes": [
            "Live Meta Model API calls were explicitly enabled with --live.",
            "MODEL_API_KEY is never included in this artifact.",
            "This is a connectivity canary, not a fair provider benchmark.",
        ],
    }

    rendered = json.dumps(summary, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
        print(f"Wrote sanitized canary summary to {args.output}")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
