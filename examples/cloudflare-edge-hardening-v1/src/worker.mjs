/**
 * HAL Cloudflare Edge Hardening Reference v1
 *
 * Public-safe reference implementation. No production hostname, gateway token,
 * Turnstile secret, account id, or rate-limit namespace is embedded here.
 *
 * Expected bindings:
 *   AI                    Workers AI binding
 *   CHAT_RATE_LIMITER     Cloudflare Rate Limiting binding
 *   HEAVY_RATE_LIMITER    Cloudflare Rate Limiting binding
 *
 * Expected secrets / vars:
 *   HAL_GATEWAY_URL
 *   HAL_GATEWAY_TOKEN
 *   HAL_ALLOWED_ORIGINS       comma-separated
 *   HAL_TURNSTILE_SECRET      required for browser session issuance
 *   HAL_SESSION_SECRET        HMAC secret for short-lived browser sessions
 *   HAL_API_BEARER            optional trusted mobile/CLI bearer
 *   HAL_REQUIRE_AUTH          "1" to require session/API bearer
 *   HAL_EDGE_FALLBACK_ENABLED "1" to enable Workers AI fallback
 *   HAL_EDGE_FALLBACK_MODEL   optional @cf/... model
 */

const MODES = Object.freeze({
  chat:    { model: "hal/chat",    maxTokens: 768,  heavy: false },
  fast:    { model: "hal/fast",    maxTokens: 1024, heavy: false },
  build:   { model: "hal/coder",   maxTokens: 2048, heavy: true  },
  expert:  { model: "hal/deep",    maxTokens: 2048, heavy: true  },
  council: { model: "hal/council", maxTokens: 1536, heavy: true  },
});

const MAX_BODY_BYTES = 96 * 1024;
const MAX_MESSAGES = 48;
const MAX_MESSAGE_CHARS = 24_000;
const DEFAULT_FALLBACK_MODEL = "@cf/meta/llama-3.1-8b-instruct";

function json(status, body, extra = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "x-content-type-options": "nosniff",
      "referrer-policy": "no-referrer",
      ...extra,
    },
  });
}

function allowedOrigins(env) {
  return new Set(
    String(env.HAL_ALLOWED_ORIGINS || "")
      .split(",")
      .map((x) => x.trim())
      .filter(Boolean)
  );
}

function corsHeaders(request, env) {
  const origin = request.headers.get("Origin");
  const allowed = allowedOrigins(env);
  if (origin && allowed.has(origin)) {
    return {
      "access-control-allow-origin": origin,
      "access-control-allow-methods": "POST,OPTIONS,GET",
      "access-control-allow-headers": "content-type,authorization,x-turnstile-token",
      "access-control-max-age": "600",
      "vary": "Origin",
    };
  }
  return {};
}

function rejectBrowserOrigin(request, env) {
  const origin = request.headers.get("Origin");
  if (!origin) return null;
  if (!allowedOrigins(env).has(origin)) {
    return json(403, { error: "origin_not_allowed" });
  }
  return null;
}

function ipKey(request) {
  return (
    request.headers.get("CF-Connecting-IP") ||
    request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ||
    "unknown"
  );
}

async function rateLimit(binding, key) {
  if (!binding || typeof binding.limit !== "function") return true;
  const outcome = await binding.limit({ key });
  return Boolean(outcome?.success);
}

async function validateTurnstile(request, env) {
  if (!request.headers.get("Origin")) {
    return { ok: false, reason: "browser_proof_required" };
  }
  const token = request.headers.get("x-turnstile-token");
  if (!token || !env.HAL_TURNSTILE_SECRET) {
    return { ok: false, reason: "missing_turnstile" };
  }
  const form = new FormData();
  form.set("secret", env.HAL_TURNSTILE_SECRET);
  form.set("response", token);
  const ip = request.headers.get("CF-Connecting-IP");
  if (ip) form.set("remoteip", ip);

  const r = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", {
    method: "POST",
    body: form,
  });
  if (!r.ok) return { ok: false, reason: "turnstile_unavailable" };
  const result = await r.json();
  return {
    ok: result.success === true,
    reason: result.success === true ? null : "turnstile_rejected",
  };
}


function utf8(value) {
  return new TextEncoder().encode(value);
}

function toBase64Url(bytes) {
  let binary = "";
  for (const b of bytes) binary += String.fromCharCode(b);
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

function fromBase64Url(value) {
  const normalized = value.replace(/-/g, "+").replace(/_/g, "/");
  const padded = normalized + "=".repeat((4 - (normalized.length % 4)) % 4);
  const binary = atob(padded);
  return Uint8Array.from(binary, (c) => c.charCodeAt(0));
}

async function importSessionKey(secret) {
  return crypto.subtle.importKey(
    "raw",
    utf8(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign", "verify"]
  );
}

async function createSessionToken(env, ttlSeconds = 900) {
  if (!env.HAL_SESSION_SECRET) throw new Error("session_secret_missing");
  const now = Math.floor(Date.now() / 1000);
  const body = toBase64Url(utf8(JSON.stringify({
    v: 1,
    scope: "hal:chat",
    iat: now,
    exp: now + ttlSeconds,
    nonce: crypto.randomUUID(),
  })));
  const key = await importSessionKey(env.HAL_SESSION_SECRET);
  const signature = new Uint8Array(await crypto.subtle.sign("HMAC", key, utf8(body)));
  return `${body}.${toBase64Url(signature)}`;
}

async function verifySessionToken(token, env) {
  if (!env.HAL_SESSION_SECRET || typeof token !== "string") return false;
  const parts = token.split(".");
  if (parts.length !== 2) return false;
  try {
    const key = await importSessionKey(env.HAL_SESSION_SECRET);
    const ok = await crypto.subtle.verify("HMAC", key, fromBase64Url(parts[1]), utf8(parts[0]));
    if (!ok) return false;
    const payload = JSON.parse(new TextDecoder().decode(fromBase64Url(parts[0])));
    const now = Math.floor(Date.now() / 1000);
    return payload?.v === 1 && payload?.scope === "hal:chat" && Number(payload?.exp) > now;
  } catch {
    return false;
  }
}

async function authorizeRequest(request, env) {
  if (env.HAL_REQUIRE_AUTH !== "1") return { ok: true, type: "disabled" };
  const header = request.headers.get("authorization") || "";
  if (!header.startsWith("Bearer ")) return { ok: false, reason: "authorization_required" };
  const token = header.slice(7).trim();
  if (env.HAL_API_BEARER && token === env.HAL_API_BEARER) return { ok: true, type: "api" };
  if (await verifySessionToken(token, env)) return { ok: true, type: "session" };
  return { ok: false, reason: "authorization_rejected" };
}

async function handleSession(request, env) {
  const originFailure = rejectBrowserOrigin(request, env);
  if (originFailure) return originFailure;
  if (!(await rateLimit(env.CHAT_RATE_LIMITER, `session:${ipKey(request)}`))) {
    return json(429, { error: "rate_limited" }, { "retry-after": "60" });
  }
  const proof = await validateTurnstile(request, env);
  if (!proof.ok) return json(403, { error: proof.reason });
  if (!env.HAL_SESSION_SECRET) return json(503, { error: "session_not_configured" });
  const token = await createSessionToken(env);
  return json(200, { session_token: token, token_type: "Bearer", expires_in: 900 });
}

function sanitizeMessages(messages) {
  if (!Array.isArray(messages)) throw new Error("messages_required");
  if (messages.length < 1 || messages.length > MAX_MESSAGES) throw new Error("message_count");
  let chars = 0;
  const clean = messages.map((m) => {
    const role = String(m?.role || "");
    if (!['user', 'assistant'].includes(role)) throw new Error("invalid_role");
    const content = typeof m.content === "string" ? m.content : JSON.stringify(m.content ?? "");
    chars += content.length;
    if (chars > MAX_MESSAGE_CHARS) throw new Error("messages_too_large");
    return { role, content };
  });
  return clean;
}

function normalizeChatPayload(raw) {
  const requestedMode = String(raw?.mode || "chat");
  const known = Object.prototype.hasOwnProperty.call(MODES, requestedMode);
  const modeName = known ? requestedMode : "chat";
  const mode = MODES[modeName];
  return {
    modeName,
    upstreamModel: mode.model,
    max_tokens: Math.max(1, Math.min(Number(raw?.max_tokens || mode.maxTokens), mode.maxTokens)),
    temperature: Math.max(0, Math.min(Number(raw?.temperature ?? 0.4), 1.2)),
    messages: sanitizeMessages(raw?.messages),
    heavy: mode.heavy,
  };
}

function fallbackPrompt(messages) {
  const safe = messages
    .slice(-12)
    .map((m) => `${m.role.toUpperCase()}: ${m.content}`)
    .join("\n\n");
  return [
    "You are HAL edge fallback. Be concise, factual, and transparent.",
    "The home HAL gateway is unavailable. Do not claim access to local memory, tools, files,",
    "accounts, agents, or computer state. Do not imitate unavailable persona/audio behaviors.",
    "Answer only from the conversation text supplied below.",
    "",
    safe,
  ].join("\n");
}

async function gatewayChat(payload, env) {
  if (!env.HAL_GATEWAY_URL || !env.HAL_GATEWAY_TOKEN) {
    throw new Error("gateway_not_configured");
  }
  const r = await fetch(`${String(env.HAL_GATEWAY_URL).replace(/\/$/, "")}/v1/chat/completions`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "authorization": `Bearer ${env.HAL_GATEWAY_TOKEN}`,
    },
    body: JSON.stringify({
      model: payload.upstreamModel,
      messages: payload.messages,
      max_tokens: payload.max_tokens,
      temperature: payload.temperature,
      stream: false,
    }),
    signal: AbortSignal.timeout(25_000),
  });
  if (!r.ok) throw new Error(`gateway_status_${r.status}`);
  return r;
}

async function workersAiFallback(payload, env) {
  if (env.HAL_EDGE_FALLBACK_ENABLED !== "1" || !env.AI) {
    throw new Error("fallback_disabled");
  }
  const model = env.HAL_EDGE_FALLBACK_MODEL || DEFAULT_FALLBACK_MODEL;
  const result = await env.AI.run(model, {
    prompt: fallbackPrompt(payload.messages),
    max_tokens: Math.min(payload.max_tokens, 768),
    temperature: Math.min(payload.temperature, 0.7),
  });
  const text =
    typeof result === "string" ? result :
    result?.response ?? result?.result?.response ?? JSON.stringify(result);

  return json(200, {
    id: `hal-edge-${crypto.randomUUID()}`,
    object: "chat.completion",
    model,
    degraded: true,
    provenance: {
      source: "cloudflare_workers_ai_fallback",
      home_gateway_available: false,
      local_tools_available: false,
      local_memory_available: false,
    },
    choices: [{ index: 0, message: { role: "assistant", content: text }, finish_reason: "stop" }],
  }, { "x-hal-degraded": "1" });
}

async function readJsonLimited(request) {
  const declared = Number(request.headers.get("content-length") || 0);
  if (declared > MAX_BODY_BYTES) throw new Error("body_too_large");
  const text = await request.text();
  if (new TextEncoder().encode(text).length > MAX_BODY_BYTES) throw new Error("body_too_large");
  return JSON.parse(text);
}

async function handleChat(request, env) {
  const originFailure = rejectBrowserOrigin(request, env);
  if (originFailure) return originFailure;

  const authorization = await authorizeRequest(request, env);
  if (!authorization.ok) return json(401, { error: authorization.reason });

  if (!(await rateLimit(env.CHAT_RATE_LIMITER, `chat:${ipKey(request)}`))) {
    return json(429, { error: "rate_limited" }, { "retry-after": "60" });
  }

  let payload;
  try {
    payload = normalizeChatPayload(await readJsonLimited(request));
  } catch (e) {
    return json(400, { error: String(e?.message || "invalid_request") });
  }

  if (payload.heavy && !(await rateLimit(env.HEAVY_RATE_LIMITER, `heavy:${ipKey(request)}`))) {
    return json(429, { error: "heavy_mode_rate_limited" }, { "retry-after": "60" });
  }

  try {
    const r = await gatewayChat(payload, env);
    const headers = new Headers(r.headers);
    headers.set("cache-control", "no-store");
    headers.set("x-hal-edge-mode", payload.modeName);
    headers.set("x-hal-degraded", "0");
    return new Response(r.body, { status: r.status, headers });
  } catch {
    try {
      return await workersAiFallback(payload, env);
    } catch {
      return json(502, {
        error: "hal_gateway_unavailable",
        degraded_fallback_available: env.HAL_EDGE_FALLBACK_ENABLED === "1",
      });
    }
  }
}

async function handleHealth(env) {
  const fallbackReady = env.HAL_EDGE_FALLBACK_ENABLED === "1" && Boolean(env.AI);
  return json(200, {
    ok: true,
    service: "hal-chat-edge",
    version: "1.0.0-reference",
    gateway_configured: Boolean(env.HAL_GATEWAY_URL && env.HAL_GATEWAY_TOKEN),
    edge_fallback_enabled: fallbackReady,
    modes: Object.keys(MODES),
    security: {
      client_tools_forwarded: false,
      client_system_messages_allowed: false,
      request_budget_enforced: true,
      rate_limit_bindings_expected: true,
      turnstile_supported: true,
      short_lived_session_supported: true,
      trusted_api_bearer_supported: true,
    },
  });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const cors = corsHeaders(request, env);

    if (request.method === "OPTIONS") {
      if (request.headers.get("Origin") && !allowedOrigins(env).has(request.headers.get("Origin"))) {
        return new Response(null, { status: 403 });
      }
      return new Response(null, { status: 204, headers: cors });
    }

    if (request.method === "GET" && url.pathname === "/health") {
      const r = await handleHealth(env);
      Object.entries(cors).forEach(([k, v]) => r.headers.set(k, v));
      return r;
    }

    if (request.method === "POST" && url.pathname === "/session") {
      const r = await handleSession(request, env);
      Object.entries(cors).forEach(([k, v]) => r.headers.set(k, v));
      return r;
    }

    if (request.method === "POST" && ["/chat", "/v1/chat/completions"].includes(url.pathname)) {
      const r = await handleChat(request, env);
      Object.entries(cors).forEach(([k, v]) => r.headers.set(k, v));
      return r;
    }

    return json(404, { error: "not_found" }, cors);
  },
};

export { MODES, normalizeChatPayload, sanitizeMessages, fallbackPrompt, allowedOrigins, createSessionToken, verifySessionToken, authorizeRequest };
