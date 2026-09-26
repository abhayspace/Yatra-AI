"""Small in-memory sliding-window rate limiter, keyed by client address.

Each chat turn can spend model tokens, so the public endpoints are capped per client. This is
best-effort protection for a single-instance demo (state is per process); put a gateway in front
for anything larger.
"""
from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock


class RateLimiter:
    def __init__(self, limit: int, window_seconds: float = 60.0, clock=time.monotonic):
        self.limit = limit
        self.window = window_seconds
        self._clock = clock
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str) -> bool:
        if self.limit <= 0:
            return True
        now = self._clock()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] >= self.window:
                hits.popleft()
            if len(hits) >= self.limit:
                return False
            hits.append(now)
            if len(self._hits) > 10_000:  # bound memory under a flood of distinct addresses
                for stale in [k for k, v in self._hits.items() if not v or now - v[-1] >= self.window]:
                    del self._hits[stale]
            return True

    def blocked(self, key: str) -> bool:
        """True if `key` is at its limit right now (does not record a hit)."""
        if self.limit <= 0:
            return False
        now = self._clock()
        with self._lock:
            hits = self._hits.get(key)
            return bool(hits) and sum(1 for h in hits if now - h < self.window) >= self.limit

    def retry_after(self, key: str) -> int:
        with self._lock:
            hits = self._hits.get(key)
            if not hits:
                return 0
            return max(1, int(self.window - (self._clock() - hits[0])) + 1)
