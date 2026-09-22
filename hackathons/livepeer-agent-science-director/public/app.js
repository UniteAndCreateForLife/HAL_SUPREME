const form = document.querySelector("#director-form");
const refineForm = document.querySelector("#refine-form");
const mediaType = document.querySelector("#mediaType");
const durationWrap = document.querySelector("#durationWrap");
const stage = document.querySelector("#stage");
const planBox = document.querySelector("#plan");
const ledger = document.querySelector("#ledger");
const status = document.querySelector("#status");
const generateButton = document.querySelector("#generate");
let lastRunId = "";

mediaType.addEventListener("change", () => {
  durationWrap.style.opacity = mediaType.value === "video" ? "1" : ".35";
});
mediaType.dispatchEvent(new Event("change"));

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  await run("/api/direct", collectBrief());
});

refineForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const feedback = document.querySelector("#feedback").value.trim();
  if (!feedback || !lastRunId) return;
  await run("/api/refine", { previousRunId: lastRunId, feedback });
});

async function run(endpoint, payload) {
  busy(true, endpoint.includes("refine") ? "Replanning with correction…" : "Livepeer Agent is planning the shot…");
  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload)
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Generation failed.");
    lastRunId = result.id;
    renderResult(result);
    await refreshLedger();
  } catch (error) {
    stage.className = "stage error";
    stage.innerHTML = `<div><strong>Generation did not complete.</strong><p>${escapeHtml(error.message)}</p></div>`;
  } finally {
    busy(false);
  }
}

function collectBrief() {
  return {
    concept: value("concept"),
    mediaType: value("mediaType"),
    aspectRatio: value("aspectRatio"),
    durationSeconds: Number(value("durationSeconds")),
    audience: value("audience"),
    style: value("style"),
    accuracyNotes: value("accuracyNotes")
  };
}

function renderResult(run) {
  const url = run.livepeer.outputUrl;
  const isVideo = run.brief.mediaType === "video";
  stage.className = "stage ready";
  stage.innerHTML = isVideo
    ? `<video src="${escapeAttr(url)}" controls autoplay loop muted playsinline></video>`
    : `<img src="${escapeAttr(url)}" alt="Generated scientific visualization" />`;

  planBox.classList.remove("hidden");
  planBox.innerHTML = `
    <h2>${escapeHtml(run.plan.title)}</h2>
    <p><b>Observable claim.</b> ${escapeHtml(run.plan.observable_claim || "—")}</p>
    <p><b>Camera.</b> ${escapeHtml(run.plan.camera || "—")}</p>
    <p><b>Accuracy guardrails.</b> ${escapeHtml((run.plan.accuracy_guardrails || []).join(" · ") || "—")}</p>
    <details><summary>Exact render prompt</summary><p>${escapeHtml(run.renderPrompt)}</p></details>`;
  refineForm.classList.remove("hidden");
}

async function refreshLedger() {
  const response = await fetch("/api/runs");
  const { runs = [] } = await response.json();
  ledger.innerHTML = runs.length ? runs.map((run) => `
    <article class="receipt">
      <div><b>${escapeHtml(run.plan.title)}</b><span>${new Date(run.finishedAt).toLocaleTimeString()}</span></div>
      <p>${escapeHtml(run.brief.concept)}</p>
      <code>${escapeHtml(run.livepeer.textCapability)} → ${escapeHtml(run.livepeer.mediaCapability)}</code>
      <code>sha256:${escapeHtml(run.provenanceHash.slice(0, 24))}…</code>
    </article>`).join("") : `<p class="muted">No attempts yet.</p>`;
}

async function health() {
  try {
    const response = await fetch("/api/health");
    const data = await response.json();
    status.classList.toggle("ok", data.ok);
    status.innerHTML = `<span></span> ${data.authMode === "bearer" ? "Livepeer authenticated" : "Livepeer keyless demo"}`;
  } catch {
    status.textContent = "offline";
  }
}

function busy(on, message = "") {
  generateButton.disabled = on;
  refineForm.querySelector("button").disabled = on;
  if (on) {
    stage.className = "stage loading";
    stage.innerHTML = `<div class="spinner"></div><p>${escapeHtml(message)}</p>`;
  }
}

function value(id) { return document.getElementById(id).value; }
function escapeHtml(value) { return String(value ?? "").replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#039;"}[c])); }
function escapeAttr(value) { return escapeHtml(value); }

health();
refreshLedger();
