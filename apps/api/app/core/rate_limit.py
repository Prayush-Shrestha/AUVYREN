"""Small in-process rate limiter for authentication endpoints.

The limiter is intentionally bounded and dependency-free. It protects a single
API process; multi-worker deployments should replace it with a shared store
(see docs/security.md).
"""

from __future__ import annotations

import asyncio
import hashlib
import math
import time
from collections import deque
from collections.abc import Iterable
from dataclasses import dataclass

from app.api.errors import AppError


@dataclass(frozen=True)
class RateLimitRule:
    key: str
    limit: int
    window_seconds: int


def email_rate_key(prefix: str, email: str) -> str:
    digest = hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()[:24]
    return f"{prefix}:email:{digest}"


def client_rate_key(prefix: str, client_host: str) -> str:
    return f"{prefix}:ip:{client_host}"


class RateLimiter:
    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = {}
        self._lock = asyncio.Lock()

    async def enforce(self, rules: Iterable[RateLimitRule]) -> None:
        rules = list(rules)
        now = time.monotonic()

        async with self._lock:
            retry_after = 0
            for rule in rules:
                events = self._events.get(rule.key)
                if events is None:
                    continue
                cutoff = now - rule.window_seconds
                while events and events[0] <= cutoff:
                    events.popleft()
                if len(events) >= rule.limit:
                    retry_after = max(
                        retry_after,
                        math.ceil(events[0] + rule.window_seconds - now),
                    )

            if retry_after:
                raise AppError(
                    429,
                    "rate_limit_exceeded",
                    title="Too many requests",
                    detail="Too many attempts. Please wait before trying again.",
                    headers={"Retry-After": str(max(1, retry_after))},
                )

            for rule in rules:
                self._events.setdefault(rule.key, deque()).append(now)

            self._prune(now)

    def _prune(self, now: float) -> None:
        if len(self._events) < 5_000:
            return
        oldest_allowed = now - 24 * 60 * 60
        for key, events in list(self._events.items()):
            while events and events[0] <= oldest_allowed:
                events.popleft()
            if not events:
                self._events.pop(key, None)

    async def reset(self) -> None:
        async with self._lock:
            self._events.clear()


rate_limiter = RateLimiter()
