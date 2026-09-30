from __future__ import annotations

import argparse
import glob
import os
import queue
import shlex
import shutil
import subprocess
import sys
import threading
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
    role = role.strip() or "output"
    pattern = pattern.strip()
    if not pattern:
        raise argparse.ArgumentTypeError("artifact pattern may not be empty")
    return role, pattern


def _reader(stream: Any, channel: str, output: queue.Queue[tuple[str, str] | None]) -> None:
    try:
        for line in iter(stream.readline, ""):
            output.put((channel, line.rstrip("\r\n")))
    finally:
        output.put(None)


def _sample_process(pid: int) -> dict[str, Any] | None:
    try:
        import psutil  # type: ignore
    except ImportError:
        return None
    try:
        proc = psutil.Process(pid)
        with proc.oneshot():
            info: dict[str, Any] = {
                "pid": pid,
                "cpu_percent": proc.cpu_percent(interval=None),
                "rss_bytes": proc.memory_info().rss,
                "threads": proc.num_threads(),
                "status": proc.status(),
            }
            try:
                io = proc.io_counters()
                info["read_bytes"] = io.read_bytes
                info["write_bytes"] = io.write_bytes
            except (psutil.AccessDenied, AttributeError):
                pass
        children = proc.children(recursive=True)
        info["child_processes"] = len(children)
        return info
    except Exception as exc:
        return {"pid": pid, "metric_error": type(exc).__name__}


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
    gpus: list[dict[str, Any]] = []
    for line in proc.stdout.splitlines():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) != 8:
            continue
        def number(value: str) -> float | None:
            try:
                return float(value)
            except ValueError:
                return None
        gpus.append({
            "index": int(parts[0]),
            "name": parts[1],
            "gpu_util_percent": number(parts[2]),
            "memory_util_percent": number(parts[3]),
            "memory_used_mib": number(parts[4]),
            "memory_total_mib": number(parts[5]),
            "temperature_c": number(parts[6]),
            "power_w": number(parts[7]),
        })
    return gpus


def _command_display(command: list[str]) -> str:
    if os.name == "nt":
        return subprocess.list2cmdline(command)
    return shlex.join(command)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run any headless command under HAL's hash-chained evidence recorder."
    )
    parser.add_argument("--root", type=Path, default=Path("evidence/runtime"))
    parser.add_argument("--title", default="HAL headless process")
    parser.add_argument("--source", default="process")
    parser.add_argument("--cwd", type=Path)
    parser.add_argument("--artifact", action="append", default=[], type=_parse_artifact,
                        help="Register ROLE=GLOB after the command exits. Repeat as needed.")
    parser.add_argument("--metric-interval", type=float, default=1.0)
    parser.add_argument("--no-metrics", action="store_true")
    parser.add_argument("--gpu-interval", type=float, default=2.0)
    parser.add_argument("--no-gpu", action="store_true")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        parser.error("provide a command after --")

    cwd = (args.cwd or Path.cwd()).expanduser().resolve()
    session = EvidenceSession(args.root, title=args.title, source=args.source)
    env = os.environ.copy()
    env["HAL_EVIDENCE_SESSION_DIR"] = str(session.session_dir.resolve())
    env["PYTHONUNBUFFERED"] = "1"

    session.emit(
        "process.launch",
        phase="execute",
        message=_command_display(command),
        data={"command": command, "cwd": str(cwd), "pid": None},
    )

    try:
        proc = subprocess.Popen(
            command,
            cwd=str(cwd),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            errors="replace",
            bufsize=1,
            shell=False,
        )
    except Exception as exc:
        session.emit(
            "process.launch_failed",
            phase="execute",
            message=str(exc),
            data={"error_type": type(exc).__name__},
        )
        session.finalize(status="failed", exit_code=None, error=str(exc))
        print(session.session_dir)
        return 127

    session.emit("process.started", phase="execute", message=f"PID {proc.pid}", data={"pid": proc.pid})

    out_queue: queue.Queue[tuple[str, str] | None] = queue.Queue()
    assert proc.stdout is not None
    assert proc.stderr is not None
    threads = [
        threading.Thread(target=_reader, args=(proc.stdout, "stdout", out_queue), daemon=True),
        threading.Thread(target=_reader, args=(proc.stderr, "stderr", out_queue), daemon=True),
    ]
    for thread in threads:
        thread.start()

    finished_readers = 0
    next_metric = 0.0
    next_gpu = 0.0
    metric_notice_sent = False
    gpu_notice_sent = False
    while finished_readers < 2 or proc.poll() is None:
        try:
            item = out_queue.get(timeout=0.1)
            if item is None:
                finished_readers += 1
            else:
                channel, line = item
                session.emit(
                    f"process.{channel}",
                    phase="execute",
                    message=line,
                    data={"pid": proc.pid},
                )
        except queue.Empty:
            pass

        now = time.monotonic()
        if not args.no_metrics and now >= next_metric and proc.poll() is None:
            metrics = _sample_process(proc.pid)
            if metrics is None:
                if not metric_notice_sent:
                    session.emit(
                        "process.metric_unavailable",
                        phase="observe",
                        message="Install psutil for per-process CPU/memory/I/O samples.",
                    )
                    metric_notice_sent = True
            else:
                session.emit("process.metric", phase="observe", data=metrics)
            next_metric = now + max(0.25, args.metric_interval)

        if not args.no_gpu and now >= next_gpu and proc.poll() is None:
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

    exit_code = proc.wait()
    for thread in threads:
        thread.join(timeout=1.0)
    session.emit(
        "process.exited",
        phase="execute",
        message=f"exit code {exit_code}",
        data={"pid": proc.pid, "exit_code": exit_code},
    )

    for role, pattern in args.artifact:
        full_pattern = pattern if Path(pattern).is_absolute() else str(cwd / pattern)
        matches = sorted(glob.glob(full_pattern, recursive=True))
        files = [Path(match) for match in matches if Path(match).is_file()]
        if not files:
            session.emit(
                "artifact.pattern_empty",
                phase="collect",
                message=pattern,
                data={"role": role, "pattern": pattern},
            )
            continue
        for path in files:
            try:
                session.register_artifact(path, role=role, copy_into_session=True)
            except Exception as exc:
                session.emit(
                    "artifact.register_failed",
                    phase="collect",
                    message=str(path),
                    data={"role": role, "error": str(exc)},
                )

    status = "completed" if exit_code == 0 else "failed"
    session.finalize(status=status, exit_code=exit_code)
    print(str(session.session_dir.resolve()))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
