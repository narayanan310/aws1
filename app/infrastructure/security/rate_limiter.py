"""Simple in-memory rate limiter for local development."""

from __future__ import annotations

from collections import defaultdict, deque
from time import time

from flask import current_app, request


class RateLimiter:
    """Per-IP rolling-window limiter.

    Replace with Redis or API Gateway throttling in distributed deployments.
    """

    def __init__(self) -> None:
        self._requests: dict[str, deque[float]] = defaultdict(deque)

    def check(self) -> bool:
        limit = current_app.config["RATE_LIMIT_PER_MINUTE"]
        key = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown")
        now = time()
        bucket = self._requests[key]
        while bucket and bucket[0] < now - 60:
            bucket.popleft()
        if len(bucket) >= limit:
            return False
        bucket.append(now)
        return True


rate_limiter = RateLimiter()

