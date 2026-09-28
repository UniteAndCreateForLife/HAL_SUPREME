from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[1]


def muse_binary() -> str:
    candidate = shutil.which("muse")
    if candidate is None:
        raise RuntimeError(
            "Muse Code is not on PATH. Install it from Meta's official Muse Code "
            "installer and complete Meta sign-in first."
        )
    return candidate


def run_muse_probe(
    muse: str,
    *,
    workspace: Path,
    max_model_steps: int,
) -> subprocess.CompletedProcess[str]:
    prompt = (
        "Use only the MCP server named hal-agent-world. "
        "Discover its tools and invoke the read-only tool that lists current "
        "Agent World episodes exactly once. Do not create, submit, advance, or "
        "modify any episode. After the tool returns, report the number of episodes."
    )
    return subprocess.run(
        [
            muse,
            "exec",
            "--json",
            "--max-model-steps",
            str(max_model_steps),
            "--workspace",
            str(workspace),
            "--trust-workspace",
            prompt,
        ],
        cwd=workspace,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=180,
        check=False,
        env=os.environ.copy(),
    )


def jsonl_has_tool_call(output: str, tool_name: str) -> bool:
    for line in output.splitlines():
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        rendered = json.dumps(payload, sort_keys=True).lower()
        if tool_name.lower() in rendered and (
            "tool" in rendered or "mcp" in rendered
        ):
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Authenticated Muse Code -> HAL Agent World MCP smoke test. "
            "Muse should launch the required stdio MCP server from its settings."
        )
    )
    parser.add_argument(
        "--max-model-steps",
        type=int,
        default=3,
        choices=range(1, 9),
        metavar="1..8",
    )
    args = parser.parse_args()

    muse = muse_binary()
    result = run_muse_probe(
        muse,
        workspace=REPO_ROOT,
        max_model_steps=args.max_model_steps,
    )
    print(result.stdout)

    if result.returncode != 0:
        raise RuntimeError(
            f"Muse MCP probe failed with exit code {result.returncode}"
        )
    if not jsonl_has_tool_call(result.stdout, "list_episodes"):
        raise RuntimeError(
            "Muse completed, but no JSONL MCP/tool event referenced list_episodes. "
            "Run /mcp interactively and inspect the transcript above."
        )

    print(
        json.dumps(
            {
                "schema": "hal.agent_world.muse_mcp_smoke.v1",
                "status": "pass",
                "server": "hal-agent-world",
                "tool": "list_episodes",
                "transport": "stdio",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
