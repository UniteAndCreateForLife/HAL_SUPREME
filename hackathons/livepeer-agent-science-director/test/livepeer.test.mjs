import test from "node:test";
import assert from "node:assert/strict";
import { LivepeerMcpClient, extractJobId, extractMediaUrl, extractStatus } from "../lib/livepeer.mjs";

test("extractors read structured Livepeer tool results", () => {
  const payload = { result: { structuredContent: { job_id: "mjob_123", status: "completed", url: "https://cdn.example/test.mp4" } } };
  assert.equal(extractJobId(payload), "mjob_123");
  assert.equal(extractStatus(payload), "completed");
  assert.equal(extractMediaUrl(payload), "https://cdn.example/test.mp4");
});

test("client initializes once and sends bearer server-side", async () => {
  const calls = [];
  const fakeFetch = async (_url, init) => {
    calls.push(init);
    return {
      ok: true,
      status: 200,
      headers: { get: () => "session-1" },
      text: async () => JSON.stringify({ result: { content: [{ text: "ok" }] } })
    };
  };
  const client = new LivepeerMcpClient({ endpoint: "https://example.test/mcp", bearer: "sk_secret", fetchImpl: fakeFetch });
  await client.callTool("run_capability", { capability: "gemini-text" });
  assert.equal(calls.length, 2);
  assert.equal(calls[0].headers.authorization, "Bearer sk_secret");
  assert.equal(calls[1].headers["mcp-session-id"], "session-1");
});
