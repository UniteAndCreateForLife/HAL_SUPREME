import crypto from "node:crypto";

export class LivepeerMcpClient {
  constructor({ endpoint, bearer, fetchImpl = fetch } = {}) {
    this.endpoint = endpoint || "https://agent.livepeer.org/api/mcp";
    this.bearer = bearer || "";
    this.fetchImpl = fetchImpl;
    this.sessionId = "";
    this.initialized = false;
  }

  async initialize() {
    if (this.initialized) return;
    const result = await this.#rpc("initialize", {
      protocolVersion: "2025-03-26",
      capabilities: {},
      clientInfo: { name: "hal-livepeer-science-director", version: "0.1.0" }
    });
    if (result.error) throw new Error(`Livepeer MCP initialize failed: ${safeError(result.error)}`);
    this.initialized = true;
  }

  async callTool(name, args = {}) {
    await this.initialize();
    const payload = await this.#rpc("tools/call", { name, arguments: args });
    assertToolSuccess(payload, name);
    return payload;
  }

  async runCapability({ capability, prompt, sourceUrl, inputs, timeout = 60, async = false, idempotencyKey }) {
    const payload = await this.callTool("run_capability", {
      capability,
      ...(prompt ? { prompt } : {}),
      ...(sourceUrl ? { source_url: sourceUrl } : {}),
      ...(inputs ? { inputs } : {}),
      timeout,
      async,
      persist: false,
      session_id: "hal_science_director",
      idempotency_key: idempotencyKey || `hal_${crypto.randomUUID()}`
    });

    if (!async) return payload;
    const jobId = extractJobId(payload);
    if (!jobId) throw new Error("Livepeer accepted an asynchronous render without returning a job id.");
    return this.waitForMediaJob(jobId, timeout);
  }

  async createMedia({ prompt, mediaType = "image", aspectRatio = "16:9", durationSeconds, modelOverride, maxCostUsd, timeout = 600 }) {
    const args = {
      action: "generate",
      prompt,
      aspect_ratio: aspectRatio,
      persist: false,
      session_id: "hal_science_director",
      ...(modelOverride ? { model_override: modelOverride } : {}),
      ...(maxCostUsd ? { max_cost_usd: maxCostUsd } : {}),
      ...(mediaType === "video" && durationSeconds ? { duration: durationSeconds } : {})
    };
    const payload = await this.callTool("create_media", args);
    const jobId = extractJobId(payload);
    if (!jobId) return payload;
    return this.waitForMediaJob(jobId, timeout);
  }

  async waitForMediaJob(jobId, timeoutSeconds = 600) {
    const deadline = Date.now() + timeoutSeconds * 1000;
    while (Date.now() < deadline) {
      const payload = await this.callTool("get_create_media", { job_id: jobId });
      const status = extractStatus(payload);
      if (["failed", "cancelled", "error"].includes(status)) {
        throw new Error(`Livepeer media job ${jobId} ended with status ${status}.`);
      }
      const url = extractMediaUrl(payload);
      if (url && ["", "done", "completed", "complete", "succeeded", "success", "ready"].includes(status)) return payload;
      await delay(4000);
    }
    throw new Error(`Livepeer media job ${jobId} timed out.`);
  }

  async #rpc(method, params) {
    const response = await this.fetchImpl(this.endpoint, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        accept: "application/json, text/event-stream",
        ...(this.sessionId ? { "mcp-session-id": this.sessionId } : {}),
        ...(this.bearer ? { authorization: `Bearer ${this.bearer}` } : {})
      },
      body: JSON.stringify({ jsonrpc: "2.0", id: crypto.randomUUID(), method, params })
    });

    this.sessionId = response.headers?.get?.("mcp-session-id") || this.sessionId;
    const text = await response.text();
    if (!response.ok) throw new Error(`Livepeer MCP HTTP ${response.status}: ${text.slice(0, 300)}`);
    return parseRpcBody(text);
  }
}

export function collectToolText(payload) {
  const content = payload?.result?.content;
  if (!Array.isArray(content)) return "";
  return content.map((entry) => (typeof entry?.text === "string" ? entry.text : "")).filter(Boolean).join("\n");
}

export function extractMediaUrl(payload) {
  const result = payload?.result || {};
  const structured = result?.structuredContent || {};
  const direct = [structured.url, structured.output_url, result.url, result.output_url].find((value) => typeof value === "string" && /^https?:\/\//.test(value));
  if (direct) return direct;
  const haystack = `${collectToolText(payload)}\n${JSON.stringify(result)}`;
  const urls = haystack.match(/https?:\/\/[^"'\s)\\]+/g) || [];
  const media = urls.find((url) => /\.(png|jpe?g|webp|gif|mp4|webm|mov|m4v)(\?|$)/i.test(url));
  return (media || urls.at(-1) || "").replace(/[.,]+$/, "");
}

export function extractJobId(payload) {
  const result = payload?.result || {};
  const structured = result?.structuredContent || {};
  for (const value of [structured.job_id, structured.jobId, result.job_id, result.jobId]) {
    if (typeof value === "string" && value) return value;
  }
  const text = collectToolText(payload);
  try {
    const parsed = JSON.parse(text);
    const candidate = parsed.job_id || parsed.jobId;
    if (typeof candidate === "string") return candidate;
  } catch {}
  return text.match(/(?:job_id|jobId)["'\s:]+([A-Za-z0-9_-]+)/)?.[1] || "";
}

export function extractStatus(payload) {
  const result = payload?.result || {};
  const structured = result?.structuredContent || {};
  for (const value of [structured.status, result.status]) {
    if (typeof value === "string") return value.toLowerCase();
  }
  const text = collectToolText(payload);
  try {
    const parsed = JSON.parse(text);
    return typeof parsed.status === "string" ? parsed.status.toLowerCase() : "";
  } catch {}
  return text.match(/status["'\s:]+([A-Za-z_-]+)/i)?.[1]?.toLowerCase() || "";
}

function assertToolSuccess(payload, label) {
  if (payload?.error || payload?.result?.isError) {
    throw new Error(`${label} failed: ${safeError(payload?.error || collectToolText(payload))}`);
  }
}

function parseRpcBody(text) {
  const trimmed = String(text || "").trim();
  if (!trimmed) throw new Error("Livepeer MCP returned an empty response.");
  if (trimmed.startsWith("{")) return JSON.parse(trimmed);
  const frames = trimmed.split(/\n\n+/).map((frame) => frame.split("\n").find((line) => line.startsWith("data:"))?.slice(5).trim()).filter(Boolean);
  if (!frames.length) throw new Error("Livepeer MCP returned an unsupported response format.");
  return JSON.parse(frames.at(-1));
}

function safeError(value) {
  return String(typeof value === "string" ? value : JSON.stringify(value)).replace(/Bearer\s+[A-Za-z0-9._-]+/gi, "Bearer [redacted]").slice(0, 500);
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
