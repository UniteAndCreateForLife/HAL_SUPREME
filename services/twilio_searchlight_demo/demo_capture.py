from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

SOURCE_SHA_RE = re.compile(r"[0-9a-f]{40}\Z")
FRAME_RATE = 30
WIDTH = 1280
HEIGHT = 720


@dataclass(frozen=True)
class Scene:
    anchor: str
    caption: str
    duration_seconds: int = 6


SCENES = (
    Scene("", "HAL operator control through Twilio Messaging."),
    Scene(
        "boundary-title",
        "Local technical rehearsal — not a live Twilio interaction.",
    ),
    Scene(
        "story-title",
        "One bounded operator story, persona, and outcome.",
    ),
    Scene(
        "architecture-title",
        "Signed webhook to canonical HAL Operator Gateway to TwiML.",
    ),
    Scene(
        "criteria-title",
        "Technical evidence mapped to the published judging criteria.",
    ),
    Scene(
        "state-title",
        "Live demo, application, award, and payment remain unverified.",
    ),
)


def current_source_sha() -> str:
    repo_root = Path(__file__).resolve().parents[2]
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repo_root, text=True
    ).strip()


def validate_html(html: str, source_sha: str) -> None:
    if not SOURCE_SHA_RE.fullmatch(source_sha):
        raise ValueError("source SHA must be 40 lowercase hexadecimal characters")
    if source_sha not in html:
        raise ValueError("judge report source SHA does not match capture source")
    if "LIVE TWILIO NOT VERIFIED" not in html or "NOT VERIFIED" not in html:
        raise ValueError("judge report live boundary is missing")
    for anchor in (scene.anchor for scene in SCENES if scene.anchor):
        if f'id="{anchor}"' not in html:
            raise ValueError(f"judge report anchor is missing: {anchor}")


def render_scene_html(html: str, scene: Scene) -> str:
    if not scene.anchor:
        return html
    style = (
        "<style>"
        "header,footer,main>section{display:none!important}"
        f'main>section[aria-labelledby="{scene.anchor}"]'
        "{display:block!important}"
        "</style>"
    )
    if "</head>" not in html:
        raise ValueError("judge report head is missing")
    return html.replace("</head>", style + "</head>", 1)


def _srt_time(seconds: int) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},000"


def render_srt(scenes: tuple[Scene, ...]) -> str:
    elapsed = 0
    blocks: list[str] = []
    for index, scene in enumerate(scenes, start=1):
        end = elapsed + scene.duration_seconds
        blocks.append(
            f"{index}\n{_srt_time(elapsed)} --> {_srt_time(end)}\n{scene.caption}\n"
        )
        elapsed = end
    return "\n".join(blocks)


def build_ffmpeg_command(
    ffmpeg: Path,
    screenshots: list[Path],
    output: Path,
) -> list[str]:
    if len(screenshots) != len(SCENES):
        raise ValueError("one screenshot is required for every capture scene")

    command = [str(ffmpeg), "-y"]
    filters: list[str] = []
    labels: list[str] = []
    for index, (screenshot, scene) in enumerate(zip(screenshots, SCENES)):
        command.extend(
            ["-loop", "1", "-t", str(scene.duration_seconds), "-i", str(screenshot)]
        )
        fade_out = max(scene.duration_seconds - 0.35, 0)
        label = f"v{index}"
        labels.append(f"[{label}]")
        filters.append(
            f"[{index}:v]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease,"
            f"pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2,"
            f"fps={FRAME_RATE},"
            f"fade=t=in:st=0:d=0.35,fade=t=out:st={fade_out}:d=0.35,"
            f"trim=duration={scene.duration_seconds},setpts=PTS-STARTPTS[{label}]"
        )
    filters.append("".join(labels) + f"concat=n={len(screenshots)}:v=1:a=0[outv]")
    command.extend(
        [
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[outv]",
            "-r",
            str(FRAME_RATE),
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            "-an",
            str(output),
        ]
    )
    return command


def capture_screenshots(
    browser: Path,
    html_path: Path,
    output_dir: Path,
) -> list[Path]:
    if not browser.is_file():
        raise FileNotFoundError(f"browser executable not found: {browser}")
    output_dir.mkdir(parents=True, exist_ok=True)
    source_html = html_path.read_text(encoding="utf-8")
    screenshots: list[Path] = []
    for index, scene in enumerate(SCENES, start=1):
        profile = output_dir / f".browser-profile-{index:02d}"
        profile.mkdir(parents=True, exist_ok=True)
        frame_html = profile / "scene.html"
        frame_html.write_text(
            render_scene_html(source_html, scene),
            encoding="utf-8",
            newline="\n",
        )
        browser_profile = profile / "browser"
        screenshot = output_dir / f"scene-{index:02d}.png"
        url = frame_html.resolve().as_uri()
        command = [
            str(browser),
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--no-first-run",
            "--no-default-browser-check",
            "--run-all-compositor-stages-before-draw",
            "--virtual-time-budget=1000",
            f"--user-data-dir={browser_profile}",
            f"--window-size={WIDTH},{HEIGHT}",
            f"--screenshot={screenshot}",
            url,
        ]
        subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=45,
        )
        if not screenshot.is_file() or screenshot.stat().st_size == 0:
            raise RuntimeError(f"browser did not create screenshot: {screenshot}")
        screenshots.append(screenshot)
        shutil.rmtree(profile, ignore_errors=True)
    return screenshots


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest(
    root: Path,
    output: Path,
    source_sha: str,
    files: list[Path],
) -> dict[str, object]:
    if not SOURCE_SHA_RE.fullmatch(source_sha):
        raise ValueError("source SHA must be 40 lowercase hexadecimal characters")
    records: dict[str, dict[str, object]] = {}
    for path in sorted(files):
        resolved = path.resolve()
        try:
            name = resolved.relative_to(root.resolve()).as_posix()
        except ValueError as exc:
            raise ValueError("manifest file must be inside output directory") from exc
        if not resolved.is_file() or resolved.is_symlink():
            raise ValueError(f"manifest input is not a regular file: {path}")
        records[name] = {
            "bytes": resolved.stat().st_size,
            "sha256": sha256_file(resolved),
        }
    manifest: dict[str, object] = {
        "schema_version": 1,
        "source_sha": source_sha,
        "duration_seconds": sum(scene.duration_seconds for scene in SCENES),
        "resolution": f"{WIDTH}x{HEIGHT}",
        "frame_rate": FRAME_RATE,
        "audio": False,
        "scope": (
            "captioned local technical rehearsal walkthrough; "
            "not a live Twilio interaction or submission receipt"
        ),
        "boundaries": {
            "live_twilio_interaction": False,
            "application_submitted": False,
            "award_received": False,
            "payment_received": False,
            "money_spent": False,
        },
        "files": records,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Capture a source-bound Twilio Searchlight judge walkthrough."
    )
    parser.add_argument("--html", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--browser", type=Path, required=True)
    parser.add_argument("--ffmpeg", type=Path, required=True)
    args = parser.parse_args()

    current_sha = current_source_sha()
    if args.source_sha != current_sha:
        raise ValueError("capture source SHA does not match current Git HEAD")
    if not args.ffmpeg.is_file():
        raise FileNotFoundError(f"ffmpeg executable not found: {args.ffmpeg}")
    html = args.html.read_text(encoding="utf-8")
    validate_html(html, args.source_sha)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    report = args.output_dir / "judge-demo.html"
    report.write_text(html, encoding="utf-8", newline="\n")
    screenshots = capture_screenshots(
        args.browser, report, args.output_dir / "screenshots"
    )
    captions = args.output_dir / "captions.srt"
    captions.write_text(render_srt(SCENES), encoding="utf-8", newline="\n")
    video = args.output_dir / "judge-walkthrough.mp4"
    subprocess.run(
        build_ffmpeg_command(args.ffmpeg, screenshots, video),
        check=True,
        capture_output=True,
        text=True,
        timeout=600,
    )
    if not video.is_file() or video.stat().st_size == 0:
        raise RuntimeError("ffmpeg did not create the walkthrough video")
    files = screenshots + [captions, video, report]
    manifest = write_manifest(
        args.output_dir,
        args.output_dir / "manifest.json",
        args.source_sha,
        files,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
