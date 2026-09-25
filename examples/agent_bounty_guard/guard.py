"""Agent Bounty Guard.

Flags bounty repositories and issues that try to extract an AI agent's session
context (system prompt, startup instructions, local paths, token budget) or that
hide instructions aimed at automated contributors.

Read-only and standard-library only:

    python -m examples.agent_bounty_guard.guard OWNER/REPO [--issue N ...] [--json]
    python -m examples.agent_bounty_guard.guard --file CONTRIBUTING.md [--json]

Exit codes: 0 ok, 1 warn, 2 block, 3 nothing could be scanned.

The rules look for what is being requested (reproduce the context your session
started with) rather than for specific field names, because live examples rotate
names such as boot_context, pre_task_context, session_init and initial_directives.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable, Iterator

OK, WARN, BLOCK = "ok", "warn", "block"
_RANK = {OK: 0, WARN: 1, BLOCK: 2}
_EXIT = {OK: 0, WARN: 1, BLOCK: 2}

REPO_DOCUMENTS = (
    "CONTRIBUTING.md",
    ".github/CONTRIBUTING.md",
    "docs/CONTRIBUTING.md",
    "AGENTS.md",
    "CLAUDE.md",
    ".github/copilot-instructions.md",
    ".github/pull_request_template.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
    "SECURITY.md",
    "README.md",
)


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: str
    source: str
    excerpt: str


_I = re.I

# A request to reproduce something.
_DISCLOSE = re.compile(
    r"\b(?:paste|copy|include|insert|provide|output|print|reproduce|dump|share|reveal|disclose|"
    r"transcribe|write\s+out|record|attach|submit|list|contain(?:s|ing)?)\b",
    _I,
)
_NEGATION = re.compile(r"\b(?:do\s+not|don'?t|never|avoid|must\s+not|should\s+not|shouldn'?t|without)\b", _I)
_SECOND_PERSON = re.compile(r"\b(?:your|you)\b", _I)

# Where an agent's hidden context lives.
_SESSION_ANCHOR = re.compile(
    r"(?:(?:start|beginning)\s+of\s+(?:your|the|this)\s+(?:session|conversation|context|chat|run)"
    r"|session\s+(?:start|startup|initiali[sz]ation)"
    r"|at\s+startup"
    r"|before\s+(?:the\s+|any\s+)?(?:first\s+)?(?:human|user)\s+(?:message|turn)s?"
    r"|(?:loaded|injected)\s+into\s+your\s+(?:session|context)"
    r"|appeared\s+in\s+your\s+context"
    r"|instructions\s+(?:you\s+)?received"
    r"|before\s+(?:the\s+|your\s+)?task\s+(?:started|starts|began|begins|assignment)"
    r"|(?:first|initial|opening)\s+message\s+(?:in|of)\s+(?:your|the|this)\s+(?:conversation|session|chat|context)"
    r"|\bpre-?(?:conversation|session|task)\b"
    r"|your\s+(?:platform|runtime|harness|framework|environment)\s+(?:provided|loaded|injected|supplied|gave\s+you))",
    _I,
)

# Phrases specific enough to block on their own, e.g. in a table with no verb.
_CONTEXT_PHRASES = re.compile(
    r"(?:session\s+initiali[sz]ation\s+(?:text|payload|prompt)"
    r"|instructions\s+received\s+at\s+(?:the\s+)?(?:start|beginning)\s+of"
    r"|everything\s+(?:that\s+)?appeared\s+in\s+your\s+context"
    r"|full\s+text\s+of\s+(?:all\s+)?(?:your\s+)?instructions)",
    _I,
)

# "your full system prompt", "the agent's hidden instructions", "your configuration prompt".
_PROMPT_OBJECT = re.compile(
    r"\b(?:your|the\s+agent'?s|the\s+model'?s|the\s+contributor'?s)\s+"
    r"(?:(?:full|complete|entire|exact|original|current)\s+)*"
    r"(?:system|configuration|config|initial|setup|startup|boot|operating|developer|custom|hidden)\s+"
    r"(?:prompt|instructions|message|directives)",
    _I,
)

# Verbs that ask the reader to copy text verbatim, and what an agent's hidden context is made of.
_STRONG_DISCLOSE = re.compile(r"\b(?:paste|copy|reproduce|transcribe|dump)\b", _I)
_CONTEXT_OBJECT = re.compile(
    r"\b(?:prompts?|instructions?|context|configuration|config|rules|directives|guidelines|text\s+block|"
    r"everything|what\s+you\s+were\s+(?:told|given))\b",
    _I,
)
# "everything injected before the first human message": exhaustive, even without "your".
_EXHAUSTIVE = re.compile(
    r"\b(?:everything|verbatim|all\s+(?:of\s+)?(?:the\s+)?(?:instructions|context|text|rules)"
    r"|(?:complete|entire|full)\s+(?:text|set|context|contents))\b",
    _I,
)

# The request is about something the contributor must submit.
_SUBMISSION = re.compile(
    r"\b(?:pr|pull\s+requests?|submissions?|commits?|metadata|description|changes|files?|json|ya?ml|"
    r"schema|field|artifact)\b",
    _I,
)

# A fill-in template such as "<paste ... >".
_PLACEHOLDER = re.compile(r"<[^<>]{0,40}\b(?:paste|copy|insert|include)\b[^<>]{0,400}>", _I)

_ENVIRONMENT = re.compile(
    r"(?:home\s+director(?:y|ies)|homedir"
    r"|absolute\s+path\s+(?:to|of)\s+(?:the\s+|your\s+)?(?:current\s+)?working\s+directory"
    r"|tokens?\s+(?:used|remaining|left)|remaining\s+(?:tokens|budget|context)|compute\s+budget)",
    _I,
)

_NON_PAYING = re.compile(
    r"(?:bount(?:y|ies)\s+(?:listed\s+here\s+)?are\s+symbolic|research\s+purposes\s+only|academic\s+study"
    r"|will\s+not\s+be\s+merged|not\s+the\s+right\s+repo|no\s+(?:real\s+)?payment|(?:are|is)\s+not\s+paid)",
    _I,
)

_HTML_COMMENT = re.compile(r"<!--(.*?)-->", re.S)
_AGENT_WORDS = re.compile(r"\b(?:ai|agents?|automated|autonomous|bots?|llms?|assistants?|automation)\b", _I)
_SUPPRESS = re.compile(
    r"\b(?:ignore|disregard|skip|bypass)\b[^.]{0,80}\b(?:notice|warning|above|instructions|guidelines|disclaimer)\b",
    _I,
)
_ENCOURAGE = re.compile(
    r"(?:\bwelcome\b|\bencouraged\b|will\s+be\s+processed|optimi[sz]ed\s+for\s+(?:automated|ai|agent)"
    r"|should\s+proceed|and\s+proceed|contributions\s+from\s+ai)",
    _I,
)
# Unicode "tag" characters can smuggle invisible ASCII text to language models.
_TAG_RUN = re.compile("[\U000E0020-\U000E007F]{8,}")
_ZERO_WIDTH = re.compile("[​‌⁠᠎]")


def _excerpt(text: str, start: int, end: int, width: int = 160) -> str:
    pad = max(0, (width - (end - start)) // 2)
    snippet = " ".join(text[max(0, start - pad): end + pad].split())
    return snippet if len(snippet) <= width else snippet[: width - 3] + "..."


def _lines(text: str) -> Iterator[tuple[int, str]]:
    offset = 0
    for line in text.splitlines(keepends=True):
        yield offset, line
        offset += len(line)


# A sentence ends at . ! or ? followed by whitespace and a character that is not a
# lowercase letter, so "e.g. the" and "i.e. your" do not split a sentence.
_SENTENCE_BREAK = re.compile(r"(?<=[.!?])(?<!e\.g\.)(?<!i\.e\.)(?<!etc\.)(?<!vs\.)\s+(?=[^a-z])")


def _sentences(line: str) -> Iterator[tuple[int, str]]:
    start = 0
    for m in _SENTENCE_BREAK.finditer(line):
        yield start, line[start:m.start()]
        start = m.end()
    yield start, line[start:]


def _requested(line: str) -> bool:
    """True when the line contains a disclosure verb that is not negated just before it."""
    for verb in _DISCLOSE.finditer(line):
        if not _NEGATION.search(line[max(0, verb.start() - 30): verb.start()]):
            return True
    return False


def scan_text(text: str, source: str) -> list[Finding]:
    findings: list[Finding] = []
    seen: set[tuple[str, str]] = set()

    def add(rule: str, severity: str, start: int, end: int, excerpt: str | None = None) -> None:
        shown = excerpt if excerpt is not None else _excerpt(text, start, end)
        if (rule, shown) not in seen:
            seen.add((rule, shown))
            findings.append(Finding(rule, severity, source, shown))

    for m in _CONTEXT_PHRASES.finditer(text):
        add("session_context_request", BLOCK, m.start(), m.end())

    for m in _PLACEHOLDER.finditer(text):
        body = m.group(0)
        if _SESSION_ANCHOR.search(body) or _PROMPT_OBJECT.search(body):
            add("session_context_request", BLOCK, m.start(), m.end())

    for offset, line in _lines(text):
        # Where the request is headed (a PR, a file) may be named anywhere on the line,
        # but the request itself and what it asks for must share one sentence.
        submission = _SUBMISSION.search(line)
        table_row = line.lstrip().startswith("|")
        for start, sentence in _sentences(line):
            base = offset + start
            requested = _requested(sentence)
            anchor = _SESSION_ANCHOR.search(sentence) if requested else None
            if anchor:
                verbatim = _STRONG_DISCLOSE.search(sentence) and _CONTEXT_OBJECT.search(sentence)
                addressed = _SECOND_PERSON.search(sentence) and (submission or verbatim)
                exhaustive = submission and _EXHAUSTIVE.search(sentence)
                if addressed or exhaustive:
                    add("session_context_request", BLOCK, base + anchor.start(), base + anchor.end())
            if requested and submission:
                prompt = _PROMPT_OBJECT.search(sentence)
                if prompt:
                    add("system_prompt_request", BLOCK, base + prompt.start(), base + prompt.end())
            env = _ENVIRONMENT.search(sentence)
            if env and not _NEGATION.search(sentence[max(0, env.start() - 30): env.start()]):
                if table_row or _PLACEHOLDER.search(line) or (requested and _SECOND_PERSON.search(sentence)):
                    add("environment_disclosure_request", WARN, base + env.start(), base + env.end())

    for m in _HTML_COMMENT.finditer(text):
        body = m.group(1)
        if not _AGENT_WORDS.search(body):
            continue
        if _SUPPRESS.search(body):
            add("hidden_notice_suppression", BLOCK, m.start(), m.end())
        elif _ENCOURAGE.search(body):
            add("hidden_agent_directive", WARN, m.start(), m.end())

    for m in _TAG_RUN.finditer(text):
        hidden = "".join(chr(ord(ch) - 0xE0000) for ch in m.group(0))
        severity = BLOCK if (_AGENT_WORDS.search(hidden) or _DISCLOSE.search(hidden)) else WARN
        add("hidden_unicode_text", severity, m.start(), m.end(), excerpt="decoded: " + " ".join(hidden.split())[:150])

    zero_width = _ZERO_WIDTH.findall(text)
    if len(zero_width) >= 3:
        first = _ZERO_WIDTH.search(text)
        add("invisible_characters", WARN, first.start(), first.end(), excerpt=f"{len(zero_width)} zero-width characters")

    for m in _NON_PAYING.finditer(text):
        add("non_paying_notice", WARN, m.start(), m.end())

    return findings


def verdict(findings: Iterable[Finding]) -> str:
    return max((f.severity for f in findings), key=_RANK.__getitem__, default=OK)


def scan_documents(documents: dict[str, str]) -> dict:
    findings = [f for source, text in documents.items() for f in scan_text(text, source)]
    return {
        "schema": "agent-bounty-guard.v1",
        "verdict": verdict(findings),
        "documents_scanned": sorted(documents),
        "findings": [asdict(f) for f in findings],
    }


Getter = Callable[..., "str | None"]


def http_get(url: str, *, token: str | None = None, timeout: float = 20.0, attempts: int = 3) -> str | None:
    """GET a URL; 404 means "no such document". Transient network failures are retried."""
    headers = {"User-Agent": "agent-bounty-guard (read-only)"}
    if token and url.startswith("https://api.github.com/"):
        headers["Authorization"] = f"Bearer {token}"
        headers["Accept"] = "application/vnd.github+json"
    request = urllib.request.Request(url, headers=headers)
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read(2_000_000).decode("utf-8", "replace")
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            raise
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt == attempts - 1:
                raise
            time.sleep(1.5 * (attempt + 1))
    return None


def fetch_repository_documents(
    repo: str, *, issues: Iterable[int] = (), token: str | None = None, get: Getter = http_get
) -> dict[str, str]:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        raise ValueError(f"expected OWNER/REPO, got {repo!r}")
    documents: dict[str, str] = {}
    for path in REPO_DOCUMENTS:
        text = get(f"https://raw.githubusercontent.com/{repo}/HEAD/{path}")
        if text:
            documents[f"{repo}:{path}"] = text
    for number in issues:
        raw = get(f"https://api.github.com/repos/{repo}/issues/{int(number)}", token=token)
        if raw:
            issue = json.loads(raw)
            documents[f"{repo}#{int(number)}"] = f"{issue.get('title') or ''}\n\n{issue.get('body') or ''}"
    return documents


def render(report: dict) -> str:
    findings = report["findings"]
    lines = [
        f"VERDICT: {report['verdict'].upper()} "
        f"({len(findings)} findings in {len(report['documents_scanned'])} documents scanned)"
    ]
    for f in sorted(findings, key=lambda f: -_RANK[f["severity"]]):
        lines.append(f"- [{f['severity']}] {f['rule']} in {f['source']}: {f['excerpt']}")
    if report["verdict"] == BLOCK:
        lines.append("Do not let an autonomous agent work on this target, and never paste session context into any artifact.")
    return "\n".join(lines)


def _emit(text: str) -> None:
    encoding = sys.stdout.encoding or "utf-8"
    sys.stdout.write(text.encode(encoding, "replace").decode(encoding) + "\n")


def main(argv: list[str] | None = None, *, get: Getter = http_get) -> int:
    parser = argparse.ArgumentParser(description="Flag bounty targets that try to extract AI agent context.")
    parser.add_argument("repo", nargs="?", help="GitHub repository as OWNER/REPO")
    parser.add_argument("--issue", type=int, action="append", default=[], help="issue number to scan (repeatable)")
    parser.add_argument("--file", action="append", default=[], help="local file to scan (repeatable)")
    parser.add_argument("--json", action="store_true", help="print the machine-readable report")
    args = parser.parse_args(argv)
    if not args.repo and not args.file:
        parser.error("give OWNER/REPO or --file")

    documents = {name: Path(name).read_text(encoding="utf-8", errors="replace") for name in args.file}
    if args.repo:
        try:
            documents.update(
                fetch_repository_documents(
                    args.repo, issues=args.issue, token=os.environ.get("GITHUB_TOKEN") or None, get=get
                )
            )
        except (urllib.error.URLError, ValueError, json.JSONDecodeError) as exc:
            print(f"agent-bounty-guard: could not fetch {args.repo}: {exc}", file=sys.stderr)
    if not documents:
        print("agent-bounty-guard: nothing could be scanned", file=sys.stderr)
        return 3

    report = scan_documents(documents)
    _emit(json.dumps(report, indent=2) if args.json else render(report))
    return _EXIT[report["verdict"]]


if __name__ == "__main__":
    raise SystemExit(main())
