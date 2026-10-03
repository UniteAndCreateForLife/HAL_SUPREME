---
description: Implement the smallest verified HAL fix or feature slice
agent: build
---

Read AGENTS.md first. Implement this bounded task:

$ARGUMENTS

Before editing, inspect the relevant code, tests, instructions, and current diff. Define acceptance criteria, make the minimum coherent change, add or update regression coverage when behavior changes, run the focused verification, then run the broader relevant gate. Do not perform protected external actions unless this task explicitly authorizes them.

Finish with changed files, exact commands/results, residual risks, and any protected action still pending. If a task packet is part of the work, do not advance its status beyond the evidence actually produced; validate it with `python -m services.agent_fabric.contract <packet.json>`.
