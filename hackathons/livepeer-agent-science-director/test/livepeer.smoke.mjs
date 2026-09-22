import { LivepeerMcpClient, collectToolText, extractMediaUrl } from "../lib/livepeer.mjs";
import { buildPlannerPrompt, buildRenderPrompt, normalizeBrief, parsePlannerJson } from "../lib/prompts.mjs";

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
const media = await livepeer.runCapability({
  capability: process.env.LIVEPEER_IMAGE_CAPABILITY || "flux-schnell",
  prompt: buildRenderPrompt(plan, brief),
  inputs: { aspect_ratio: brief.aspectRatio },
  timeout: 90,
  async: false,
  idempotencyKey: `hal_ci_image_${Date.now()}`
});
const outputUrl = extractMediaUrl(media);
if (!outputUrl) throw new Error("Smoke test completed without a media URL.");
console.log(JSON.stringify({ ok: true, title: plan.title, outputUrl }, null, 2));
