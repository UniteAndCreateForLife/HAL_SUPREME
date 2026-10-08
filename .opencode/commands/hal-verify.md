---
description: Run bounded deterministic verification for the current HAL change
agent: hal-verifier
---

Verify the current change against AGENTS.md and this requested scope, if supplied:

$ARGUMENTS

Use focused checks first. If a task packet path is supplied, also validate it with `python -m services.agent_fabric.contract <packet.json>`. Report evidence, not confidence.
