---
title: HAL Campus Evidence Desk
emoji: 🧾
colorFrom: gray
colorTo: blue
sdk: static
license: apache-2.0
pinned: false
short_description: Try to sneak an uncited claim past an evidence gate
tags:
  - hallucination
  - citations
  - evaluation
  - llm-safety
  - agents
---

# HAL Campus Evidence Desk

Model findings about campus operations only count if they cite supplied evidence.
This Space runs the deterministic acceptance layer from HAL Campus Evidence Desk
entirely in your browser.

**Try it:** pick a synthetic case, then run a model draft through the gate. Drafts
with no citation, invented evidence IDs, conflicts the evidence does not support, or
malformed items are rejected with the reason. You can also edit the JSON yourself.

- The browser gate is a port of the Python engine and is tested to give identical
  results on 25 drafts and edge cases.
- All data is synthetic. Conflicts are checked against each case's seeded ground truth.
- No model is called from this page. Accepted items still go to a human reviewer.

Source, tests and receipts:
https://github.com/UniteAndCreateForLife/HAL_SUPREME/tree/main/challenges/global-smart-campus-2026
