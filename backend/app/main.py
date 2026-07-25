"""Точка входа backend DzenPilot."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app import __version__
from app.api.router import api_router
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.logging import RequestLogMiddleware, setup_logging
from app.core.rate_limit import check_rate_limit
from app.core.redis_client import close_redis, redis_ping
from app.db.session import AsyncSessionLocal, dispose_engine

DESCRIPTION = """
API сервиса DzenPilot: анализ конкурентов, поиск тем, генерация статей,
контент-календарь и подготовка публикаций для Яндекс Дзена.

Авторизация выполняется через httpOnly-cookie: сначала вызовите
`POST /api/v1/auth/login`, затем остальные методы.
"""


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_logging()
    yield
    await close_redis()
    await dispose_engine()


app = FastAPI(
    title="DzenPilot API",
    description=DESCRIPTION,
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)
app.add_middleware(RequestLogMiddleware)
register_exception_handlers(app)


@app.middleware("http")
async def global_rate_limit(request: Request, call_next):
    """Общий лимит запросов. Точечные лимиты задаются в самих маршрутах."""
    if request.url.path.startswith(settings.api_prefix):
        await check_rate_limit(request, "global", settings.rate_limit_default_per_minute)
    return await call_next(request)


@app.get("/health", tags=["Служебное"], summary="Проверка работоспособности")
async def health() -> dict[str, object]:
    database_ok = False
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        database_ok = True
    except Exception:  # noqa: BLE001 — состояние показываем, а не падаем
        database_ok = False

    redis_ok = await redis_ping()
    return {
        "status": "ok" if database_ok else "degraded",
        "version": __version__,
        "database": "доступна" if database_ok else "недоступна",
        "redis": "доступен" if redis_ok else "недоступен",
    }


app.include_router(api_router, prefix=settings.api_prefix)
