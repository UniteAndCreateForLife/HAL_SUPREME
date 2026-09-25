# Evidence Gate

Keep only the parts of an LLM draft that cite evidence you supplied.

When a model writes findings, recommendations or "conflicts" from documents you gave it, an
ungrounded sentence reads exactly like a grounded one. Evidence Gate is a deterministic
acceptance layer you run on the model's output before a person sees it:

- a finding or action survives only if every citation names a supplied evidence ID;
- a claimed conflict survives only if its two evidence IDs form a pair you declared;
- everything else is rejected with a reason, never silently dropped.

One file, standard library only, Python 3.9 or newer. No model calls.

## Try it

Copy `evidence_gate.py` into your project.

```python
from evidence_gate import check

evidence = [
    {"id": "E1", "text": "Memo A: after-hours lab access needs chair approval."},
    {"id": "E2", "text": "Memo B: trained staff can get access from the security office."},
]
draft = {  # what the model returned
    "findings": [
        {"text": "Memo A requires chair approval.", "citations": ["E1"]},
        {"text": "A prior incident report supports approval.", "citations": ["E9"]},
    ],
    "conflicts": [{"detail": "The memos prescribe different approval paths.", "evidence": ["E1", "E2"]}],
}

result = check(draft, evidence, conflicts=[("E1", "E2")])
result.accepted["findings"]   # [{"text": "Memo A requires chair approval.", "citations": ["E1"]}]
result.accepted["conflicts"]  # [{"detail": "The memos prescribe ...", "evidence": ["E1", "E2"]}]
result.rejected               # [{"section": "findings", "index": 1, "reason": "unknown_evidence",
                              #   "invalid_citations": ["E9"]}]
result.ok                     # False: something was rejected
result.to_dict()              # the same as JSON-ready data, with counts and missed_conflicts
```

From the command line:

```bash
python evidence_gate.py draft.json --evidence E1 E2 E3 --conflict E1,E2
```

It prints the result as JSON and exits with 0 when everything was accepted, 1 when something
was rejected, and 2 when the input could not be read.

## Why an item is rejected

| Reason | Meaning |
|---|---|
| `no_citation` | The item cites nothing, or its citations are not a list |
| `unknown_evidence` | At least one citation is not a supplied evidence ID (listed in `invalid_citations`) |
| `too_many_citations` | More than 6 different IDs (configurable with `max_citations`) |
| `empty_text` | No text left after cleaning |
| `conflict_needs_two_ids` | A conflict must name exactly two different evidence IDs |
| `unsupported_conflict` | The pair is not one you declared in `conflicts` |
| `over_limit` | The section has more rows than its limit (50 by default; set `limits`) |
| `not_an_object` / `not_a_list` | The draft, a section or a row has the wrong shape |

## Choices worth knowing

- **No partial acceptance.** One unknown ID rejects the whole item, so a real citation cannot
  vouch for an invented one.
- **Nothing disappears quietly.** Rows over a limit are rejected with a reason, not skipped.
- **Every citation is checked.** Repeated IDs count once, and the whole list is checked, so an
  invented ID cannot hide behind the cap.
- **Conflicts need your rules.** Pass the pairs your evidence really supports. Without them,
  every claimed conflict is rejected. `missed_conflicts` lists declared pairs the draft did not
  report, which is often the most useful signal for a reviewer.
- **Accepted text is cleaned.** Whitespace is collapsed; control characters and invisible
  format characters (zero-width characters, bidirectional overrides, Unicode tag characters) are
  removed, so accepted text cannot carry hidden instructions. Other languages are kept. Text is
  capped at 600 characters (`max_text`).
- **Only checked fields are passed on.** Accepted findings and actions keep `text` and
  `citations`; conflicts keep `detail` and `evidence`. Extra keys a model adds are dropped.

## Limits

- It checks grounding, not truth. A finding can cite E1 and still misread E1. Keep a person in
  the review step for anything that matters.
- It does not discover conflicts. The conflict rules come from you or your domain experts.
- The draft shape is fixed: `findings`, `actions` and `conflicts`. Map other shapes first.

## Where it comes from

It is extracted from [Campus Evidence Desk](../../challenges/global-smart-campus-2026/), where
it checks model drafts before a reviewer sees them. The tests confirm it accepts exactly the
same items as that project's gate on all 25 of its recorded drafts. They also cover the cases
where this version is stricter: rows over the limit, citation lists over the cap, repeated IDs
in a conflict, and invisible characters.

```bash
python -m unittest -v examples.evidence_gate.test_evidence_gate
```

19 tests. Each rule was also checked by putting the bug back and confirming a test fails
(12 of 12 caught).

License: Apache-2.0, like the rest of this repository.
