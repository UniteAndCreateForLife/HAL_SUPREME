from __future__ import annotations

import argparse
from typing import Any

from .service import ArenaService, decode_json_object


def build_mcp_server(service: ArenaService | None = None):
    """Build the optional MCP surface around the dependency-free arena service."""

    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError(
            'The optional MCP server requires the current MCP Python SDK. '
            'Install it in an isolated environment with: pip install "mcp[cli]"'
        ) from exc

    authority = service or ArenaService()
    mcp = FastMCP(
        "HAL Agent World",
        instructions=(
            "Provider-neutral multi-agent simulation authority. "
            "Models submit bounded actions; the arena owns world state. "
            "This development server exposes no provider credentials or host shell."
        ),
        stateless_http=True,
    )

    @mcp.tool()
    def create_episode(
        scenario_json: str,
        provider_ids: list[str],
        episode_id: str = "",
    ) -> dict[str, Any]:
        """Create one reviewed in-memory episode from a scenario JSON object."""
        scenario = decode_json_object(scenario_json, label="scenario_json")
        return authority.create_episode(
            scenario,
            provider_ids,
            episode_id=episode_id or None,
        )

    @mcp.tool()
    def list_episodes() -> list[dict[str, Any]]:
        """List process-local Agent World episodes."""
        return authority.list_episodes()

    @mcp.tool()
    def read_observation(episode_id: str, agent_id: str) -> dict[str, Any]:
        """Read one agent's provider-independent observation."""
        return authority.observe(episode_id, agent_id)

    @mcp.tool()
    def submit_action(
        episode_id: str,
        agent_id: str,
        action_json: str,
    ) -> dict[str, Any]:
        """Submit exactly one bounded action for an agent's current tick."""
        action = decode_json_object(action_json, label="action_json")
        return authority.submit_action(episode_id, agent_id, action)

    @mcp.tool()
    def episode_status(episode_id: str) -> dict[str, Any]:
        """Read current tick, submissions and waiting agents."""
        return authority.status(episode_id)

    @mcp.tool()
    def advance_episode(episode_id: str) -> dict[str, Any]:
        """Commit a tick only after every enrolled agent has submitted."""
        return authority.advance(episode_id)

    @mcp.tool()
    def advance_episode_with_idle_timeout(
        episode_id: str,
        reason: str = "deadline",
    ) -> dict[str, Any]:
        """Explicitly fail missing agent actions to idle and commit the tick."""
        return authority.advance_with_idle_for_missing(
            episode_id,
            reason=reason,
        )

    @mcp.tool()
    def episode_replay(episode_id: str) -> dict[str, Any]:
        """Return replay receipts and deterministic state hashes."""
        return authority.replay(episode_id)

    return mcp


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the local HAL Agent World MCP development server."
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    if args.host not in {"127.0.0.1", "localhost", "::1"}:
        raise SystemExit(
            "Refusing non-loopback bind. Put authentication and transport security "
            "in front of Agent World before exposing it remotely."
        )

    mcp = build_mcp_server()
    mcp.run(
        transport="streamable-http",
        host=args.host,
        port=args.port,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
