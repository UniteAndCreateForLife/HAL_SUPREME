from __future__ import annotations

import argparse
import glob
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evidence.runtime import EvidenceSession


def _parse_artifact(value: str) -> tuple[str, str]:
    if "=" not in value:
        return "output", value
    role, pattern = value.split("=", 1)
    return (role.strip() or "output", pattern.strip())


def _sample(proc: Any) -> dict[str, Any]:
    with proc.oneshot():
        data: dict[str, Any] = {
            "pid": proc.pid,
            "name": proc.name(),
            "status": proc.status(),
            "cpu_percent": proc.cpu_percent(interval=None),
            "rss_bytes": proc.memory_info().rss,
            "threads": proc.num_threads(),
        }
        try:
            io = proc.io_counters()
            data["read_bytes"] = io.read_bytes
            data["write_bytes"] = io.write_bytes
        except Exception:
            pass
    try:
        children = proc.children(recursive=True)
        data["child_processes"] = len(children)
        data["child_rss_bytes"] = sum(
            child.memory_info().rss for child in children if child.is_running()
        )
    except Exception:
        data["child_processes"] = None
    return data


def _sample_nvidia() -> list[dict[str, Any]] | None:
    executable = shutil.which("nvidia-smi")
    if executable is None:
        return None
    proc = subprocess.run(
        [
            executable,
            "--query-gpu=index,name,utilization.gpu,utilization.memory,memory.used,memory.total,temperature.gpu,power.draw",
            "--format=csv,noheader,nounits",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
    )
    if proc.returncode != 0:
        return []
    result: list[dict[str, Any]] = []
    for line in proc.stdout.splitlines():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) != 8:
            continue
        def number(value: str) -> float | None:
            try:
                return float(value)
            except ValueError:
                return None
        result.append({
            "index": int(parts[0]),
            "name": parts[1],
            "gpu_util_percent": number(parts[2]),
            "memory_util_percent": number(parts[3]),
            "memory_used_mib": number(parts[4]),
            "memory_total_mib": number(parts[5]),
            "temperature_c": number(parts[6]),
            "power_w": number(parts[7]),
        })
    return result


def _tail(path: Path, position: int) -> tuple[int, list[str]]:
    if not path.is_file():
        return position, []
    size = path.stat().st_size
    if size < position:
        position = 0
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        handle.seek(position)
        lines = [line.rstrip("\r\n") for line in handle.readlines()]
        return handle.tell(), lines


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Attach HAL evidence observation to an already-running headless process."
    )
    parser.add_argument("--pid", required=True, type=int)
    parser.add_argument("--duration", type=float, help="Stop after N seconds; otherwise observe until process exit.")
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--gpu-interval", type=float, default=2.0)
    parser.add_argument("--no-gpu", action="store_true")
    parser.add_argument("--session", type=Path, help="Join an existing evidence session instead of creating one.")
    parser.add_argument("--root", type=Path, default=Path("evidence/runtime"))
    parser.add_argument("--title", default="HAL attached process observation")
    parser.add_argument("--source", default="process-attach")
    parser.add_argument("--tail-log", action="append", default=[], type=Path)
    parser.add_argument("--tail-from-start", action="store_true")
    parser.add_argument("--artifact", action="append", default=[], type=_parse_artifact)
    args = parser.parse_args()

    try:
        import psutil  # type: ignore
    except ImportError:
        parser.error("observe_headless.py requires psutil")

    own_session = args.session is None
    session = (
        EvidenceSession(args.root, title=args.title, source=args.source)
        if own_session
        else EvidenceSession.open_existing(args.session)
    )

    try:
        proc = psutil.Process(args.pid)
    except psutil.Error as exc:
        session.emit(
            "observer.attach_failed",
            phase="observe",
            message=str(exc),
            data={"pid": args.pid},
        )
        if own_session:
            session.finalize(status="failed", error=str(exc))
        return 2

    log_positions: dict[Path, int] = {}
    for raw in args.tail_log:
        path = raw.expanduser().resolve()
        log_positions[path] = 0 if args.tail_from_start or not path.exists() else path.stat().st_size

    session.emit(
        "observer.attached",
        phase="observe",
        message=f"PID {args.pid}",
        data={"pid": args.pid, "process_name": proc.name(), "logs": [str(p) for p in log_positions]},
    )

    try:
        proc.cpu_percent(interval=None)
    except psutil.Error:
        pass

    started = time.monotonic()
    next_gpu = 0.0
    gpu_notice_sent = False
    reason = "process_exit"
    while True:
        if args.duration is not None and time.monotonic() - started >= args.duration:
            reason = "duration_elapsed"
            break
        if not proc.is_running():
            break
        try:
            if proc.status() == psutil.STATUS_ZOMBIE:
                break
            session.emit("process.metric", phase="observe", data=_sample(proc))
            now = time.monotonic()
            if not args.no_gpu and now >= next_gpu:
                gpu_metrics = _sample_nvidia()
                if gpu_metrics is None:
                    if not gpu_notice_sent:
                        session.emit(
                            "gpu.metric_unavailable",
                            phase="observe",
                            message="nvidia-smi not available",
                        )
                        gpu_notice_sent = True
                elif gpu_metrics:
                    session.emit("gpu.metric", phase="observe", data={"gpus": gpu_metrics})
                next_gpu = now + max(0.5, args.gpu_interval)
        except psutil.Error as exc:
            session.emit(
                "observer.process_unavailable",
                phase="observe",
                message=str(exc),
                data={"pid": args.pid},
            )
            break

        for path, position in list(log_positions.items()):
            try:
                new_position, lines = _tail(path, position)
                log_positions[path] = new_position
                for line in lines:
                    session.emit(
                        "log.line",
                        phase="observe",
                        message=line,
                        data={"path": str(path), "pid": args.pid},
                    )
            except Exception as exc:
                session.emit(
                    "log.read_failed",
                    phase="observe",
                    message=str(exc),
                    data={"path": str(path)},
                )
        time.sleep(max(0.25, args.interval))

    session.emit(
        "observer.detached",
        phase="observe",
        message=reason,
        data={"pid": args.pid, "reason": reason},
    )

    cwd = Path.cwd()
    for role, pattern in args.artifact:
        full_pattern = pattern if Path(pattern).is_absolute() else str(cwd / pattern)
        for match in sorted(glob.glob(full_pattern, recursive=True)):
            path = Path(match)
            if path.is_file():
                try:
                    session.register_artifact(path, role=role, copy_into_session=True)
                except Exception as exc:
                    session.emit(
                        "artifact.register_failed",
                        phase="collect",
                        message=str(path),
                        data={"role": role, "error": str(exc)},
                    )

    if own_session:
        session.finalize(status="completed", exit_code=None)
        print(session.session_dir.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
