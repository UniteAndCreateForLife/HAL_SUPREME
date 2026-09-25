/* Agent Bounty Guard, JavaScript port.
 *
 * Mirrors examples/agent_bounty_guard/guard.py (scan_text, verdict, scan_documents and
 * repository fetching) so the detector can run in a browser or in Node without Python.
 * test/guard.test.js holds it to parity/expected.json, generated from the Python
 * reference by parity/generate_expected.py.
 *
 * Positions are counted in Unicode code points and whitespace follows Python's
 * definition, so excerpts match the Python output exactly. Known difference: Python's
 * \b and \w treat non-ASCII letters as word characters and JavaScript's do not, so a
 * keyword glued to a non-ASCII letter can match in one and not the other.
 */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.AgentBountyGuard = api;
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  const OK = 'ok', WARN = 'warn', BLOCK = 'block';
  const RANK = {ok: 0, warn: 1, block: 2};

  const REPO_DOCUMENTS = [
    'CONTRIBUTING.md', '.github/CONTRIBUTING.md', 'docs/CONTRIBUTING.md', 'AGENTS.md', 'CLAUDE.md',
    '.github/copilot-instructions.md', '.github/pull_request_template.md', '.github/PULL_REQUEST_TEMPLATE.md',
    'SECURITY.md', 'README.md'
  ];

  // Python's str.isspace() set, used wherever the Python patterns say \s.
  const WS = '\\t\\n\\x0b\\x0c\\r\\x1c-\\x1f \\x85\\xa0\\u1680\\u2000-\\u200a\\u2028\\u2029\\u202f\\u205f\\u3000';
  const re = (source, flags = 'i') => new RegExp(source.replace(/\\s/g, `[${WS}]`), flags);

  const DISCLOSE = re(String.raw`\b(?:paste|copy|include|insert|provide|output|print|reproduce|dump|share|reveal|disclose|transcribe|write\s+out|record|attach|submit|list|contain(?:s|ing)?)\b`, 'gi');
  const NEGATION = re(String.raw`\b(?:do\s+not|don'?t|never|avoid|must\s+not|should\s+not|shouldn'?t|without)\b`);
  const SECOND_PERSON = re(String.raw`\b(?:your|you)\b`);
  const SESSION_ANCHOR = re(String.raw`(?:(?:start|beginning)\s+of\s+(?:your|the|this)\s+(?:session|conversation|context|chat|run)` +
    String.raw`|session\s+(?:start|startup|initiali[sz]ation)` +
    String.raw`|at\s+startup` +
    String.raw`|before\s+(?:the\s+|any\s+)?(?:first\s+)?(?:human|user)\s+(?:message|turn)s?` +
    String.raw`|(?:loaded|injected)\s+into\s+your\s+(?:session|context)` +
    String.raw`|appeared\s+in\s+your\s+context` +
    String.raw`|instructions\s+(?:you\s+)?received` +
    String.raw`|before\s+(?:the\s+|your\s+)?task\s+(?:started|starts|began|begins|assignment)` +
    String.raw`|(?:first|initial|opening)\s+message\s+(?:in|of)\s+(?:your|the|this)\s+(?:conversation|session|chat|context)` +
    String.raw`|\bpre-?(?:conversation|session|task)\b` +
    String.raw`|your\s+(?:platform|runtime|harness|framework|environment)\s+(?:provided|loaded|injected|supplied|gave\s+you))`);
  const CONTEXT_PHRASES = re(String.raw`(?:session\s+initiali[sz]ation\s+(?:text|payload|prompt)` +
    String.raw`|instructions\s+received\s+at\s+(?:the\s+)?(?:start|beginning)\s+of` +
    String.raw`|everything\s+(?:that\s+)?appeared\s+in\s+your\s+context` +
    String.raw`|full\s+text\s+of\s+(?:all\s+)?(?:your\s+)?instructions)`, 'gi');
  const PROMPT_OBJECT = re(String.raw`\b(?:your|the\s+agent'?s|the\s+model'?s|the\s+contributor'?s)\s+` +
    String.raw`(?:(?:full|complete|entire|exact|original|current)\s+)*` +
    String.raw`(?:system|configuration|config|initial|setup|startup|boot|operating|developer|custom|hidden)\s+` +
    String.raw`(?:prompt|instructions|message|directives)`);
  const STRONG_DISCLOSE = re(String.raw`\b(?:paste|copy|reproduce|transcribe|dump)\b`);
  const CONTEXT_OBJECT = re(String.raw`\b(?:prompts?|instructions?|context|configuration|config|rules|directives|guidelines|text\s+block|everything|what\s+you\s+were\s+(?:told|given))\b`);
  const EXHAUSTIVE = re(String.raw`\b(?:everything|verbatim|all\s+(?:of\s+)?(?:the\s+)?(?:instructions|context|text|rules)|(?:complete|entire|full)\s+(?:text|set|context|contents))\b`);
  const SUBMISSION = re(String.raw`\b(?:pr|pull\s+requests?|submissions?|commits?|metadata|description|changes|files?|json|ya?ml|schema|field|artifact)\b`);
  const PLACEHOLDER_SRC = String.raw`<[^<>]{0,40}\b(?:paste|copy|insert|include)\b[^<>]{0,400}>`;
  const PLACEHOLDER = re(PLACEHOLDER_SRC, 'gi');
  const PLACEHOLDER_ONE = re(PLACEHOLDER_SRC, 'i');
  const ENVIRONMENT = re(String.raw`(?:home\s+director(?:y|ies)|homedir|absolute\s+path\s+(?:to|of)\s+(?:the\s+|your\s+)?(?:current\s+)?working\s+directory|tokens?\s+(?:used|remaining|left)|remaining\s+(?:tokens|budget|context)|compute\s+budget)`);
  const NON_PAYING = re(String.raw`(?:bount(?:y|ies)\s+(?:listed\s+here\s+)?are\s+symbolic|research\s+purposes\s+only|academic\s+study|will\s+not\s+be\s+merged|not\s+the\s+right\s+repo|no\s+(?:real\s+)?payment|(?:are|is)\s+not\s+paid)`, 'gi');
  const HTML_COMMENT = /<!--([\s\S]*?)-->/g;
  const AGENT_WORDS = re(String.raw`\b(?:ai|agents?|automated|autonomous|bots?|llms?|assistants?|automation)\b`);
  const SUPPRESS = re(String.raw`\b(?:ignore|disregard|skip|bypass)\b[^.]{0,80}\b(?:notice|warning|above|instructions|guidelines|disclaimer)\b`);
  const ENCOURAGE = re(String.raw`(?:\bwelcome\b|\bencouraged\b|will\s+be\s+processed|optimi[sz]ed\s+for\s+(?:automated|ai|agent)|should\s+proceed|and\s+proceed|contributions\s+from\s+ai)`);
  const TAG_RUN = /[\u{E0020}-\u{E007F}]{8,}/gu;
  const ZERO_WIDTH = /[\u200b\u200c\u2060\u180e]/g;
  const SENTENCE_BREAK = re(String.raw`(?<=[.!?])(?<!e\.g\.)(?<!i\.e\.)(?<!etc\.)(?<!vs\.)\s+(?=[^a-z])`, 'g');
  const LINE_END = /\r\n|[\n\r\x0b\x0c\x1c\x1d\x1e\x85\u2028\u2029]/g;
  const WS_RUN = new RegExp(`[${WS}]+`);
  const WS_LEFT = new RegExp(`^[${WS}]+`);

  const collapse = s => s.split(WS_RUN).filter(Boolean).join(' ');

  // Code-point view of a string: Python indexes by code point, JavaScript by UTF-16 unit.
  function codePoints(str) {
    const cps = Array.from(str);
    const at = new Int32Array(str.length + 1);
    let u = 0;
    cps.forEach((ch, i) => { for (let k = 0; k < ch.length; k++) at[u++] = i; });
    at[str.length] = cps.length;
    return {cps, cp: u16 => at[u16]};
  }

  function* matchAll(regex, str) {
    regex.lastIndex = 0;
    let m;
    while ((m = regex.exec(str)) !== null) {
      yield m;
      if (m[0] === '') regex.lastIndex++;
    }
  }

  function* lines(text) {
    let start = 0;
    for (const m of matchAll(LINE_END, text)) {
      const end = m.index + m[0].length;
      yield [start, text.slice(start, end)];
      start = end;
    }
    if (start < text.length) yield [start, text.slice(start)];
  }

  function* sentences(line) {
    let start = 0;
    for (const m of matchAll(SENTENCE_BREAK, line)) {
      yield [start, line.slice(start, m.index)];
      start = m.index + m[0].length;
    }
    yield [start, line.slice(start)];
  }

  // True when a disclosure verb is not negated within the 30 code points before it.
  function requested(sentence) {
    const view = codePoints(sentence);
    for (const verb of matchAll(DISCLOSE, sentence)) {
      const v = view.cp(verb.index);
      if (!NEGATION.test(view.cps.slice(Math.max(0, v - 30), v).join(''))) return true;
    }
    return false;
  }

  function scanText(text, source) {
    const view = codePoints(text);
    const findings = [];
    const seen = new Set();

    function excerpt(u16Start, u16End, width = 160) {
      const start = view.cp(u16Start), end = view.cp(u16End);
      const pad = Math.max(0, Math.floor((width - (end - start)) / 2));
      const snippet = collapse(view.cps.slice(Math.max(0, start - pad), end + pad).join(''));
      const chars = Array.from(snippet);
      return chars.length <= width ? snippet : chars.slice(0, width - 3).join('') + '...';
    }
    function add(rule, severity, start, end, shown) {
      const text_ = shown !== undefined ? shown : excerpt(start, end);
      const key = rule + '\u0000' + text_;
      if (!seen.has(key)) {
        seen.add(key);
        findings.push({rule, severity, source, excerpt: text_});
      }
    }

    for (const m of matchAll(CONTEXT_PHRASES, text)) add('session_context_request', BLOCK, m.index, m.index + m[0].length);

    for (const m of matchAll(PLACEHOLDER, text)) {
      if (SESSION_ANCHOR.test(m[0]) || PROMPT_OBJECT.test(m[0])) add('session_context_request', BLOCK, m.index, m.index + m[0].length);
    }

    for (const [offset, line] of lines(text)) {
      const submission = SUBMISSION.test(line);
      const tableRow = line.replace(WS_LEFT, '').startsWith('|');
      for (const [start, sentence] of sentences(line)) {
        const base = offset + start;
        const isRequested = requested(sentence);
        const anchor = isRequested ? SESSION_ANCHOR.exec(sentence) : null;
        if (anchor) {
          const verbatim = STRONG_DISCLOSE.test(sentence) && CONTEXT_OBJECT.test(sentence);
          const addressed = SECOND_PERSON.test(sentence) && (submission || verbatim);
          const exhaustive = submission && EXHAUSTIVE.test(sentence);
          if (addressed || exhaustive) add('session_context_request', BLOCK, base + anchor.index, base + anchor.index + anchor[0].length);
        }
        if (isRequested && submission) {
          const prompt = PROMPT_OBJECT.exec(sentence);
          if (prompt) add('system_prompt_request', BLOCK, base + prompt.index, base + prompt.index + prompt[0].length);
        }
        const env = ENVIRONMENT.exec(sentence);
        if (env) {
          const sview = codePoints(sentence);
          const e = sview.cp(env.index);
          if (!NEGATION.test(sview.cps.slice(Math.max(0, e - 30), e).join(''))) {
            if (tableRow || PLACEHOLDER_ONE.test(line) || (isRequested && SECOND_PERSON.test(sentence))) {
              add('environment_disclosure_request', WARN, base + env.index, base + env.index + env[0].length);
            }
          }
        }
      }
    }

    for (const m of matchAll(HTML_COMMENT, text)) {
      const body = m[1];
      if (!AGENT_WORDS.test(body)) continue;
      if (SUPPRESS.test(body)) add('hidden_notice_suppression', BLOCK, m.index, m.index + m[0].length);
      else if (ENCOURAGE.test(body)) add('hidden_agent_directive', WARN, m.index, m.index + m[0].length);
    }

    for (const m of matchAll(TAG_RUN, text)) {
      const hidden = Array.from(m[0], ch => String.fromCodePoint(ch.codePointAt(0) - 0xE0000)).join('');
      DISCLOSE.lastIndex = 0;
      const severity = (AGENT_WORDS.test(hidden) || DISCLOSE.test(hidden)) ? BLOCK : WARN;
      DISCLOSE.lastIndex = 0;
      add('hidden_unicode_text', severity, m.index, m.index + m[0].length, 'decoded: ' + Array.from(collapse(hidden)).slice(0, 150).join(''));
    }

    const zeroWidth = text.match(ZERO_WIDTH) || [];
    if (zeroWidth.length >= 3) {
      const first = text.search(/[\u200b\u200c\u2060\u180e]/);
      add('invisible_characters', WARN, first, first + 1, `${zeroWidth.length} zero-width characters`);
    }

    for (const m of matchAll(NON_PAYING, text)) add('non_paying_notice', WARN, m.index, m.index + m[0].length);

    return findings;
  }

  function verdict(findings) {
    return findings.reduce((best, f) => (RANK[f.severity] > RANK[best] ? f.severity : best), OK);
  }

  function scanDocuments(documents) {
    const findings = Object.entries(documents).flatMap(([source, text]) => scanText(text, source));
    return {
      schema: 'agent-bounty-guard.v1',
      verdict: verdict(findings),
      documents_scanned: Object.keys(documents).sort(),
      findings
    };
  }

  async function fetchRepositoryDocuments(repo, {issues = [], fetchFn = fetch} = {}) {
    if (!/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(repo || '')) throw new Error(`expected OWNER/REPO, got ${JSON.stringify(repo)}`);
    const documents = {};
    for (const path of REPO_DOCUMENTS) {
      const r = await fetchFn(`https://raw.githubusercontent.com/${repo}/HEAD/${path}`);
      if (r.ok) documents[`${repo}:${path}`] = await r.text();
      else if (r.status !== 404) throw new Error(`GitHub returned ${r.status} for ${path}`);
    }
    for (const n of issues) {
      const r = await fetchFn(`https://api.github.com/repos/${repo}/issues/${Number(n)}`, {headers: {Accept: 'application/vnd.github+json'}});
      if (r.ok) {
        const issue = await r.json();
        documents[`${repo}#${Number(n)}`] = `${issue.title || ''}\n\n${issue.body || ''}`;
      } else if (r.status !== 404) {
        throw new Error(`GitHub returned ${r.status} for issue ${n}`);
      }
    }
    return documents;
  }

  return {OK, WARN, BLOCK, REPO_DOCUMENTS, scanText, verdict, scanDocuments, fetchRepositoryDocuments};
});
