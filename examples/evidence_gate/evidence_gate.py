"""Evidence Gate: keep only the parts of an LLM draft that cite evidence you supplied.

A deterministic acceptance layer for model output. A finding or action survives only if
every citation names a supplied evidence ID; a claimed conflict survives only if its two
evidence IDs form a pair you declared as a real conflict. Everything else is rejected with
a reason and never silently dropped. The gate checks grounding, not truth: a person still
reviews what passes.

Standard library only (Python 3.9+). Extracted from Campus Evidence Desk
(challenges/global-smart-campus-2026) and tested against its 25 recorded drafts.

    python evidence_gate.py draft.json --evidence E1 E2 E3 --conflict E1,E2

Exit codes: 0 everything accepted, 1 something rejected, 2 unreadable input.
"""
from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, Iterable, List, Optional, Set

CLAIM_SECTIONS = ("findings", "actions")
CONFLICTS = "conflicts"
SECTIONS = CLAIM_SECTIONS + (CONFLICTS,)
DEFAULT_LIMIT = 50
EXIT_OK, EXIT_REJECTED, EXIT_USAGE = 0, 1, 2

NOT_AN_OBJECT = "not_an_object"
NOT_A_LIST = "not_a_list"
OVER_LIMIT = "over_limit"
EMPTY_TEXT = "empty_text"
NO_CITATION = "no_citation"
TOO_MANY_CITATIONS = "too_many_citations"
UNKNOWN_EVIDENCE = "unknown_evidence"
CONFLICT_NEEDS_TWO_IDS = "conflict_needs_two_ids"
UNSUPPORTED_CONFLICT = "unsupported_conflict"


@dataclass
class GateResult:
    accepted: Dict[str, List[Dict[str, Any]]]
    rejected: List[Dict[str, Any]]
    missed_conflicts: List[List[str]]

    @property
    def ok(self) -> bool:
        """True when nothing in the draft was rejected."""
        return not self.rejected

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "accepted": self.accepted,
            "rejected": self.rejected,
            "invalid_citations": sorted({c for row in self.rejected for c in row.get("invalid_citations", [])}),
            "missed_conflicts": self.missed_conflicts,
            "counts": {"accepted": sum(len(rows) for rows in self.accepted.values()), "rejected": len(self.rejected)},
        }


def clean_text(value: Any, max_chars: int = 600) -> str:
    """Collapse whitespace, remove control and invisible format characters, and cap the length."""
    if not isinstance(value, str):
        return ""
    visible = "".join(ch for ch in value if ch.isspace() or unicodedata.category(ch) not in ("Cc", "Cf"))
    return " ".join(visible.split())[:max_chars]


def _ids(value: Any) -> Optional[List[str]]:
    """Citation IDs as unique strings in their original order; None when the field is not a list."""
    if not isinstance(value, list):
        return None
    unique: Dict[str, None] = {}
    for item in value:
        text = str(item).strip()
        if text:
            unique.setdefault(text, None)
    return list(unique)


def _evidence_ids(evidence: Iterable[Any]) -> FrozenSet[str]:
    ids: Set[str] = set()
    for item in evidence:
        raw = item.get("id") if isinstance(item, dict) else item
        text = "" if raw is None else str(raw).strip()
        if not text:
            raise ValueError("every evidence item needs a non-empty id")
        ids.add(text)
    return frozenset(ids)


def _conflict_rules(conflicts: Optional[Iterable[Iterable[Any]]], known: FrozenSet[str]) -> Set[FrozenSet[str]]:
    rules: Set[FrozenSet[str]] = set()
    for pair in conflicts or ():
        ids = None if isinstance(pair, (str, bytes)) else _ids(list(pair))
        if not ids or len(ids) != 2:
            raise ValueError(f"a conflict rule needs two different evidence IDs, got {pair!r}")
        unknown = [i for i in ids if i not in known]
        if unknown:
            raise ValueError(f"conflict rule {pair!r} names evidence that was not supplied: {unknown}")
        rules.add(frozenset(ids))
    return rules


def _judge(row: Any, section: str, known: FrozenSet[str], rules: Set[FrozenSet[str]],
           max_text: int, max_citations: int) -> Dict[str, Any]:
    """Return {"item": accepted item} or {"reason": ..., maybe "invalid_citations": [...]}."""
    if not isinstance(row, dict):
        return {"reason": NOT_AN_OBJECT}
    text_key, ids_key = ("detail", "evidence") if section == CONFLICTS else ("text", "citations")
    text = clean_text(row.get(text_key), max_text)
    if not text:
        return {"reason": EMPTY_TEXT}
    ids = _ids(row.get(ids_key))
    if not ids:
        return {"reason": NO_CITATION}
    if len(ids) > max_citations:
        return {"reason": TOO_MANY_CITATIONS}
    invalid = [i for i in ids if i not in known]
    if invalid:
        return {"reason": UNKNOWN_EVIDENCE, "invalid_citations": invalid}
    if section != CONFLICTS:
        return {"item": {"text": text, "citations": ids}}
    if len(ids) != 2:
        return {"reason": CONFLICT_NEEDS_TWO_IDS}
    if frozenset(ids) not in rules:
        return {"reason": UNSUPPORTED_CONFLICT}
    return {"item": {"detail": text, "evidence": sorted(ids)}}


def check(draft: Any, evidence: Iterable[Any], *, conflicts: Optional[Iterable[Iterable[Any]]] = None,
          limits: Optional[Dict[str, int]] = None, max_text: int = 600, max_citations: int = 6) -> GateResult:
    """Gate a draft of the form {"findings": [...], "actions": [...], "conflicts": [...]}.

    ``evidence`` is the supplied evidence: IDs, or objects with an "id".  ``conflicts`` lists
    the ID pairs your evidence really supports as conflicts; with none, every claimed conflict
    is rejected.  ``limits`` caps rows per section (default 50); extra rows are rejected.
    """
    known = _evidence_ids(evidence)
    rules = _conflict_rules(conflicts, known)
    caps = {section: DEFAULT_LIMIT for section in SECTIONS}
    caps.update(limits or {})
    accepted: Dict[str, List[Dict[str, Any]]] = {section: [] for section in SECTIONS}
    rejected: List[Dict[str, Any]] = []

    if not isinstance(draft, dict):
        rejected.append({"section": "draft", "index": 0, "reason": NOT_AN_OBJECT})
    else:
        for section in SECTIONS:
            rows = draft.get(section)
            if rows is None:
                continue
            if not isinstance(rows, list):
                rejected.append({"section": section, "index": 0, "reason": NOT_A_LIST})
                continue
            for index, row in enumerate(rows):
                verdict = {"reason": OVER_LIMIT} if index >= caps[section] else _judge(
                    row, section, known, rules, max_text, max_citations)
                if "item" in verdict:
                    accepted[section].append(verdict["item"])
                else:
                    rejected.append({"section": section, "index": index, **verdict})

    reported = {frozenset(item["evidence"]) for item in accepted[CONFLICTS]}
    missed = sorted(sorted(pair) for pair in rules - reported)
    return GateResult(accepted=accepted, rejected=rejected, missed_conflicts=missed)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Keep only the parts of an LLM draft that cite supplied evidence.")
    parser.add_argument("draft", help="JSON file with findings, actions and conflicts ('-' reads standard input)")
    parser.add_argument("--evidence", nargs="+", required=True, metavar="ID", help="evidence IDs the draft may cite")
    parser.add_argument("--conflict", action="append", default=[], metavar="ID,ID",
                        help="two evidence IDs that really conflict (repeat for more pairs)")
    args = parser.parse_args(argv)
    try:
        if args.draft == "-":
            text = sys.stdin.read()
        else:
            with open(args.draft, encoding="utf-8") as handle:
                text = handle.read()
        result = check(json.loads(text), args.evidence, conflicts=[pair.split(",") for pair in args.conflict])
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_USAGE
    print(json.dumps(result.to_dict(), indent=2))
    return EXIT_OK if result.ok else EXIT_REJECTED


if __name__ == "__main__":
    raise SystemExit(main())
