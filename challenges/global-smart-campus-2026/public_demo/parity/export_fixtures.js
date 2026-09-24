// Writes parity/gate_fixtures.json: every demo scenario for every case, plus edge cases.
// Then run: python parity/generate_expected.py   (from public_demo/)
'use strict';
const fs = require('fs');
const path = require('path');
const {CASES, SCENARIOS} = require('../public/gate.js');

const EDGE_CASES = [
  {name: 'unicode_whitespace', case_id: 'policy-conflict', payload: {
    summary: '  Approve\tthe\n request — café  naïve ',
    findings: [{text: ' Memo A  requires approval ', citations: [' E1 ']}], actions: [], conflicts: []}},
  {name: 'limits', case_id: 'research-access', payload: {
    findings: Array.from({length: 10}, (_, i) => ({text: `Finding ${i}`, citations: ['E1']})),
    actions: Array.from({length: 8}, (_, i) => ({text: `Action ${i}`, citations: ['E2']})), conflicts: []}},
  {name: 'duplicate_conflict_ids', case_id: 'policy-conflict', payload: {
    findings: [], actions: [], conflicts: [{detail: 'duplicate ids', evidence: ['E1', 'E1', 'E2']}]}},
  {name: 'reversed_conflict_pair', case_id: 'policy-conflict', payload: {
    findings: [], actions: [], conflicts: [{detail: 'reversed', evidence: ['E2', 'E1']}]}},
  {name: 'non_string_citations', case_id: 'energy-anomaly', payload: {
    findings: [{text: 'numeric', citations: [1, 'E1']}, {text: 'boolean', citations: [true]},
      {text: 'null', citations: [null]}, {text: 'string, not a list', citations: 'E1'}], actions: [], conflicts: []}},
  {name: 'too_many_citations', case_id: 'energy-anomaly', payload: {
    findings: [{text: 'many citations', citations: ['E1', 'E2', 'E3', 'E4', 'E1', 'E2', 'E3']}], actions: [], conflicts: []}},
  {name: 'long_text', case_id: 'research-access', payload: {
    summary: 's'.repeat(1000), findings: [{text: 'x'.repeat(700), citations: ['E1']}], uncertainty: 'u'.repeat(800),
    actions: [], conflicts: []}},
  {name: 'missing_sections', case_id: 'research-access', payload: {}},
  {name: 'wrong_keys', case_id: 'policy-conflict', payload: {
    findings: [{detail: 'wrong key', evidence: ['E1']}], conflicts: [{text: 'wrong key', citations: ['E1', 'E2']}]}},
  {name: 'emoji_and_control', case_id: 'policy-conflict', payload: {
    findings: [{text: 'Safe 👍 approval\u001cnow', citations: ['E3']}], actions: [], conflicts: []}}
];

function scenarioFixtures() {
  return CASES.flatMap(c => SCENARIOS.map(s => ({name: `scenario:${s.id}`, case_id: c.id, payload: s.build(c)})));
}

function allFixtures() {
  return [...scenarioFixtures(), ...EDGE_CASES];
}

if (require.main === module) {
  const out = path.join(__dirname, 'gate_fixtures.json');
  fs.writeFileSync(out, JSON.stringify(allFixtures(), null, 1) + '\n', 'utf8');
  console.log(`wrote ${allFixtures().length} fixtures to ${path.basename(out)}`);
}

module.exports = {allFixtures, scenarioFixtures, EDGE_CASES};
