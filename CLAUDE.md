# Claude Code guidance

Read and follow [AGENTS.md](AGENTS.md) before making changes. `AGENTS.md` is the canonical HAL SUPREME engineering contract; do not maintain a divergent copy of its rules here.

Claude-specific expectations:

- keep plans proportional to task complexity;
- preserve permission and approval boundaries;
- use focused tests before broad tests;
- when handing work to another worker, use the handoff fields defined in `AGENTS.md`;
- before claiming completion, report the exact verification that actually ran.

If this file and `AGENTS.md` ever disagree, follow `AGENTS.md` and fix this compatibility file.
