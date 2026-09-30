from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import re
import shutil
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator


SCHEMA_VERSION = 1
_SECRET_KEYS = {
    "authorization", "password", "passwd", "secret", "token", "access_token",
    "refresh_token", "api_key", "apikey", "bearer", "cookie", "set-cookie",
}
_SECRET_PATTERNS = [
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"(?i)([?&](?:token|key|secret|code)=)[^&\s]+"),
]


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def redact(value: Any, key: str | None = None) -> Any:
    if key and key.lower().replace("-", "_") in _SECRET_KEYS:
        return "[REDACTED]"
    if isinstance(value, dict):
        return {str(k): redact(v, str(k)) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, str):
        text = value
        for pattern in _SECRET_PATTERNS:
            if pattern.pattern.startswith("(?i)([?&]"):
                text = pattern.sub(lambda m: m.group(1) + "[REDACTED]", text)
            else:
                text = pattern.sub("[REDACTED]", text)
        return text
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return repr(value)


@contextmanager
def _file_lock(path: Path) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        if path.stat().st_size == 0:
            handle.write(b"0")
            handle.flush()
        if os.name == "nt":
            import msvcrt

            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _tail_json(path: Path) -> dict[str, Any] | None:
    if not path.exists() or path.stat().st_size == 0:
        return None
    with path.open("rb") as handle:
        handle.seek(0, os.SEEK_END)
        pos = handle.tell() - 1
        while pos >= 0:
            handle.seek(pos)
            byte = handle.read(1)
            if byte not in {b"\n", b"\r"}:
                break
            pos -= 1
        while pos >= 0:
            handle.seek(pos)
            if handle.read(1) == b"\n":
                pos += 1
                break
            pos -= 1
        handle.seek(max(pos, 0))
        line = handle.readline().decode("utf-8").strip()
    if not line:
        return None
    return json.loads(line)


class EvidenceSession:
    def __init__(
        self,
        root: Path,
        *,
        title: str,
        source: str,
        session_id: str | None = None,
        existing: bool = False,
    ) -> None:
        self.root = Path(root)
        self.session_id = session_id or (
            datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
        )
        self.session_dir = self.root if existing else self.root / self.session_id
        self.events_path = self.session_dir / "events.jsonl"
        self.manifest_path = self.session_dir / "manifest.json"
        self.artifact_dir = self.session_dir / "artifacts"
        self.lock_path = self.session_dir / ".events.lock"
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        self.title = title
        self.source = source
        self._started_at_utc = datetime.now(timezone.utc)

        if existing:
            manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            self.session_id = str(manifest["session_id"])
            self.title = str(manifest.get("title") or title)
            self.source = str(manifest.get("source") or source)
            started_at = manifest.get("started_at")
            if started_at:
                self._started_at_utc = datetime.fromisoformat(str(started_at))
            else:
                elapsed = float(manifest.get("elapsed_seconds") or 0.0)
                self._started_at_utc = datetime.now(timezone.utc) - timedelta(seconds=elapsed)
        else:
            self._write_manifest(status="recording")
            self.emit("session.start", message=title, data={"source": source})

    @classmethod
    def from_env(cls) -> "EvidenceSession | None":
        value = os.environ.get("HAL_EVIDENCE_SESSION_DIR")
        if not value:
            return None
        session_dir = Path(value).expanduser().resolve()
        if not (session_dir / "manifest.json").is_file():
            return None
        return cls.open_existing(session_dir)

    @classmethod
    def open_existing(cls, session_dir: Path) -> "EvidenceSession":
        session_dir = Path(session_dir)
        manifest = json.loads((session_dir / "manifest.json").read_text(encoding="utf-8"))
        return cls(
            session_dir,
            title=str(manifest.get("title") or "HAL evidence session"),
            source=str(manifest.get("source") or "unknown"),
            session_id=str(manifest["session_id"]),
            existing=True,
        )

    def _write_manifest(self, *, status: str, **extra: Any) -> None:
        payload = {
            "schema_version": SCHEMA_VERSION,
            "session_id": self.session_id,
            "title": self.title,
            "source": self.source,
            "status": status,
            "session_dir": str(self.session_dir),
            "events_file": "events.jsonl",
            "artifact_dir": "artifacts",
            "started_at": self._started_at_utc.isoformat(),
            "elapsed_seconds": max(
                0.0,
                (datetime.now(timezone.utc) - self._started_at_utc).total_seconds(),
            ),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            **redact(extra),
        }
        tmp = self.manifest_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(tmp, self.manifest_path)

    def emit(
        self,
        kind: str,
        *,
        message: str = "",
        phase: str | None = None,
        data: dict[str, Any] | None = None,
        source: str | None = None,
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        base = {
            "schema_version": SCHEMA_VERSION,
            "session_id": self.session_id,
            "ts_utc": now.isoformat(),
            "elapsed_ms": int(max(0.0, (now - self._started_at_utc).total_seconds()) * 1000),
            "kind": str(kind),
            "source": source or self.source,
            "phase": phase,
            "message": message,
            "data": data or {},
        }
        safe = redact(base)
        with _file_lock(self.lock_path):
            previous = _tail_json(self.events_path)
            safe["seq"] = 1 if previous is None else int(previous["seq"]) + 1
            safe["prev_hash"] = None if previous is None else previous["event_hash"]
            encoded = _canonical(safe).encode("utf-8")
            safe["event_hash"] = _sha256_bytes(encoded)
            with self.events_path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(_canonical(safe) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
        return safe

    def register_artifact(
        self,
        path: Path,
        *,
        role: str,
        copy_into_session: bool = True,
    ) -> dict[str, Any]:
        source = Path(path).expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(source)
        digest = sha256_file(source)
        mime, _ = mimetypes.guess_type(source.name)
        stored_path: str | None = None
        if copy_into_session:
            name = source.name
            target = self.artifact_dir / name
            if target.exists() and sha256_file(target) != digest:
                target = self.artifact_dir / f"{source.stem}-{digest[:10]}{source.suffix}"
            if not target.exists():
                shutil.copy2(source, target)
            stored_path = str(target.relative_to(self.session_dir)).replace("\\", "/")
        record = {
            "role": role,
            "source_path": str(source),
            "stored_path": stored_path,
            "sha256": digest,
            "bytes": source.stat().st_size,
            "mime_type": mime or "application/octet-stream",
        }
        self.emit("artifact.registered", message=source.name, data=record)
        return record

    def finalize(self, *, status: str, exit_code: int | None = None, error: str | None = None) -> None:
        final = self.emit(
            "session.end",
            message=status,
            data={"exit_code": exit_code, "error": error},
        )
        artifact_count = 0
        if self.events_path.exists():
            with self.events_path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if '"kind":"artifact.registered"' in line:
                        artifact_count += 1
        self._write_manifest(
            status=status,
            exit_code=exit_code,
            error=error,
            artifact_count=artifact_count,
            last_event_hash=final["event_hash"],
        )


def verify_session(session_dir: Path) -> dict[str, Any]:
    path = Path(session_dir) / "events.jsonl"
    previous_hash: str | None = None
    expected_seq = 1
    count = 0
    failures: list[str] = []
    with path.open("r", encoding="utf-8") as handle:
        for raw in handle:
            if not raw.strip():
                continue
            event = json.loads(raw)
            event_hash = event.pop("event_hash", None)
            if event.get("seq") != expected_seq:
                failures.append(f"seq:{event.get('seq')}!=expected:{expected_seq}")
            if event.get("prev_hash") != previous_hash:
                failures.append(f"prev_hash_mismatch_at:{expected_seq}")
            calculated = _sha256_bytes(_canonical(event).encode("utf-8"))
            if event_hash != calculated:
                failures.append(f"hash_mismatch_at:{expected_seq}")
            previous_hash = event_hash
            expected_seq += 1
            count += 1
    return {
        "passed": not failures,
        "event_count": count,
        "last_event_hash": previous_hash,
        "failures": failures,
    }
