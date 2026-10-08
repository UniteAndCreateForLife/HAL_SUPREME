import fs from "node:fs/promises";
import path from "node:path";
import crypto from "node:crypto";

async function loadPlaywright() {
  try {
    return await import("playwright");
  } catch (first) {
    try {
      return await import("@playwright/test");
    } catch (second) {
      throw new Error("Playwright is required. Install playwright or @playwright/test and Chromium.");
    }
  }
}

function emit(kind, data = {}) {
  process.stdout.write(JSON.stringify({
    kind,
    ts_utc: new Date().toISOString(),
    ...data
  }) + "\n");
}

const planPath = process.argv[2];
const outputDirArg = process.argv[3] || "browser-capture";
if (!planPath) {
  throw new Error("Usage: node scripts/record_browser_plan.mjs <plan.json> [output-dir]");
}

const planText = await fs.readFile(planPath, "utf8");
const plan = JSON.parse(planText);
const outputDir = path.resolve(outputDirArg);
await fs.mkdir(outputDir, { recursive: true });
const videoDir = path.join(outputDir, ".video");
await fs.mkdir(videoDir, { recursive: true });

const pw = await loadPlaywright();
const viewport = plan.viewport || { width: 1440, height: 900 };
const browser = await pw.chromium.launch({ headless: true });
const context = await browser.newContext({
  viewport,
  recordVideo: { dir: videoDir, size: viewport }
});

await context.tracing.start({
  screenshots: true,
  snapshots: true,
  sources: false
});

const page = await context.newPage();
const video = page.video();
page.on("console", msg => emit("browser.console", { level: msg.type(), text: msg.text() }));
page.on("pageerror", err => emit("browser.pageerror", { message: String(err) }));

emit("browser.start", {
  title: plan.title || "browser capture",
  viewport,
  plan_sha256: crypto.createHash("sha256").update(planText).digest("hex")
});

for (let i = 0; i < (plan.actions || []).length; i += 1) {
  const action = plan.actions[i];
  const common = { index: i, type: action.type, selector: action.selector || null };
  emit("browser.action.start", common);

  switch (action.type) {
    case "goto":
      await page.goto(action.url, { waitUntil: action.waitUntil || "load" });
      break;
    case "click":
      await page.locator(action.selector).click();
      break;
    case "fill":
      await page.locator(action.selector).fill(action.value || "");
      break;
    case "press":
      await page.locator(action.selector).press(action.key);
      break;
    case "wait":
      await page.waitForTimeout(Number(action.ms || 1000));
      break;
    case "waitFor":
      await page.locator(action.selector).waitFor({
        state: action.state || "visible",
        timeout: Number(action.timeoutMs || 30000)
      });
      break;
    case "screenshot": {
      const name = action.name || ("step-" + String(i + 1).padStart(3, "0") + ".png");
      const target = path.join(outputDir, name);
      await page.screenshot({ path: target, fullPage: Boolean(action.fullPage) });
      emit("browser.screenshot", { index: i, path: target });
      break;
    }
    default:
      throw new Error("Unsupported browser action type: " + action.type);
  }

  emit("browser.action.end", common);
}

const tracePath = path.join(outputDir, "trace.zip");
await context.tracing.stop({ path: tracePath });
emit("browser.trace", { path: tracePath });

await page.close();
await context.close();

if (!video) {
  await browser.close();
  throw new Error("Playwright did not create a video object.");
}
const videoPath = path.join(outputDir, "browser.webm");
await video.saveAs(videoPath);
await browser.close();

const receipt = {
  schema_version: 1,
  title: plan.title || "browser capture",
  plan_sha256: crypto.createHash("sha256").update(planText).digest("hex"),
  video: "browser.webm",
  trace: "trace.zip",
  viewport,
  actions: (plan.actions || []).length,
  completed_at: new Date().toISOString()
};
await fs.writeFile(path.join(outputDir, "browser.receipt.json"), JSON.stringify(receipt, null, 2) + "\n");
emit("browser.end", receipt);
