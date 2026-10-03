import { pathToFileURL } from "node:url";
import path from "node:path";
import fs from "node:fs/promises";

async function loadPlaywright() {
  try {
    return await import("playwright");
  } catch (first) {
    try {
      return await import("@playwright/test");
    } catch (second) {
      throw new Error("Playwright is required. Install playwright or @playwright/test and a Chromium browser.");
    }
  }
}

const htmlPath = process.argv[2];
const outputPath = process.argv[3] || "evidence-replay.webm";
const timeoutMs = Number(process.argv[4] || "600000");

if (!htmlPath) {
  throw new Error("Usage: node scripts/record_evidence_replay.mjs <replay.html> [output.webm] [timeout_ms]");
}

const pw = await loadPlaywright();
const chromium = pw.chromium;
const output = path.resolve(outputPath);
const videoDir = path.resolve(path.dirname(output), ".playwright-video");
await fs.mkdir(videoDir, { recursive: true });

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  viewport: { width: 1920, height: 1080 },
  recordVideo: {
    dir: videoDir,
    size: { width: 1920, height: 1080 }
  }
});
const page = await context.newPage();
const video = page.video();
const url = pathToFileURL(path.resolve(htmlPath));
url.searchParams.set("autoplay", "1");
url.searchParams.set("speed", "1");

await page.goto(url.href, { waitUntil: "load" });
await page.waitForFunction(
  () => document.body.dataset.replayDone === "true",
  null,
  { timeout: timeoutMs }
);
await page.waitForTimeout(700);
await page.close();
await context.close();

if (!video) {
  await browser.close();
  throw new Error("Playwright did not create a video object.");
}
await video.saveAs(output);
await browser.close();
console.log(output);
