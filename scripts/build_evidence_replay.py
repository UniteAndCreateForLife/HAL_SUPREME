from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from typing import Any


_PRIVATE_PATH_KEYS = {"source_path", "session_dir", "cwd"}
_WINDOWS_PATH = re.compile(r"(?i)\b[A-Z]:\\(?:Users|Documents and Settings)\\[^\\\s]+")
_UNIX_HOME_PATH = re.compile(r"/(?:home|Users)/[^/\s]+")


def _sanitize_replay(value: Any, key: str | None = None) -> Any:
    if isinstance(value, dict):
        return {str(k): _sanitize_replay(v, str(k)) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize_replay(item) for item in value]
    if isinstance(value, str):
        if key in _PRIVATE_PATH_KEYS:
            name = Path(value).name
            return f"[LOCAL_PATH]/{name}" if name else "[LOCAL_PATH]"
        text = _WINDOWS_PATH.sub("[LOCAL_HOME]", value)
        text = _UNIX_HOME_PATH.sub("[LOCAL_HOME]", text)
        return text
    return value


def _load_events(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                events.append(json.loads(line))
    return events


def _display_ms(kind: str) -> int:
    if kind.startswith("artifact."):
        return 3200
    if kind in {"session.start", "session.end", "process.launch", "process.exited"}:
        return 2200
    if "failed" in kind or kind.endswith("stderr"):
        return 1800
    if kind == "process.metric":
        return 700
    return 1000


def _condense(events: list[dict[str, Any]], bucket_ms: int = 1800) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    bucket: list[dict[str, Any]] = []
    bucket_start: int | None = None
    last_metric_at = -10_000

    def flush() -> None:
        nonlocal bucket, bucket_start
        if not bucket:
            return
        lines = [str(item.get("message") or "") for item in bucket if item.get("message")]
        if lines:
            lines = lines[-10:]
            output.append({
                "seq": f"{bucket[0]['seq']}-{bucket[-1]['seq']}",
                "elapsed_ms": bucket[-1].get("elapsed_ms", 0),
                "kind": "process.output",
                "source": bucket[-1].get("source"),
                "phase": "execute",
                "message": "\n".join(lines),
                "data": {
                    "source_seq_start": bucket[0]["seq"],
                    "source_seq_end": bucket[-1]["seq"],
                    "source_event_count": len(bucket),
                },
            })
        bucket = []
        bucket_start = None

    for event in events:
        kind = str(event.get("kind") or "")
        elapsed = int(event.get("elapsed_ms") or 0)
        if kind in {"process.stdout", "process.stderr"}:
            if bucket_start is None:
                bucket_start = elapsed
            if bucket and elapsed - bucket_start >= bucket_ms:
                flush()
                bucket_start = elapsed
            bucket.append(event)
            continue

        flush()
        if kind == "process.metric":
            if elapsed - last_metric_at < 5000:
                continue
            last_metric_at = elapsed
        output.append(dict(event))

    flush()
    return output


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__ — HAL Evidence Replay</title>
<style>
:root { color-scheme: dark; font-family: Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif; }
* { box-sizing: border-box; }
body { margin: 0; background: #07090d; color: #f1f5f9; overflow: hidden; }
#app { width: 100vw; height: 100vh; display: grid; grid-template-rows: 70px 1fr 54px; }
header { display: flex; align-items: center; justify-content: space-between; padding: 0 34px; border-bottom: 1px solid #202633; background: #0b0f15; }
.brand { font-weight: 800; letter-spacing: .08em; font-size: 18px; }
.meta { font: 13px ui-monospace, SFMono-Regular, Consolas, monospace; color: #9aa7b7; }
main { display: grid; grid-template-columns: 29% 71%; min-height: 0; }
.timeline { border-right: 1px solid #202633; padding: 22px; overflow: hidden; background: #090c11; }
.timeline h2 { margin: 0 0 14px; font-size: 14px; color: #8fa1b7; letter-spacing: .12em; }
#events { height: calc(100% - 34px); overflow: hidden; }
.ev { padding: 8px 10px; margin-bottom: 5px; border-left: 2px solid #2c3443; color: #6f7d90; font: 12px ui-monospace, SFMono-Regular, Consolas, monospace; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ev.active { color: #f8fafc; border-left-color: #f8fafc; background: #121722; }
.stage { padding: 44px 54px; display: grid; grid-template-rows: auto auto 1fr; gap: 18px; min-width: 0; }
.kicker { font: 13px ui-monospace, SFMono-Regular, Consolas, monospace; letter-spacing: .14em; color: #8fa1b7; }
h1 { font-size: 40px; line-height: 1.08; margin: 0; max-width: 1200px; }
#message { white-space: pre-wrap; font: 20px/1.45 ui-monospace, SFMono-Regular, Consolas, monospace; color: #dbe4ef; max-height: 190px; overflow: hidden; }
.content { display: grid; grid-template-columns: 1fr 1fr; gap: 22px; min-height: 0; }
pre { margin: 0; padding: 18px; border: 1px solid #222b39; background: #0b1017; border-radius: 12px; overflow: hidden; white-space: pre-wrap; word-break: break-word; font: 13px/1.45 ui-monospace, SFMono-Regular, Consolas, monospace; color: #aebcd0; }
.media { border: 1px solid #222b39; background: #030506; border-radius: 12px; display: flex; align-items: center; justify-content: center; overflow: hidden; min-height: 0; }
.media img, .media video { width: 100%; height: 100%; object-fit: contain; }
.media audio { width: 90%; }
.placeholder { color: #4d596a; font-size: 14px; text-align: center; padding: 30px; }
footer { display: grid; grid-template-columns: 1fr auto; align-items: center; padding: 0 34px; border-top: 1px solid #202633; background: #0b0f15; }
.truth { color: #9aa7b7; font-size: 12px; letter-spacing: .09em; }
#progress { font: 13px ui-monospace, SFMono-Regular, Consolas, monospace; color: #dbe4ef; }
</style>
</head>
<body data-replay-done="false">
<div id="app">
<header>
  <div class="brand">HAL EVIDENCE REPLAY</div>
  <div class="meta" id="session"></div>
</header>
<main>
  <aside class="timeline"><h2>HASH-CHAINED EVENT TIMELINE</h2><div id="events"></div></aside>
  <section class="stage">
    <div class="kicker" id="kicker"></div>
    <h1 id="kind"></h1>
    <div id="message"></div>
    <div class="content">
      <pre id="data"></pre>
      <div class="media" id="media"><div class="placeholder">No registered visual artifact for this event.</div></div>
    </div>
  </section>
</main>
<footer>
  <div class="truth">TELEMETRY REPLAY • DERIVED FROM RECORDED EVENTS • NOT A SCREEN CAPTURE</div>
  <div id="progress"></div>
</footer>
</div>
<script>
const MANIFEST = __MANIFEST__;
const EVENTS = __EVENTS__;
const params = new URLSearchParams(location.search);
const autoplay = params.get("autoplay") === "1";
const speed = Math.max(0.1, Number(params.get("speed") || "1"));
let index = 0;
let timer = null;

document.getElementById("session").textContent = MANIFEST.session_id + " • " + (MANIFEST.source || "unknown");
const eventsEl = document.getElementById("events");
EVENTS.forEach(function(ev, i) {
  const node = document.createElement("div");
  node.className = "ev";
  node.id = "event-" + i;
  node.textContent = String(ev.seq) + "  " + ev.kind;
  eventsEl.appendChild(node);
});

function mediaFor(ev) {
  const box = document.getElementById("media");
  box.innerHTML = "";
  const data = ev.data || {};
  const path = data.stored_path;
  const mime = String(data.mime_type || "");
  if (!path) {
    box.innerHTML = '<div class="placeholder">No registered visual artifact for this event.</div>';
    return;
  }
  let node = null;
  if (mime.startsWith("image/")) {
    node = document.createElement("img");
    node.src = path;
  } else if (mime.startsWith("video/")) {
    node = document.createElement("video");
    node.src = path;
    node.autoplay = true;
    node.muted = true;
    node.loop = true;
    node.playsInline = true;
  } else if (mime.startsWith("audio/")) {
    node = document.createElement("audio");
    node.src = path;
    node.controls = true;
    node.autoplay = true;
  }
  if (node) box.appendChild(node);
  else box.innerHTML = '<div class="placeholder">Registered artifact: ' + path + '</div>';
}

function render(i) {
  index = i;
  const ev = EVENTS[i];
  document.querySelectorAll(".ev.active").forEach(function(n){ n.classList.remove("active"); });
  const active = document.getElementById("event-" + i);
  if (active) {
    active.classList.add("active");
    active.scrollIntoView({block: "center"});
  }
  document.getElementById("kicker").textContent =
    "SEQ " + String(ev.seq) + " • " + String(ev.phase || "event") + " • " +
    ((Number(ev.elapsed_ms || 0) / 1000).toFixed(2)) + "s";
  document.getElementById("kind").textContent = ev.kind;
  document.getElementById("message").textContent = ev.message || "";
  document.getElementById("data").textContent = JSON.stringify(ev.data || {}, null, 2);
  document.getElementById("progress").textContent = String(i + 1) + " / " + String(EVENTS.length);
  mediaFor(ev);
}

function advance() {
  if (index >= EVENTS.length - 1) {
    document.body.dataset.replayDone = "true";
    return;
  }
  index += 1;
  render(index);
  schedule();
}

function schedule() {
  if (!autoplay) return;
  const ms = Math.max(120, Number(EVENTS[index].display_ms || 1000) / speed);
  timer = setTimeout(advance, ms);
}

if (EVENTS.length) {
  render(0);
  schedule();
} else {
  document.body.dataset.replayDone = "true";
}
</script>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a visual telemetry replay from a HAL evidence session.")
    parser.add_argument("session_dir", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--full", action="store_true", help="Show every raw event instead of a condensed replay.")
    parser.add_argument("--show-local-paths", action="store_true", help="Do not mask local filesystem paths in the replay.")
    args = parser.parse_args()

    session_dir = args.session_dir.expanduser().resolve()
    manifest = json.loads((session_dir / "manifest.json").read_text(encoding="utf-8"))
    raw_events = _load_events(session_dir / "events.jsonl")
    events = raw_events if args.full else _condense(raw_events)
    if not args.show_local_paths:
        events = [_sanitize_replay(event) for event in events]
        manifest = _sanitize_replay(manifest)
    for event in events:
        event["display_ms"] = _display_ms(str(event.get("kind") or ""))

    output = (args.output or (session_dir / "replay.html")).expanduser().resolve()
    title = html.escape(str(manifest.get("title") or "HAL evidence session"))
    document = TEMPLATE
    document = document.replace("__TITLE__", title)
    document = document.replace("__MANIFEST__", json.dumps(manifest, ensure_ascii=False).replace("</", "<\\/"))
    document = document.replace("__EVENTS__", json.dumps(events, ensure_ascii=False).replace("</", "<\\/"))
    output.write_text(document, encoding="utf-8")

    replay_source = {
        "session_id": manifest.get("session_id"),
        "raw_event_count": len(raw_events),
        "display_event_count": len(events),
        "mode": "full" if args.full else "condensed",
        "output": str(output),
    }
    (session_dir / "replay.receipt.json").write_text(
        json.dumps(replay_source, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
