const MEDIA_LABELS = {
  image: "single scientific keyframe",
  video: "short scientific video shot"
};

export function normalizeBrief(input = {}) {
  const concept = clean(input.concept, 500);
  if (!concept) throw new Error("A scientific concept is required.");

  const mediaType = input.mediaType === "video" ? "video" : "image";
  const aspectRatio = ["16:9", "9:16", "1:1"].includes(input.aspectRatio) ? input.aspectRatio : "16:9";
  const durationSeconds = mediaType === "video" ? clamp(Number(input.durationSeconds) || 6, 3, 12) : undefined;
  const audience = clean(input.audience, 120) || "curious general audience";
  const style = clean(input.style, 180) || "cinematic photoreal scientific visualization";
  const accuracyNotes = clean(input.accuracyNotes, 700);
  const feedback = clean(input.feedback, 700);

  return { concept, mediaType, aspectRatio, durationSeconds, audience, style, accuracyNotes, feedback };
}

export function buildPlannerPrompt(brief) {
  return [
    "You are the scientific shot-planning module for HAL Science Director.",
    "Return ONLY valid JSON, no markdown, with keys: title, observable_claim, visual_subject, camera, environment, motion, exclusions, accuracy_guardrails, render_prompt.",
    `Goal: plan one ${MEDIA_LABELS[brief.mediaType]} that teaches the concept accurately enough to be useful, while remaining visually compelling.`,
    `Scientific concept: ${brief.concept}`,
    `Audience: ${brief.audience}`,
    `Style: ${brief.style}`,
    `Aspect ratio: ${brief.aspectRatio}`,
    ...(brief.durationSeconds ? [`Duration: ${brief.durationSeconds} seconds`] : []),
    ...(brief.accuracyNotes ? [`Accuracy constraints supplied by the operator: ${brief.accuracyNotes}`] : []),
    ...(brief.feedback ? [`Corrections from the previous attempt that MUST be addressed: ${brief.feedback}`] : []),
    "Rules: depict only observables or clearly labeled scientific abstractions; do not invent instruments, measurements, labels, scales, causal mechanisms, or numerical values; avoid decorative pseudo-data; state exclusions explicitly; make the final render_prompt self-contained and production-ready."
  ].join("\n");
}

export function buildRenderPrompt(plan, brief) {
  const core = typeof plan?.render_prompt === "string" ? plan.render_prompt : brief.concept;
  const guardrails = list(plan?.accuracy_guardrails);
  const exclusions = list(plan?.exclusions);
  return [
    core,
    `Format: ${brief.aspectRatio}${brief.durationSeconds ? `, ${brief.durationSeconds}s` : ""}.`,
    "Scientific fidelity is more important than spectacle.",
    guardrails ? `Accuracy guardrails: ${guardrails}.` : "",
    exclusions ? `Do not show: ${exclusions}.` : "",
    "No captions, logos, fake HUD data, watermarks, or unreadable scientific text unless explicitly requested."
  ].filter(Boolean).join(" ");
}

export function parsePlannerJson(text) {
  const source = String(text || "").trim();
  const fenced = source.match(/```(?:json)?\s*([\s\S]*?)```/i)?.[1];
  const candidate = fenced || source;
  const start = candidate.indexOf("{");
  const end = candidate.lastIndexOf("}");
  if (start < 0 || end <= start) throw new Error("Planner did not return JSON.");
  const parsed = JSON.parse(candidate.slice(start, end + 1));
  return {
    title: clean(parsed.title, 160) || "Untitled science shot",
    observable_claim: clean(parsed.observable_claim, 500),
    visual_subject: clean(parsed.visual_subject, 500),
    camera: clean(parsed.camera, 300),
    environment: clean(parsed.environment, 300),
    motion: clean(parsed.motion, 300),
    exclusions: normalizeList(parsed.exclusions),
    accuracy_guardrails: normalizeList(parsed.accuracy_guardrails),
    render_prompt: clean(parsed.render_prompt, 2400) || clean(parsed.visual_subject, 500)
  };
}

function normalizeList(value) {
  if (Array.isArray(value)) return value.map((item) => clean(item, 300)).filter(Boolean).slice(0, 12);
  if (typeof value === "string") return value.split(/[;\n]/).map((item) => clean(item, 300)).filter(Boolean).slice(0, 12);
  return [];
}

function list(value) {
  return normalizeList(value).join("; ");
}

function clean(value, max) {
  return String(value ?? "").replace(/[\u0000-\u001f]+/g, " ").replace(/\s+/g, " ").trim().slice(0, max);
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}
