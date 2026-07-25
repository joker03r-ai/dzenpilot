"""Подключение к Redis.

Redis используется для ограничения частоты запросов, защиты от повторной отправки
и кэша. Если Redis недоступен, приложение продолжает работать — соответствующие
функции просто отключаются, а в лог пишется предупреждение.
"""

from __future__ import annotations

import logging

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import settings

logger = logging.getLogger("dzenpilot.redis")

_client: Redis | None = None
_unavailable_logged = False


def get_redis() -> Redis:
    global _client
    if _client is None:
        _client = Redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
    return _client


async def redis_ping() -> bool:
    global _unavailable_logged
    try:
        await get_redis().ping()
        _unavailable_logged = False
        return True
    except (RedisError, OSError) as exc:
        if not _unavailable_logged:
            logger.warning("Redis недоступен: %s", exc)
            _unavailable_logged = True
        return False


async def close_redis() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
