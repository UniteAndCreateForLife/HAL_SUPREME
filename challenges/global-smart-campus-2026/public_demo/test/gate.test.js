'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');

const gate = require('../public/gate.js');
const {scenarioFixtures} = require('../parity/export_fixtures.js');

const ROOT = path.join(__dirname, '..');
const readJson = rel => JSON.parse(fs.readFileSync(path.join(ROOT, rel), 'utf8'));
const fixtures = readJson('parity/gate_fixtures.json');
const expected = readJson('parity/gate_expected.json');
const caseById = id => gate.CASES.find(c => c.id === id);
const withoutRejected = ({rejected, ...rest}) => rest;

test('embedded cases match the canonical mvp/cases.json', () => {
  assert.deepEqual(gate.CASES, readJson('../mvp/cases.json').cases);
});

test('committed fixtures contain exactly the current demo scenarios', () => {
  const committed = fixtures.filter(f => f.name.startsWith('scenario:'));
  assert.deepEqual(committed, JSON.parse(JSON.stringify(scenarioFixtures())));
});

test('analyzeCase matches the Python engine for every case', () => {
  for (const c of gate.CASES) {
    assert.deepEqual(gate.analyzeCase(c), expected.reports[c.id], c.id);
  }
});

test('normalizeSynthesis matches the Python acceptance layer on every fixture', () => {
  assert.equal(fixtures.length, expected.normalized.length);
  fixtures.forEach((f, i) => {
    const want = expected.normalized[i];
    assert.equal(want.name, f.name);
    const got = gate.normalizeSynthesis(caseById(f.case_id), f.payload);
    assert.deepEqual(withoutRejected(got), want.result, `${f.case_id} ${f.name}`);
    assert.equal(got.rejected.length, want.result.acceptance.rejected_items, `${f.name} rejected list`);
  });
});

test('the demo scenarios behave as their labels say', () => {
  for (const c of gate.CASES) {
    const run = id => gate.normalizeSynthesis(c, gate.SCENARIOS.find(s => s.id === id).build(c));
    const grounded = run('grounded');
    assert.equal(grounded.acceptance.rejected_items, 0, c.id);
    assert.equal(grounded.acceptance.model_conflict_detection, true, c.id);

    const uncited = run('uncited');
    assert.equal(uncited.findings.length, 1);
    assert.deepEqual(uncited.rejected.map(r => r.reason), ['missing_or_invalid_citation']);

    const invented = run('invented_id');
    assert.equal(invented.acceptance.accepted_items, 0);
    assert.deepEqual(invented.acceptance.invalid_citations, ['E9']);

    const conflict = run('invented_conflict');
    assert.equal(conflict.conflicts.length, 0);
    assert.equal(conflict.acceptance.unsupported_conflict_relations_rejected, 1);

    const malformed = run('malformed');
    assert.equal(malformed.acceptance.accepted_items, 0);
    assert.deepEqual(malformed.rejected.map(r => r.reason), ['wrong_shape', 'missing_or_invalid_citation']);
  }
});

test('only own payload keys are read, like Python dict.get', () => {
  const c = gate.CASES[0];
  // Simulate a polluted prototype: inherited keys must not become model output.
  Object.prototype.findings = [{text: 'polluted', citations: ['E1']}];
  Object.prototype.text = 'polluted';
  try {
    assert.equal(gate.normalizeSynthesis(c, {}).acceptance.accepted_items, 0);
    const row = gate.normalizeSynthesis(c, {findings: [{citations: ['E1']}]});
    assert.equal(row.findings.length, 0);
  } finally {
    delete Object.prototype.findings;
    delete Object.prototype.text;
  }
  const payload = JSON.parse('{"findings":[{"__proto__":{"text":"x"},"citations":["E1"]}]}');
  assert.equal(gate.normalizeSynthesis(c, payload).acceptance.rejected_items, 1);
  assert.equal(gate.normalizeSynthesis(c, 'not an object').acceptance.accepted_items, 0);
});
