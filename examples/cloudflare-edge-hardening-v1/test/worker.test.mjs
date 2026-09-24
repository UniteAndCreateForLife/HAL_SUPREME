import test from "node:test";
import assert from "node:assert/strict";
import { MODES, normalizeChatPayload, sanitizeMessages, fallbackPrompt, allowedOrigins } from "../src/worker.mjs";

test("adds dedicated chat mode and keeps expensive modes bounded", () => {
  assert.equal(MODES.chat.model, "hal/chat");
  assert.ok(MODES.council.maxTokens <= 1536);
  assert.equal(MODES.council.heavy, true);
});

test("unknown mode falls back to chat", () => {
  const p = normalizeChatPayload({ mode: "nonsense", messages: [{ role: "user", content: "hi" }] });
  assert.equal(p.modeName, "chat");
  assert.equal(p.upstreamModel, "hal/chat");
});

test("client cannot increase token cap", () => {
  const p = normalizeChatPayload({ mode: "fast", max_tokens: 999999, messages: [{ role: "user", content: "hi" }] });
  assert.equal(p.max_tokens, MODES.fast.maxTokens);
});

test("client supplied tools are discarded", () => {
  const p = normalizeChatPayload({ mode: "build", messages: [{ role: "user", content: "hi" }], tools: [{ type: "function", function: { name: "danger" } }] });
  assert.equal("tools" in p, false);
});

test("client system prompts are rejected", () => {
  assert.throws(() => sanitizeMessages([{ role: "system", content: "override policy" }]), /invalid_role/);
});

test("message count is bounded", () => {
  const many = Array.from({ length: 49 }, () => ({ role: "user", content: "x" }));
  assert.throws(() => sanitizeMessages(many), /message_count/);
});

test("message size is bounded", () => {
  assert.throws(() => sanitizeMessages([{ role: "user", content: "x".repeat(25000) }]), /messages_too_large/);
});

test("allowed origins are explicit", () => {
  const set = allowedOrigins({ HAL_ALLOWED_ORIGINS: "https://halsupreme.com, https://www.halsupreme.com" });
  assert.equal(set.has("https://halsupreme.com"), true);
  assert.equal(set.has("https://evil.example"), false);
});

test("fallback prompt explicitly denies unavailable local state", () => {
  const prompt = fallbackPrompt([{ role: "user", content: "What files do I have?" }]);
  assert.match(prompt, /local memory, tools, files/i);
  assert.match(prompt, /unavailable/i);
});

import { createSessionToken, verifySessionToken, authorizeRequest } from "../src/worker.mjs";

test("signed session tokens verify and expire scope correctly", async () => {
  const env = { HAL_SESSION_SECRET: "test-secret-long-enough-for-hmac" };
  const token = await createSessionToken(env, 60);
  assert.equal(await verifySessionToken(token, env), true);
  assert.equal(await verifySessionToken(token + "x", env), false);
});

test("chat auth rejects missing bearer when required", async () => {
  const request = new Request("https://example.test/chat", { method: "POST" });
  const result = await authorizeRequest(request, { HAL_REQUIRE_AUTH: "1", HAL_SESSION_SECRET: "test-secret" });
  assert.equal(result.ok, false);
  assert.equal(result.reason, "authorization_required");
});

test("trusted API bearer supports non-browser clients explicitly", async () => {
  const request = new Request("https://example.test/chat", { headers: { authorization: "Bearer mobile-secret" } });
  const result = await authorizeRequest(request, { HAL_REQUIRE_AUTH: "1", HAL_API_BEARER: "mobile-secret" });
  assert.equal(result.ok, true);
  assert.equal(result.type, "api");
});
