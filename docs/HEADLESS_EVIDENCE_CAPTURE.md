# HAL Headless Evidence Capture

## Why screen recording is not enough

A headless process may have no desktop surface to record. Treating that as a capture failure is the wrong abstraction.

HAL should capture **what actually happened** at the process, browser, renderer, engine, model, artifact, and verification layers, then produce a clearly labeled visual replay from that evidence.

The rule is:

**capture truth first; express it second.**

The raw evidence is durable and complete. The review video is a derived editorial view, not the source of truth.

## Evidence classes

Every visual used in a HAL technical demo should be attributable to one of these classes:

1. **ACTUAL SCREEN CAPTURE** — pixels recorded from a real visible UI.
2. **ENGINE / BROWSER RENDER** — pixels produced directly by a headless engine or browser.
3. **PROVIDER ARTIFACT** — a real image, video, audio, or 3D artifact returned by a model/provider job and registered with provenance.
4. **TELEMETRY REPLAY** — a deterministic visualization of recorded events, logs, metrics, artifacts, and receipts.
5. **GENERATED ILLUSTRATION** — synthetic explanatory media that must never be presented as proof of a real process.

This classification should be visible in review tooling and retained in the shot manifest.

## Core recorder

scripts/record_headless.py wraps an arbitrary command without requiring a GUI. It records:

- command launch and PID;
- stdout and stderr with timestamps;
- exit status;
- optional per-process CPU, memory, I/O and thread samples when psutil is installed;
- semantic events emitted by child HAL components;
- declared output artifacts;
- SHA-256 for registered artifacts;
- a hash chain across every evidence event;
- a manifest describing the session.

The wrapper exports HAL_EVIDENCE_SESSION_DIR to the child process. HAL-aware children can therefore join the same evidence session instead of creating disconnected logs.

Example:

    python scripts/record_headless.py \
      --root evidence/runtime \
      --title "Science Director render" \
      --source comfyui \
      --artifact render=artifacts/**/*.mp4 \
      -- python scripts/canary_render.py \
         --workflow configs/workflows/wan_api.json \
         --bindings configs/workflows/wan_bindings.json \
         --output-node 42

## Attach to processes that are already running

Some HAL services are already alive before a recording session begins. You cannot reliably recover another process's original stdout after the fact, but HAL can still attach an observer to the PID and record live process metrics plus any logs that service is already writing.

Example:

    python scripts/observe_headless.py       --pid 12345       --duration 120       --tail-log D:/HAL_SUPREME/logs/worker.log       --artifact output=artifacts/**/*.mp4

This produces the same hash-chained evidence format as the launch wrapper. If the target service also emits semantic events through HAL_EVIDENCE_SESSION_DIR or the event CLI, the replay combines both sources.

For long-lived services, the preferred design is to start them under the recorder or add native EvidenceSession/OpenTelemetry instrumentation so the system has semantic events from process start rather than only attach-time metrics.

## Semantic events from any process

Python components can use EvidenceSession.from_env().

Shell scripts, PowerShell, batch files, or other languages can call:

    python scripts/evidence_event.py phase.start "Planning scientific shot" --phase plan

Register a produced artifact:

    python scripts/evidence_event.py artifact \
      --artifact artifacts/shot-001/render.mp4 \
      --role render_candidate

Secrets are redacted before events are written. The evidence hash chain covers the redacted record that HAL actually stores.

## ComfyUI

The HAL ComfyUI renderer now joins the active evidence session automatically when HAL_EVIDENCE_SESSION_DIR exists.

It records:

- renderer request;
- task and shot identity;
- prompt;
- requested dimensions, FPS, frame count and seed;
- bound workflow SHA-256;
- ComfyUI prompt ID;
- output discovery;
- downloaded candidate artifact and SHA-256;
- timeout if the render does not complete.

The next ComfyUI adapter upgrade should consume its WebSocket stream so node progress and preview frames become additional evidence. ComfyUI's own examples expose execution messages through the WebSocket and binary preview frames during generation.

## Browser / web agents

For browser automation, do not synthesize a browser window after the fact.

Use Playwright in headless mode with:

- recordVideo for real browser pixels;
- tracing with screenshots and DOM snapshots;
- console/page-error capture;
- network metadata where appropriate;
- screenshots at explicit semantic checkpoints.

The real browser video is an **ENGINE / BROWSER RENDER** artifact. The trace is debugging/evidence data. Both can be registered in the same HAL evidence session.

## Godot and other engines

Godot can write a movie directly while running headlessly. This is better evidence than filming a desktop window because it records the actual engine output deterministically.

Typical pattern:

    python scripts/record_headless.py \
      --title "Godot proof run" \
      --source godot \
      --artifact engine_movie=proof.avi \
      --artifact engine_log=godot.log \
      -- godot --headless --log-file godot.log \
         --write-movie proof.avi --fixed-fps 24 --quit-after 120

Register the resulting movie and log as first-class artifacts.

## Model and agent work

Agents and model workers should emit semantic events around consequential steps:

- goal accepted;
- plan created;
- tool selected;
- model/provider selected;
- request submitted;
- response received;
- verification passed or failed;
- retry/correction;
- artifact promoted or rejected.

Do not record hidden chain-of-thought. Record inspectable decisions, inputs that are safe to retain, outputs, tool receipts, measurements, and verification results.

For services already instrumented with OpenTelemetry, map spans and span events into the same evidence schema instead of inventing another observability system.

## Visual replay

Raw JSONL is complete but poor video.

Create a condensed replay:

    python scripts/build_evidence_replay.py evidence/runtime/<session>

The generated replay.html shows:

- the hash-chained event timeline;
- elapsed process time;
- semantic phase;
- recorded message;
- structured evidence;
- registered image/video/audio artifacts when copied into the session.

It is permanently labeled:

TELEMETRY REPLAY • DERIVED FROM RECORDED EVENTS • NOT A SCREEN CAPTURE

That distinction prevents a polished visualization from being confused with literal UI footage.

If Playwright is available, turn the replay into a 1920x1080 headless recording:

    node scripts/record_evidence_replay.mjs \
      evidence/runtime/<session>/replay.html \
      evidence/runtime/<session>/replay.webm

A deterministic FFmpeg finishing stage may then combine:

- actual UI/browser video;
- headless engine output;
- ComfyUI preview/final artifacts;
- telemetry replay segments;
- narration;
- titles;
- receipts and verification.

## Verification

Verify the evidence chain before using a replay as proof:

    python scripts/verify_evidence_session.py evidence/runtime/<session>

If any stored event is modified, reordered, removed from the middle, or has a broken predecessor hash, verification fails.

The evidence session should be verified again after production and before a review video is promoted.

## Pipeline integration

For a HAL work order:

1. Create one evidence session.
2. Launch the headless process under the recorder.
3. Let child services join through HAL_EVIDENCE_SESSION_DIR.
4. Register all meaningful artifacts.
5. Finalize the session.
6. Verify the hash chain.
7. Run artifact-specific QC.
8. Build the telemetry replay.
9. Assemble the final review film from real visual artifacts plus clearly labeled replay segments.
10. Feed rejected shots and process failures back into the after-action improvement loop.

This gives HAL something stronger than "record my screen": a reusable black-box flight recorder for autonomous work.
