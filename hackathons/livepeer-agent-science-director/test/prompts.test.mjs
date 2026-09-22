import test from "node:test";
import assert from "node:assert/strict";
import { normalizeBrief, buildPlannerPrompt, buildRenderPrompt, parsePlannerJson } from "../lib/prompts.mjs";

test("normalizes a science brief and clamps video duration", () => {
  const brief = normalizeBrief({ concept: "  plasma   wave ", mediaType: "video", durationSeconds: 99, aspectRatio: "16:9" });
  assert.equal(brief.concept, "plasma wave");
  assert.equal(brief.durationSeconds, 12);
});

test("planner prompt prioritizes accuracy and operator corrections", () => {
  const brief = normalizeBrief({ concept: "black hole accretion disk", feedback: "do not show jets from the event horizon" });
  const prompt = buildPlannerPrompt(brief);
  assert.match(prompt, /scientific/i);
  assert.match(prompt, /MUST be addressed/);
  assert.match(prompt, /do not show jets/);
});

test("parses fenced planner JSON and builds a constrained render prompt", () => {
  const plan = parsePlannerJson('```json\n{"title":"T","observable_claim":"C","visual_subject":"S","camera":"wide","environment":"space","motion":"slow","exclusions":["fake labels"],"accuracy_guardrails":["field lines are illustrative"],"render_prompt":"Earth magnetosphere"}\n```');
  const prompt = buildRenderPrompt(plan, normalizeBrief({ concept: "magnetosphere" }));
  assert.equal(plan.title, "T");
  assert.match(prompt, /field lines are illustrative/);
  assert.match(prompt, /fake labels/);
});

test("parses Livepeer planner JSON returned with transport escapes", () => {
  const escaped = String.raw`{\n  \"title\": \"Saturn rings\",\n  \"observable_claim\": \"A and B rings are visually distinct\",\n  \"visual_subject\": \"Saturn\",\n  \"camera\": {\"angle\": \"oblique\"},\n  \"environment\": {\"background\": \"space\"},\n  \"motion\": {\"subject_motion\": \"static\"},\n  \"exclusions\": [\"fake labels\"],\n  \"accuracy_guardrails\": [\"preserve ring gaps\"],\n  \"render_prompt\": \"Photoreal Saturn rings\"\n}`;
  const plan = parsePlannerJson(escaped);
  assert.equal(plan.title, "Saturn rings");
  assert.equal(plan.exclusions[0], "fake labels");
  assert.match(plan.camera, /oblique/);
});
