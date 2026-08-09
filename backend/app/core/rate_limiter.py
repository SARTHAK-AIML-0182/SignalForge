"""
Process-Local Rate Limiter for SignalForge Backend.

NOTE: This is a lightweight, in-memory, process-local rate limiter suitable for single-process API deployments.
It does NOT use Redis, Celery, RQ, or external rate-limiting services.
For distributed multi-worker production deployments, a Redis-backed rate limiter would be required.
"""

import time
from typing import Callable, Dict, List, Optional
from fastapi import HTTPException, Request, status


class ProcessLocalRateLimiter:
    """
    In-memory, deterministic sliding-window rate limiter.
    Supports injectable time functions for deterministic zero-sleep testing.
    """

    def __init__(
        self,
        requests_per_window: int = 5,
        window_seconds: int = 60,
        time_func: Optional[Callable[[], float]] = None,
    ):
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        self.time_func = time_func or time.time
        self._history: Dict[str, List[float]] = {}

    def reset(self) -> None:
        """Clear all rate limiting history (primarily for testing)."""
        self._history.clear()

    def set_time_func(self, time_func: Optional[Callable[[], float]] = None) -> None:
        """Set a custom time function (primarily for testing). Resets to time.time if None."""
        self.time_func = time_func or time.time

    def check(self, key: str) -> None:
        """
        Check rate limit for a key.
        If limit is exceeded, raises HTTPException(429) with Retry-After header.
        """
        now = self.time_func()
        cutoff = now - self.window_seconds

        timestamps = self._history.get(key, [])
        valid_timestamps = [t for t in timestamps if t > cutoff]

        if len(valid_timestamps) >= self.requests_per_window:
            oldest_valid = valid_timestamps[0]
            retry_after = max(1, int(oldest_valid + self.window_seconds - now))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {self.requests_per_window} requests per {self.window_seconds}s allowed.",
                headers={"Retry-After": str(retry_after)},
            )

        valid_timestamps.append(now)
        self._history[key] = valid_timestamps


# Default process-local rate limiters for key endpoints
workflow_run_limiter = ProcessLocalRateLimiter(requests_per_window=5, window_seconds=60)
persona_update_limiter = ProcessLocalRateLimiter(requests_per_window=10, window_seconds=60)
feed_config_limiter = ProcessLocalRateLimiter(requests_per_window=10, window_seconds=60)


def rate_limit_workflow_run(agent_id: str, request: Request) -> None:
    """Rate limit POST /agent/{agent_id}/workflow/run (5 req / 60s per agent_id)."""
    client_ip = request.client.host if (request and request.client) else "local"
    key = f"workflow_run:{agent_id or client_ip}"
    workflow_run_limiter.check(key)


def rate_limit_persona_update(agent_id: str, request: Request) -> None:
    """Rate limit PUT /agent/{agent_id}/persona (10 req / 60s per agent_id)."""
    client_ip = request.client.host if (request and request.client) else "local"
    key = f"persona_update:{agent_id or client_ip}"
    persona_update_limiter.check(key)


def rate_limit_feed_config_update(agent_id: str, request: Request) -> None:
    """Rate limit PUT /agent/{agent_id}/feed/config (10 req / 60s per agent_id)."""
    client_ip = request.client.host if (request and request.client) else "local"
    key = f"feed_config:{agent_id or client_ip}"
    feed_config_limiter.check(key)
