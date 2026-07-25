"""Ограничение частоты запросов на Redis (скользящее окно в одну минуту)."""

from __future__ import annotations

import time
from collections.abc import Callable

from fastapi import Request
from redis.exceptions import RedisError

from app.core.config import settings
from app.core.errors import RateLimitError
from app.core.redis_client import get_redis


def _client_key(request: Request) -> str:
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"
    forwarded = request.headers.get("X-Forwarded-For")
    ip = forwarded.split(",")[0].strip() if forwarded else (
        request.client.host if request.client else "unknown"
    )
    return f"ip:{ip}"


async def check_rate_limit(request: Request, bucket: str, limit: int) -> None:
    """Бросает RateLimitError при превышении лимита. При недоступности Redis пропускает."""
    if limit <= 0:
        return
    window = 60
    now = time.time()
    key = f"ratelimit:{bucket}:{_client_key(request)}"
    try:
        redis = get_redis()
        pipe = redis.pipeline()
        pipe.zremrangebyscore(key, 0, now - window)
        pipe.zadd(key, {f"{now}:{id(request)}": now})
        pipe.zcard(key)
        pipe.expire(key, window)
        results = await pipe.execute()
        used = int(results[2])
    except (RedisError, OSError):
        return  # Redis недоступен — лимиты временно не применяются

    if used > limit:
        raise RateLimitError(
            "Слишком много запросов. Подождите минуту и попробуйте снова.",
            details={"limit": limit, "window_seconds": window},
        )


def rate_limit(bucket: str, limit: int | None = None) -> Callable:
    """Зависимость FastAPI: Depends(rate_limit('auth', 10))."""

    async def dependency(request: Request) -> None:
        effective = limit if limit is not None else settings.rate_limit_default_per_minute
        await check_rate_limit(request, bucket, effective)

    return dependency


auth_rate_limit = rate_limit("auth", settings.rate_limit_auth_per_minute)
ai_rate_limit = rate_limit("ai", settings.rate_limit_ai_per_minute)
default_rate_limit = rate_limit("default", settings.rate_limit_default_per_minute)
