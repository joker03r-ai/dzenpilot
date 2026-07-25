"""Защита от повторной отправки запроса.

Клиент передаёт заголовок `Idempotency-Key`. Первый запрос выполняется и его ответ
кладётся в Redis на 24 часа. Повтор с тем же ключом получает сохранённый ответ,
а дубликат в базе не создаётся.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import Request
from redis.exceptions import RedisError

from app.core.errors import ConflictError
from app.core.redis_client import get_redis

logger = logging.getLogger("dzenpilot.idempotency")

TTL_SECONDS = 24 * 60 * 60
HEADER_NAME = "Idempotency-Key"


def _key(request: Request, idem_key: str) -> str:
    user_id = getattr(request.state, "user_id", "anonymous")
    return f"idem:{user_id}:{request.url.path}:{idem_key}"


async def get_cached_response(request: Request) -> dict[str, Any] | None:
    """Возвращает сохранённый ответ или None. Если запрос ещё выполняется — 409."""
    idem_key = request.headers.get(HEADER_NAME)
    if not idem_key:
        return None
    try:
        redis = get_redis()
        stored = await redis.get(_key(request, idem_key))
        if stored is None:
            # Помечаем ключ как «в работе», чтобы отсечь параллельный дубль.
            await redis.set(_key(request, idem_key), "__in_progress__", ex=TTL_SECONDS, nx=True)
            return None
        if stored == "__in_progress__":
            raise ConflictError(
                "Этот запрос уже выполняется. Дождитесь результата, не отправляйте повторно."
            )
        return json.loads(stored)
    except (RedisError, OSError):
        return None
    except json.JSONDecodeError:
        return None


async def store_response(request: Request, payload: dict[str, Any]) -> None:
    idem_key = request.headers.get(HEADER_NAME)
    if not idem_key:
        return
    try:
        await get_redis().set(
            _key(request, idem_key),
            json.dumps(payload, ensure_ascii=False, default=str),
            ex=TTL_SECONDS,
        )
    except (RedisError, OSError, TypeError) as exc:
        logger.debug("Не удалось сохранить идемпотентный ответ: %s", exc)
