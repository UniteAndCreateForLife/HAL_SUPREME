"""Download the SIGNAL SPLIT media from the Livepeer Agent receipts, so the edit can be rebuilt without re-rendering.

Usage: python tools/fetch_media.py [receipts/livepeer_calls.json]

Every generation call is in the receipt with its idempotency key and output URL. The key names the file: song takes go
to song/, keyframes to keyframes/, Kling shots to shots/, lip-sync clips to performance/, the cut-out title to titles/.
Livepeer asset URLs inherit the provider's lifetime, so a URL may expire; the receipt still records what was made."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
TAKES = {"take1": "A_glitch_trap", "take2": "B_glitch_trap", "emo-take3": "C_emo_trap", "emo-take4": "D_emo_trap"}


def target(key: str) -> Path | None:
    if match := re.match(r"signal-split-song-(take1|take2|emo-take3|emo-take4)-", key):
        return HERE / "song" / f"{TAKES[match.group(1)]}.wav"
    if match := re.match(r"signal-split-k(\d\d)-", key):
        return HERE / "keyframes" / f"K{match.group(1)}.png"
    if match := re.match(r"signal-split-v(\d\d)-", key):
        return HERE / "shots" / f"V{match.group(1)}.mp4"
    if match := re.match(r"signal-split-perf-(\w+?)-2026", key):
        return HERE / "performance" / f"P_{match.group(1)}.mp4"
    if match := re.match(r"signal-split-pk-(\w+?)-2026", key):
        return HERE / "performance" / f"PK_{match.group(1)}.jpg"
    if key.startswith("signal-split-title-gothic-alpha-"):
        return HERE / "titles" / "title_gothic_alpha.png"
    return None


def main(receipt: Path) -> list[str]:
    fetched = []
    for call in json.loads(receipt.read_text(encoding="utf-8")):
        path, url = target(call.get("idempotency_key") or ""), call.get("url")
        if not path or not url or path.exists():
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = path.with_suffix(Path(url.split("?")[0]).suffix or path.suffix)
        subprocess.run(["curl", "-sSLf", "-o", str(raw), url], check=True)
        if raw != path:  # a song take arrives as mp3 and the edit reads wav
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(raw), str(path)], check=True)
            raw.unlink()
        fetched.append(str(path.relative_to(HERE)))
    return fetched


if __name__ == "__main__":
    print(json.dumps(main(Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "receipts" / "livepeer_calls.json"), indent=1))
