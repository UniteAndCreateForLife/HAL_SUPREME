'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');

const guard = require('../guard.js');

const PARITY = path.join(__dirname, '..', 'parity');
const fixtures = JSON.parse(fs.readFileSync(path.join(PARITY, 'fixtures.json'), 'utf8'));
const expected = JSON.parse(fs.readFileSync(path.join(PARITY, 'expected.json'), 'utf8'));

test('every fixture produces exactly the Python findings and verdict', () => {
  assert.equal(fixtures.items.length, expected.items.length);
  fixtures.items.forEach((item, i) => {
    const want = expected.items[i];
    assert.equal(want.name, item.name);
    const got = guard.scanText(item.text, item.name);
    assert.deepEqual(got, want.findings, item.name);
    assert.equal(guard.verdict(got), want.verdict, item.name);
  });
});

test('scanDocuments matches the Python report shape and content', () => {
  assert.deepEqual(guard.scanDocuments(fixtures.documents), expected.documents_report);
});

test('the fixture set covers every rule the detector can raise', () => {
  const rules = new Set(expected.items.flatMap(item => item.findings.map(f => f.rule)));
  for (const rule of ['session_context_request', 'system_prompt_request', 'hidden_notice_suppression',
    'hidden_unicode_text', 'environment_disclosure_request', 'hidden_agent_directive',
    'invisible_characters', 'non_paying_notice']) {
    assert.ok(rules.has(rule), rule);
  }
});

test('repository fetching reads only public GitHub URLs, skips 404s and fails loudly otherwise', async () => {
  const seen = [];
  const reply = (status, body) => ({ok: status === 200, status, text: async () => body, json: async () => JSON.parse(body)});
  const fetchFn = async url => {
    seen.push(url);
    if (url === 'https://raw.githubusercontent.com/o/r/HEAD/CONTRIBUTING.md') return reply(200, 'Full session initialization text');
    if (url === 'https://api.github.com/repos/o/r/issues/7') return reply(200, JSON.stringify({title: 'T', body: 'B'}));
    return reply(404, '');
  };
  const docs = await guard.fetchRepositoryDocuments('o/r', {issues: [7], fetchFn});
  assert.deepEqual(Object.keys(docs).sort(), ['o/r#7', 'o/r:CONTRIBUTING.md']);
  assert.ok(seen.every(u => u.startsWith('https://raw.githubusercontent.com/o/r/') || u.startsWith('https://api.github.com/repos/o/r/')));
  await assert.rejects(guard.fetchRepositoryDocuments('not a repo', {fetchFn}));
  await assert.rejects(guard.fetchRepositoryDocuments('o/r', {fetchFn: async () => reply(403, '')}), /403/);
});
