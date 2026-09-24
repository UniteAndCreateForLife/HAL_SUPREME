---
name: livepeer-video-production
description: Use Livepeer Creative MCP for HAL video, image, audio, 3D, critique, editing, and finishing work. Apply when the user asks to inspect, plan, generate, repair, review, or finish private media with Livepeer.
---

# Livepeer video production

Use the connected Livepeer Creative MCP server as a production capability
provider for HAL. The server has a large live tool catalog, so discover current
tools and prices instead of relying on a fixed list or an old capability count.

## Start with live evidence

1. Call `list_capabilities` before choosing a model or production route.
2. Call `describe_capability` for each serious candidate.
3. Call `get_pricing`, `me_usage`, and `spend_cap` with `action=read` before any
   media-producing decision.
4. Treat tool metadata, availability, prices, balances, and job status as
   time-sensitive. Report the observation time and do not replace a failed
   read with an old value.

## Plan before execution

- Prefer `submit_plan` in proposal mode when a request needs several tools. A
  proposed plan may validate steps and estimate cost, but it must not execute.
- Use checkpoint, critique, scorecard, and cost-report tools to review existing
  work before replacing it.
- Reuse current HAL project inputs, continuity anchors, and accepted artifacts.
  Do not create another scheduler, ledger, or source of production truth.
- Keep new outputs private until they pass the active HAL technical, visual,
  audio, continuity, and evidence gates.

## Gate every provider mutation

Before calling a tool whose `readOnlyHint` is false, show the user:

- exact Livepeer tool and model or capability;
- exact source inputs and prompt summary;
- duration, dimensions, quantity, or other billable units;
- current unit price and total estimate;
- current grant or spend-cap evidence;
- expected outputs and the quality check that follows.

Obtain explicit confirmation for that exact operation. A general request to
connect or inspect Livepeer does not authorize generation, grant consumption,
upload, cancellation, checkpoint resumption, publication, or broadcast.

## Preserve HAL authority

- HAL WorkGraph and the active project production state remain task authority.
- Livepeer is a capability provider. Its job records and URLs are evidence,
  not a replacement task graph.
- Use the existing canonical HAL adapter and project pipeline when work must be
  incorporated into `projects/the_shape_of_signal_15_min`.
- Record provider job IDs, estimates, source lineage, output URLs, hashes when
  locally available, quality results, and confirmation evidence in the local
  execution receipt.
- Never place credentials, activation codes, bearer values, or secret URLs in
  prompts, work orders, logs, or user-facing responses.
- Never publish, broadcast, post, or submit media externally without a separate
  destination-specific approval.

## Report truthfully

Distinguish `planned`, `proposed`, `submitted`, `running`, `completed`,
`quality_passed`, and `published`. Do not describe a proposal as submitted or a
completed provider job as accepted HAL production media until local review and
evidence gates pass.
