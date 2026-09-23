from __future__ import annotations

import hashlib
import threading
import time
from collections import OrderedDict
from concurrent.futures import Future, TimeoutError as FutureTimeoutError
from dataclasses import dataclass
from typing import Callable

ReplayResult = tuple[str, dict[str, str]]


class ReplayConflict(ValueError):
    """Raised when a MessageSid is reused with different content."""


class ReplayWaitTimeout(TimeoutError):
    """Raised when an identical in-flight delivery does not finish in time."""


@dataclass
class _Entry:
    body_digest: str
    created_at: float
    future: Future[ReplayResult]


class ReplayGuard:
    """Deduplicate successful Twilio retries without retaining raw message data."""

    def __init__(
        self,
        max_entries: int = 256,
        ttl_seconds: float = 600.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if max_entries < 1:
            raise ValueError("max_entries must be positive")
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        self._max_entries = max_entries
        self._ttl_seconds = ttl_seconds
        self._clock = clock
        self._entries: OrderedDict[str, _Entry] = OrderedDict()
        self._lock = threading.Lock()

    @staticmethod
    def _digest(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def _purge(self, now: float) -> None:
        expired = [
            key
            for key, entry in self._entries.items()
            if entry.future.done() and now - entry.created_at >= self._ttl_seconds
        ]
        for key in expired:
            self._entries.pop(key, None)
        while len(self._entries) >= self._max_entries:
            completed_key = next(
                (key for key, entry in self._entries.items() if entry.future.done()),
                None,
            )
            if completed_key is None:
                break
            self._entries.pop(completed_key, None)

    def run_once(
        self,
        message_sid: str,
        body: str,
        action: Callable[[], ReplayResult],
        wait_timeout_seconds: float = 10.0,
    ) -> tuple[ReplayResult, bool]:
        key = self._digest(message_sid)
        body_digest = self._digest(body)
        with self._lock:
            self._purge(self._clock())
            entry = self._entries.get(key)
            if entry is not None:
                if entry.body_digest != body_digest:
                    raise ReplayConflict(
                        "MessageSid was reused with different message content"
                    )
                self._entries.move_to_end(key)
                owner = False
            else:
                entry = _Entry(body_digest, self._clock(), Future())
                self._entries[key] = entry
                owner = True

        if not owner:
            try:
                return entry.future.result(timeout=wait_timeout_seconds), True
            except FutureTimeoutError as exc:
                raise ReplayWaitTimeout(
                    "matching webhook delivery is still in progress"
                ) from exc

        try:
            result = action()
        except BaseException as exc:
            entry.future.set_exception(exc)
            with self._lock:
                if self._entries.get(key) is entry:
                    self._entries.pop(key, None)
            raise
        entry.future.set_result(result)
        return result, False
