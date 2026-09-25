/* HAL Campus Evidence Desk: the deterministic acceptance layer, running in the browser.
 *
 * Port of mvp/engine.py (analyze_case, validate_report) and mvp/live_model.py
 * (normalize_synthesis). test/gate.test.js checks this file against
 * parity/gate_expected.json, which parity/generate_expected.py produces from the
 * Python reference, so the two implementations cannot drift silently.
 *
 * Known difference: non-string citation values are coerced like Python's str() for
 * strings, integers, booleans and null only (a JSON float such as 1.0 prints as "1").
 */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.HALGate = api;
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  const CASES = [
    {id:'policy-conflict',title:'Conflicting policy guidance',question:'What should the department do before approving after-hours lab access?',evidence:[
      {id:'E1',type:'policy_memo',text:'Policy memo A requires department-chair approval and annual safety training before after-hours lab access.'},
      {id:'E2',type:'policy_memo',text:'Policy memo B allows trained research staff to request after-hours access through the security office without chair approval.'},
      {id:'E3',type:'training_record',text:'The synthetic requester completed annual safety training on 2026-08-18.'}],expected_conflicts:[['E1','E2']]},
    {id:'research-access',title:'Research access request',question:'What review steps are required before releasing the synthetic research dataset?',evidence:[
      {id:'E1',type:'request',text:'The synthetic requester asks for a de-identified dataset for a campus mobility study.'},
      {id:'E2',type:'data_policy',text:'Dataset release requires data-owner approval, a purpose statement, and a documented retention period.'},
      {id:'E3',type:'security_note',text:'The proposed workspace supports encrypted storage and access logging.'},
      {id:'E4',type:'review_note',text:'No data-owner approval is attached to the request.'}],expected_conflicts:[]},
    {id:'energy-anomaly',title:'Facilities energy anomaly',question:'What should facilities investigate first after the overnight energy spike?',evidence:[
      {id:'E1',type:'meter_event',text:'Building C electricity use increased 38 percent between 01:00 and 03:00 compared with the prior seven-night median.'},
      {id:'E2',type:'maintenance_note',text:'Air-handler AHU-C3 was placed in manual override during a ventilation inspection at 00:42.'},
      {id:'E3',type:'occupancy_note',text:'No scheduled overnight event or approved extended occupancy is recorded for Building C.'},
      {id:'E4',type:'weather_note',text:'Outdoor temperature remained within two degrees of the seven-night median.'}],expected_conflicts:[]}
  ];

  const ACTIONS = {
    'policy-conflict': [
      ['Pause approval until the conflicting approval paths are reconciled by the policy owner.', ['E1', 'E2']],
      ['Treat annual safety training as satisfied for this synthetic request.', ['E3']]],
    'research-access': [
      ['Obtain data-owner approval before release.', ['E2', 'E4']],
      ['Record the purpose statement and retention period before release.', ['E2']],
      ['Use the encrypted, access-logged workspace if the request is approved.', ['E3']]],
    'energy-anomaly': [
      ['Inspect AHU-C3 manual override first because its timing precedes the overnight spike.', ['E1', 'E2']],
      ['Do not attribute the spike to scheduled occupancy or unusual weather without new evidence.', ['E3', 'E4']]]
  };

  const claim = (text, citations, kind = 'evidence') => ({text, citations, kind});
  const own = (obj, key) => (Object.prototype.hasOwnProperty.call(obj, key) ? obj[key] : undefined);
  const isObject = v => typeof v === 'object' && v !== null && !Array.isArray(v);
  const pairKey = ids => JSON.stringify([...ids].sort());

  // Python's str.split()/str.strip() whitespace set, so text normalization matches exactly.
  const WS = '\\t\\n\\x0b\\x0c\\r\\x1c-\\x1f \\x85\\xa0\\u1680\\u2000-\\u200a\\u2028\\u2029\\u202f\\u205f\\u3000';
  const WS_RUN = new RegExp(`[${WS}]+`);
  const WS_EDGES = new RegExp(`^[${WS}]+|[${WS}]+$`, 'g');

  function analyzeCase(c) {
    const evidence = new Set(c.evidence.map(e => e.id));
    const report = {
      case_id: c.id,
      title: c.title,
      question: c.question,
      claims: c.evidence.map(e => claim(e.text, [e.id])),
      conflicts: (c.expected_conflicts || []).map(([left, right]) => ({
        evidence: [left, right],
        detail: `Conflict requires human resolution: [${left}] and [${right}] prescribe incompatible approval paths.`
      })),
      actions: (ACTIONS[c.id] || []).map(([text, citations]) => claim(text, citations, 'action')),
      uncertainty: 'Only supplied synthetic evidence was considered; missing records may change the result.',
      review_gate: {required: true, status: 'PENDING_HUMAN_REVIEW'}
    };
    report.validation = validateReport(report, evidence, c);
    return report;
  }

  function validateReport(report, evidence, c) {
    const invalid = [];
    const uncited = [];
    for (const item of [...report.claims, ...report.actions]) {
      const citations = item.citations || [];
      if (!citations.length) uncited.push(item.text);
      for (const citation of citations) if (!evidence.has(citation)) invalid.push(citation);
    }
    const found = new Set((report.conflicts || []).map(x => pairKey(x.evidence)));
    const expected = new Set((c.expected_conflicts || []).map(pairKey));
    return {
      citation_validity: !invalid.length && !uncited.length ? 1.0 : 0.0,
      invalid_citations: [...new Set(invalid)].sort(),
      uncited_items: uncited,
      conflict_detection: found.size === expected.size && [...found].every(k => expected.has(k)),
      unsupported_material_claims: invalid.length + uncited.length
    };
  }

  function pyStr(value) {
    if (value === null || value === undefined) return 'None';
    if (value === true) return 'True';
    if (value === false) return 'False';
    return typeof value === 'string' ? value : String(value);
  }

  function boundedText(value, limit = 600) {
    if (typeof value !== 'string') return '';
    let text = value.split(WS_RUN).filter(Boolean).join(' ');
    text = Array.from(text, ch => (ch.codePointAt(0) < 128 ? ch : '?')).join('');
    text = text.replace(/(?<=[A-Za-z])\?+(?=[A-Za-z])/g, '-');
    return text.slice(0, limit);
  }

  function citationList(value) {
    if (!Array.isArray(value)) return [];
    return value.map(v => pyStr(v).replace(WS_EDGES, '')).filter(Boolean).slice(0, 6);
  }

  function filterItems(rows, validIds, textKey, citeKey, limit) {
    const accepted = [];
    const rejected = [];
    if (!Array.isArray(rows)) return [accepted, rejected];
    for (const row of rows.slice(0, limit)) {
      if (!isObject(row)) {
        rejected.push({reason: 'wrong_shape'});
        continue;
      }
      const text = boundedText(own(row, textKey));
      const citations = citationList(own(row, citeKey));
      const invalid = citations.filter(c => !validIds.has(c));
      if (!text || !citations.length || invalid.length) {
        rejected.push({reason: 'missing_or_invalid_citation', invalid_citations: invalid});
        continue;
      }
      accepted.push({[textKey]: text, [citeKey]: citations});
    }
    return [accepted, rejected];
  }

  function normalizeSynthesis(c, payload) {
    const validIds = new Set(c.evidence.map(e => e.id));
    const body = isObject(payload) ? payload : {};
    const [findings, rejectedFindings] = filterItems(own(body, 'findings'), validIds, 'text', 'citations', 8);
    const [actions, rejectedActions] = filterItems(own(body, 'actions'), validIds, 'text', 'citations', 6);
    const [candidates, rejectedConflicts] = filterItems(own(body, 'conflicts'), validIds, 'detail', 'evidence', 4);
    const expected = new Set((c.expected_conflicts || []).map(pairKey));
    const conflicts = [];
    const rejectedRelations = [];
    for (const conflict of candidates) {
      const pair = [...new Set(conflict.evidence)].sort();
      if (expected.has(JSON.stringify(pair))) conflicts.push(conflict);
      else rejectedRelations.push({reason: 'unsupported_conflict_relation', evidence: pair});
    }
    const rejected = [...rejectedFindings, ...rejectedActions, ...rejectedConflicts, ...rejectedRelations];
    const invalid = [...new Set(rejected.flatMap(row => row.invalid_citations || []))].sort();
    const acceptedPairs = new Set(conflicts.map(x => pairKey(x.evidence)));
    return {
      summary: boundedText(own(body, 'summary'), 900),
      findings,
      actions,
      conflicts,
      uncertainty: boundedText(own(body, 'uncertainty'), 700),
      acceptance: {
        accepted_items: findings.length + actions.length + conflicts.length,
        rejected_items: rejected.length,
        invalid_citations: invalid,
        all_accepted_items_grounded: !invalid.length,
        unsupported_conflict_relations_rejected: rejectedRelations.length,
        model_conflict_detection: acceptedPairs.size === expected.size && [...acceptedPairs].every(k => expected.has(k)),
        policy: 'Only model items with supplied evidence IDs and seeded-valid conflict relations survive the deterministic acceptance layer.'
      },
      rejected
    };
  }

  // Model drafts a visitor can run through the gate. Each is built from the selected case.
  const SCENARIOS = [
    {id: 'grounded', label: 'Grounded draft (should pass)', build: c => ({
      summary: `Draft answer to: ${c.question}`,
      findings: c.evidence.slice(0, 2).map(e => ({text: e.text, citations: [e.id]})),
      actions: [{text: 'Send the decision to a human reviewer together with the cited evidence.', citations: [c.evidence[0].id]}],
      conflicts: (c.expected_conflicts || []).map(([a, b]) => ({detail: `[${a}] and [${b}] prescribe incompatible requirements.`, evidence: [a, b]})),
      uncertainty: 'Only the supplied evidence was considered.'
    })},
    {id: 'uncited', label: 'A finding with no citation', build: c => ({
      findings: [
        {text: 'This request is low risk and can be approved today.', citations: []},
        {text: c.evidence[0].text, citations: [c.evidence[0].id]}],
      actions: [], conflicts: []
    })},
    {id: 'invented_id', label: 'Cites evidence that does not exist', build: c => ({
      findings: [{text: 'A prior incident report supports approval.', citations: ['E9']}],
      actions: [{text: 'Approve on the strength of the incident report.', citations: [c.evidence[0].id, 'E9']}],
      conflicts: []
    })},
    {id: 'invented_conflict', label: 'Claims a conflict the evidence does not support', build: c => ({
      findings: [], actions: [],
      conflicts: [{detail: 'These two records contradict each other.', evidence: [c.evidence[1].id, c.evidence[2].id]}]
    })},
    {id: 'malformed', label: 'Malformed and empty items', build: c => ({
      findings: ['approve it', {text: '   ', citations: [c.evidence[0].id]}],
      actions: {text: 'not a list'},
      conflicts: []
    })}
  ];

  return {CASES, analyzeCase, validateReport, normalizeSynthesis, boundedText, citationList, SCENARIOS};
});
