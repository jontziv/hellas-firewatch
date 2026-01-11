from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import Dict, Tuple

from fastapi import Request, HTTPException

from .config import settings


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def get_client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def device_fingerprint_raw(request: Request) -> str:
    cookie_fp = request.cookies.get("hf_fp")
    if cookie_fp:
        return cookie_fp
    ua = request.headers.get("user-agent", "unknown")
    ip = get_client_ip(request)
    return f"{ua}|{ip}"


@dataclass
class TokenBucket:
    capacity: int
    refill_per_second: float
    tokens: float
    last_refill: float


class RateLimiter:
    def __init__(self, per_minute: int) -> None:
        self.per_minute = per_minute
        self._buckets: Dict[str, TokenBucket] = {}

    def check(self, key: str) -> bool:
        now = time.time()
        capacity = self.per_minute
        refill_per_second = self.per_minute / 60.0

        b = self._buckets.get(key)
        if b is None:
            b = TokenBucket(capacity=capacity, refill_per_second=refill_per_second, tokens=capacity, last_refill=now)
            self._buckets[key] = b

        elapsed = max(0.0, now - b.last_refill)
        b.tokens = min(b.capacity, b.tokens + elapsed * b.refill_per_second)
        b.last_refill = now

        if b.tokens >= 1.0:
            b.tokens -= 1.0
            return True
        return False


rate_limiter = RateLimiter(settings.rate_limit_per_minute)

_last_verify_ts: Dict[str, float] = {}
_abuse_totals: Dict[str, int] = {"verify_attempts": 0, "blocked": 0}


def record_attempt() -> None:
    _abuse_totals["verify_attempts"] += 1


def record_block() -> None:
    _abuse_totals["blocked"] += 1


def abuse_stats() -> Tuple[int, int]:
    return _abuse_totals["verify_attempts"], _abuse_totals["blocked"]


def enforce_rate_limit(request: Request) -> None:
    ip = get_client_ip(request)
    if not rate_limiter.check(ip):
        record_block()
        raise HTTPException(status_code=429, detail="Too many requests. Please slow down.")


def enforce_cooldown(device_fp_hash: str) -> None:
    now = time.time()
    last = _last_verify_ts.get(device_fp_hash)
    if last is not None and (now - last) < settings.verify_cooldown_seconds:
        record_block()
        raise HTTPException(status_code=429, detail="Please wait before verifying again.")
    _last_verify_ts[device_fp_hash] = now
