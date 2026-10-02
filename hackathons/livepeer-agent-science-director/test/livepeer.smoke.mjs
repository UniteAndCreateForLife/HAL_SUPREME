import fs from "node:fs/promises";
import { LivepeerMcpClient, collectToolText, extractMediaUrl } from "../lib/livepeer.mjs";
import { buildPlannerPrompt, buildRenderPrompt, normalizeBrief, parsePlannerJson } from "../lib/prompts.mjs";
import { judgeScienceArtifact } from "../lib/judge.mjs";

const livepeer = new LivepeerMcpClient({ endpoint: process.env.LIVEPEER_MCP_URL || "https://agent.livepeer.org/api/mcp" });
const brief = normalizeBrief({
  concept: "Show the structure of Saturn's rings without inventing labels or measurements.",
  mediaType: "image",
  aspectRatio: "16:9",
  accuracyNotes: "Keep ring structure physically plausible and avoid fake instrument overlays."
});

const planner = await livepeer.runCapability({
  capability: process.env.LIVEPEER_TEXT_CAPABILITY || "gemini-text",
  prompt: buildPlannerPrompt(brief),
  timeout: 90,
  async: false,
  idempotencyKey: `hal_ci_plan_${Date.now()}`
});
const plan = parsePlannerJson(collectToolText(planner));

const mediaCapability = process.env.LIVEPEER_IMAGE_CAPABILITY || "flux-schnell";
const media = await livepeer.runCapability({
  capability: mediaCapability,
  prompt: buildRenderPrompt(plan, brief),
  inputs: { aspect_ratio: brief.aspectRatio },
  timeout: 90,
  async: false,
  idempotencyKey: `hal_ci_image_${Date.now()}`
});
const outputUrl = extractMediaUrl(media);
if (!outputUrl) throw new Error("Smoke test completed without a media URL.");

const scienceReview = await judgeScienceArtifact({ livepeer, outputUrl, brief, plan, capability: process.env.LIVEPEER_TEXT_CAPABILITY || "gemini-text" });

const response = await fetch(outputUrl);
if (!response.ok) throw new Error(`Rendered media could not be downloaded: HTTP ${response.status}`);
const bytes = new Uint8Array(await response.arrayBuffer());

await fs.mkdir("artifacts", { recursive: true });
await fs.writeFile("artifacts/livepeer-smoke.jpg", bytes);

const receipt = {
  ok: true,
  generatedAt: new Date().toISOString(),
  plannerCapability: process.env.LIVEPEER_TEXT_CAPABILITY || "gemini-text",
  mediaCapability,
  title: plan.title,
  observableClaim: plan.observable_claim,
  accuracyGuardrails: plan.accuracy_guardrails,
  outputUrl,
  scienceReview,
  bytes: bytes.byteLength
};
await fs.writeFile("artifacts/livepeer-smoke-receipt.json", JSON.stringify(receipt, null, 2));

console.log(JSON.stringify(receipt, null, 2));
