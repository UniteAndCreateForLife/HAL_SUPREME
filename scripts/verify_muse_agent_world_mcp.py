from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_URL = "http://127.0.0.1:8765/mcp"


def wait_for_server(url: str, *, timeout_seconds: float = 20.0) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None

    while time.monotonic() < deadline:
        try:
            request = Request(url, method="GET")
            with urlopen(request, timeout=1.0):
                return
        except HTTPError as exc:
            if 400 <= exc.code < 600:
                return
            last_error = exc
        except (URLError, TimeoutError, OSError) as exc:
            last_error = exc
        time.sleep(0.25)

    raise RuntimeError(f"Agent World MCP listener did not become reachable: {last_error}")


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
        "Use the MCP server named hal-agent-world. "
        "Call its list_episodes tool exactly once. "
        "Do not create or advance an episode. "
        "Return a concise statement confirming the tool result."
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
    )


def output_mentions_expected_tool(output: str) -> bool:
    return "list_episodes" in output and "hal-agent-world" in output


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "End-to-end smoke test: local Agent World MCP server -> Muse Code -> "
            "Agent World list_episodes tool."
        )
    )
    parser.add_argument(
        "--url",
        default=os.environ.get("HAL_AGENT_WORLD_MCP_URL", DEFAULT_URL),
    )
    parser.add_argument(
        "--max-model-steps",
        type=int,
        default=3,
        choices=range(1, 9),
        metavar="1..8",
    )
    parser.add_argument(
        "--no-start-server",
        action="store_true",
        help="Use an already-running Agent World MCP server.",
    )
    args = parser.parse_args()

    os.environ["HAL_AGENT_WORLD_MCP_URL"] = args.url
    muse = muse_binary()

    server: subprocess.Popen[str] | None = None
    try:
        if not args.no_start_server:
            server = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "examples.agent_world_arena.mcp_server",
                    "--transport",
                    "streamable-http",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "8765",
                ],
                cwd=REPO_ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
        wait_for_server(args.url)

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
        if not output_mentions_expected_tool(result.stdout):
            raise RuntimeError(
                "Muse completed, but the JSONL transcript did not contain both "
                "'hal-agent-world' and 'list_episodes'. Inspect the output above."
            )

        print(
            json.dumps(
                {
                    "schema": "hal.agent_world.muse_mcp_smoke.v0",
                    "status": "pass",
                    "server": "hal-agent-world",
                    "tool": "list_episodes",
                    "url": args.url,
                },
                indent=2,
            )
        )
        return 0
    finally:
        if server is not None and server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()


if __name__ == "__main__":
    raise SystemExit(main())
