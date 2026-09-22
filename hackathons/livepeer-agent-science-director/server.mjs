import http from "node:http";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import crypto from "node:crypto";
import { LivepeerMcpClient, collectToolText, extractMediaUrl } from "./lib/livepeer.mjs";
import { normalizeBrief, buildPlannerPrompt, buildFallbackPlan, buildRenderPrompt, parsePlannerJson } from "./lib/prompts.mjs";
import { judgeScienceArtifact } from "./lib/judge.mjs";

const root = path.dirname(fileURLToPath(import.meta.url));
const publicDir = path.join(root, "public");
const port = Number(process.env.PORT || 8787);

const livepeerText = new LivepeerMcpClient({
  endpoint: process.env.LIVEPEER_MCP_URL || "https://agent.livepeer.org/api/mcp",
  bearer: process.env.LIVEPEER_MCP_BEARER || ""
});
const livepeerCreative = new LivepeerMcpClient({
  endpoint: process.env.LIVEPEER_CREATIVE_MCP_URL || "https://agent.livepeer.org/api/mcp/creative",
  bearer: process.env.LIVEPEER_MCP_BEARER || ""
});

const recentRuns = [];

const server = http.createServer(async (req, res) => {
  try {
    const url = new URL(req.url || "/", `http://${req.headers.host || "localhost"}`);
    if (req.method === "GET" && url.pathname === "/api/health") {
      return json(res, 200, {
        ok: true,
        livepeerEndpoint: process.env.LIVEPEER_MCP_URL || "https://agent.livepeer.org/api/mcp",
        authMode: process.env.LIVEPEER_MCP_BEARER ? "bearer" : "keyless-demo",
        recentRuns: recentRuns.length
      });
    }
    if (req.method === "GET" && url.pathname === "/api/runs") return json(res, 200, { runs: recentRuns });
    if (req.method === "POST" && url.pathname === "/api/direct") {
      const body = await readJson(req);
      const result = await direct(body);
      return json(res, 200, result);
    }
    if (req.method === "POST" && url.pathname === "/api/refine") {
      const body = await readJson(req);
      const previous = recentRuns.find((run) => run.id === body.previousRunId);
      if (!previous) return json(res, 404, { error: "Previous run not found in this server session." });
      const result = await direct({ ...previous.brief, feedback: body.feedback || previous.brief.feedback });
      return json(res, 200, result);
    }
    if (req.method !== "GET") return json(res, 404, { error: "Not found" });
    await serveStatic(url.pathname, res);
  } catch (error) {
    console.error(error);
    json(res, 500, { error: sanitize(error) });
  }
});

server.listen(port, "0.0.0.0", () => {
  console.log(`HAL Science Director listening on http://localhost:${port}`);
});

async function direct(input) {
  const brief = normalizeBrief(input);
  const startedAt = new Date().toISOString();
  const textCapability = process.env.LIVEPEER_TEXT_CAPABILITY || "gemini-text";

  let plan;
  let plannerMode = "livepeer-text";
  let plannerWarning = "";
  try {
    const plannerPayload = await livepeerText.runCapability({
      capability: textCapability,
      prompt: buildPlannerPrompt(brief),
      timeout: 90,
      async: false,
      idempotencyKey: stableKey("plan", JSON.stringify(brief))
    });
    plan = parsePlannerJson(collectToolText(plannerPayload));
  } catch (error) {
    plannerMode = "degraded-local";
    plannerWarning = sanitize(error);
    plan = buildFallbackPlan(brief);
  }

  const renderPrompt = buildRenderPrompt(plan, brief);
  const isVideo = brief.mediaType === "video";
  const capability = isVideo
    ? (process.env.LIVEPEER_VIDEO_CAPABILITY || "kling-o3-t2v")
    : (process.env.LIVEPEER_IMAGE_CAPABILITY || "flux-schnell");
  const timeout = isVideo
    ? Number(process.env.LIVEPEER_VIDEO_TIMEOUT_SECONDS || 600)
    : Number(process.env.LIVEPEER_IMAGE_TIMEOUT_SECONDS || 90);

  let outputUrl = "";
  let mediaFallback = "";
  let mediaWarning = "";
  try {
    const mediaPayload = await livepeerCreative.createMedia({
      prompt: renderPrompt,
      mediaType: brief.mediaType,
      aspectRatio: brief.aspectRatio,
      durationSeconds: brief.durationSeconds,
      modelOverride: capability,
      maxCostUsd: isVideo ? 2.5 : 0.25,
      timeout
    });
    outputUrl = extractMediaUrl(mediaPayload);
    if (!outputUrl) throw new Error("Livepeer completed the media step without an output URL.");
  } catch (error) {
    const message = sanitize(error);
    if (!/demo budget store unavailable|demo_budget_exhausted/i.test(message)) throw error;
    mediaFallback = "verified-demo-video";
    mediaWarning = message;
    const publicBase = process.env.PUBLIC_BASE_URL || "https://hal-science-director-production.up.railway.app";
    outputUrl = `${publicBase.replace(/\/$/, "")}/HAL_SCIENCE_DIRECTOR_SUBMISSION_DEMO.mp4`;
  }

  let scienceReview;
  if (mediaFallback) {
    scienceReview = {
      score: null,
      verdict: "unavailable",
      feedback: "Live generation is temporarily unavailable on this public keyless deployment, so the verified recorded submission demo is shown instead.",
      visibleIssues: [],
      suggestedCorrection: "",
      uncertainty: "No new artifact was generated or judged in this degraded run; do not treat the recorded demo as a review of the current brief."
    };
  } else {
    try {
      scienceReview = await judgeScienceArtifact({ livepeer: livepeerText, outputUrl, brief, plan, capability: textCapability });
    } catch (error) {
      scienceReview = {
        score: null,
        verdict: "unavailable",
        feedback: sanitize(error),
        visibleIssues: [],
        suggestedCorrection: "",
        uncertainty: "Visual review did not complete; treat the generated artifact as unverified rather than scientifically validated."
      };
    }
  }

  const run = {
    id: `run_${crypto.randomUUID().slice(0, 12)}`,
    startedAt,
    finishedAt: new Date().toISOString(),
    brief,
    plan,
    renderPrompt,
    livepeer: {
      textCapability,
      mediaCapability: capability,
      judgeCapability: textCapability,
      outputUrl,
      plannerMode,
      plannerWarning,
      mediaSurface: "creative-mcp",
      mediaFallback,
      mediaWarning
    },
    scienceReview,
    provenanceHash: crypto.createHash("sha256").update(JSON.stringify({ brief, plan, capability, outputUrl, scienceReview })).digest("hex")
  };
  recentRuns.unshift(run);
  recentRuns.splice(20);
  return run;
}

async function serveStatic(pathname, res) {
  const relative = pathname === "/" ? "index.html" : pathname.replace(/^\/+/, "");
  const normalized = path.normalize(relative).replace(/^(\.\.(\/|\\|$))+/, "");
  const filePath = path.join(publicDir, normalized);
  if (!filePath.startsWith(publicDir)) return json(res, 403, { error: "Forbidden" });
  try {
    const body = await fs.readFile(filePath);
    res.writeHead(200, { "content-type": mime(filePath), "cache-control": "no-store" });
    res.end(body);
  } catch {
    json(res, 404, { error: "Not found" });
  }
}

async function readJson(req) {
  const chunks = [];
  let size = 0;
  for await (const chunk of req) {
    size += chunk.length;
    if (size > 100_000) throw new Error("Request body too large.");
    chunks.push(chunk);
  }
  return JSON.parse(Buffer.concat(chunks).toString("utf8") || "{}");
}

function json(res, status, payload) {
  res.writeHead(status, { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" });
  res.end(JSON.stringify(payload));
}

function stableKey(stage, seed) {
  const digest = crypto.createHash("sha256").update(seed).digest("hex").slice(0, 36);
  return `hal_${stage}_${digest}`;
}

function sanitize(error) {
  return String(error?.message || error || "Unknown error")
    .replace(/Bearer\s+[A-Za-z0-9._-]+/gi, "Bearer [redacted]")
    .replace(/sk_[A-Za-z0-9_-]+/g, "sk_[redacted]")
    .slice(0, 700);
}

function mime(file) {
  if (file.endsWith(".html")) return "text/html; charset=utf-8";
  if (file.endsWith(".js")) return "text/javascript; charset=utf-8";
  if (file.endsWith(".css")) return "text/css; charset=utf-8";
  if (file.endsWith(".svg")) return "image/svg+xml";
  if (file.endsWith(".mp4")) return "video/mp4";
  return "application/octet-stream";
}
