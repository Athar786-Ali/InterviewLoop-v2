import threading
import time
from collections import defaultdict

from app.core.config import settings
from app.core.exceptions import AppError


class RateLimiter:
    """In-memory rate limiter using a sliding counter with TTL reset.

    Replaces the Redis-backed implementation. State resets on server restart,
    which is acceptable for a single-instance student SaaS deployment.
    Thread-safe via a per-key lock.
    """

    def __init__(self) -> None:
        self._counters: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def check(self, key: str) -> None:
        window = settings.auth_rate_limit_window_seconds
        limit = settings.auth_rate_limit_attempts
        now = time.monotonic()
        cutoff = now - window

        with self._lock:
            # Evict timestamps outside the rolling window
            self._counters[key] = [ts for ts in self._counters[key] if ts > cutoff]
            self._counters[key].append(now)
            count = len(self._counters[key])

        if count > limit:
            raise AppError("RATE_LIMITED", "Too many attempts. Try again later.", 429)
