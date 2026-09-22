import test from "node:test";
import assert from "node:assert/strict";
import { buildScienceJudgePrompt, parseScienceJudgeJson } from "../lib/judge.mjs";

test("science judge prompt is adversarial and uncertainty-aware", () => {
  const prompt = buildScienceJudgePrompt(
    { concept: "Saturn rings", accuracyNotes: "rings must be coplanar" },
    { observable_claim: "ring divisions", accuracy_guardrails: ["thin rings"], exclusions: ["labels"] }
  );
  assert.match(prompt, /impossible geometry/);
  assert.match(prompt, /rings must be coplanar/);
  assert.match(prompt, /Do not trust the plan/);
  assert.match(prompt, /cannot be verified visually/);
  assert.match(prompt, /not proof/);
});

test("parses transport-escaped judge JSON and derives verdict from score", () => {
  const raw = String.raw`{\n\"score\":4,\n\"verdict\":\"pass\",\n\"feedback\":\"Ring planes conflict.\",\n\"visible_issues\":[\"perpendicular rings\"],\n\"suggested_correction\":\"Keep all rings in one plane.\",\n\"uncertainty\":\"Exact ring thickness cannot be measured from this image.\"\n}`;
  const result = parseScienceJudgeJson(raw);
  assert.equal(result.score, 4);
  assert.equal(result.verdict, "revise");
  assert.deepEqual(result.visibleIssues, ["perpendicular rings"]);
  assert.match(result.uncertainty, /cannot be measured/);
});

test("provides an explicit uncertainty fallback for older judge responses", () => {
  const result = parseScienceJudgeJson('{"score":8,"feedback":"Geometry is visually consistent.","visible_issues":[],"suggested_correction":"Keep current geometry."}');
  assert.equal(result.verdict, "pass");
  assert.equal(result.uncertainty, "No additional visual uncertainty reported.");
});
