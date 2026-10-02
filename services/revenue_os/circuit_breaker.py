from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass
class CircuitBreaker:
    failure_threshold: int = 3
    cooldown_seconds: int = 300
    failures: int = 0
    opened_at: datetime | None = None

    def allowed(self) -> bool:
        if self.opened_at is None:
            return True
        if datetime.now(timezone.utc) - self.opened_at >= timedelta(seconds=self.cooldown_seconds):
            self.failures = 0
            self.opened_at = None
            return True
        return False

    def success(self) -> None:
        self.failures = 0
        self.opened_at = None

    def failure(self) -> None:
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.opened_at = datetime.now(timezone.utc)
