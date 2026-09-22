import http from "node:http";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import crypto from "node:crypto";
import { LivepeerMcpClient, collectToolText, extractMediaUrl } from "./lib/livepeer.mjs";
import { normalizeBrief, buildPlannerPrompt, buildRenderPrompt, parsePlannerJson } from "./lib/prompts.mjs";
import { judgeScienceArtifact } from "./lib/judge.mjs";

const root = path.dirname(fileURLToPath(import.meta.url));
const publicDir = path.join(root, "public");
const port = Number(process.env.PORT || 8787);

const livepeer = new LivepeerMcpClient({
  endpoint: process.env.LIVEPEER_MCP_URL || "https://agent.livepeer.org/api/mcp",
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
  const plannerPayload = await livepeer.runCapability({
    capability: textCapability,
    prompt: buildPlannerPrompt(brief),
    timeout: 90,
    async: false,
    idempotencyKey: stableKey("plan", JSON.stringify(brief))
  });
  const plannerText = collectToolText(plannerPayload);
  const plan = parsePlannerJson(plannerText);
  const renderPrompt = buildRenderPrompt(plan, brief);

  const isVideo = brief.mediaType === "video";
  const capability = isVideo
    ? (process.env.LIVEPEER_VIDEO_CAPABILITY || "pixverse-t2v")
    : (process.env.LIVEPEER_IMAGE_CAPABILITY || "flux-schnell");
  const timeout = isVideo
    ? Number(process.env.LIVEPEER_VIDEO_TIMEOUT_SECONDS || 600)
    : Number(process.env.LIVEPEER_IMAGE_TIMEOUT_SECONDS || 60);
  const mediaPayload = await livepeer.runCapability({
    capability,
    prompt: renderPrompt,
    inputs: isVideo
      ? { duration: brief.durationSeconds, aspect_ratio: brief.aspectRatio }
      : { aspect_ratio: brief.aspectRatio },
    timeout,
    async: isVideo,
    idempotencyKey: stableKey("render", `${capability}:${renderPrompt}`)
  });
  const outputUrl = extractMediaUrl(mediaPayload);
  if (!outputUrl) throw new Error("Livepeer completed the media step without an output URL.");

  let scienceReview;
  try {
    scienceReview = await judgeScienceArtifact({ livepeer, outputUrl, brief, plan, capability: textCapability });
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

  const run = {
    id: `run_${crypto.randomUUID().slice(0, 12)}`,
    startedAt,
    finishedAt: new Date().toISOString(),
    brief,
    plan,
    renderPrompt,
    livepeer: { textCapability, mediaCapability: capability, judgeCapability: textCapability, outputUrl },
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
