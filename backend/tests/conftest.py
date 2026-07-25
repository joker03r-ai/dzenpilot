"""Общая настройка тестов.

Тесты работают с отдельной базой `<POSTGRES_DB>_test`, которая создаётся
автоматически и очищается перед каждым тестом.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")

from app.core.config import settings  # noqa: E402
from app.db.base import target_metadata  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402

TEST_DB_NAME = f"{settings.postgres_db}_test"
TEST_DB_URL = os.getenv(
    "TEST_DATABASE_URL",
    (
        f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password}"
        f"@{settings.postgres_host}:{settings.postgres_port}/{TEST_DB_NAME}"
    ),
)
ADMIN_DB_URL = (
    f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password}"
    f"@{settings.postgres_host}:{settings.postgres_port}/postgres"
)


@pytest.fixture(scope="session")
async def engine():
    admin_engine = create_async_engine(ADMIN_DB_URL, isolation_level="AUTOCOMMIT")
    try:
        async with admin_engine.connect() as connection:
            from sqlalchemy import text

            exists = await connection.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": TEST_DB_NAME}
            )
            if not exists:
                await connection.execute(text(f'CREATE DATABASE "{TEST_DB_NAME}"'))
    finally:
        await admin_engine.dispose()

    test_engine = create_async_engine(TEST_DB_URL, poolclass=None)
    async with test_engine.begin() as connection:
        await connection.run_sync(target_metadata.drop_all)
        await connection.run_sync(target_metadata.create_all)

    yield test_engine
    await test_engine.dispose()


@pytest.fixture
async def session(engine) -> AsyncIterator[AsyncSession]:
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        yield db


@pytest.fixture(autouse=True)
async def clean_tables(engine):
    """Перед каждым тестом база пустая."""
    async with engine.begin() as connection:
        for table in reversed(target_metadata.sorted_tables):
            await connection.execute(table.delete())
    yield


@pytest.fixture
async def client(engine) -> AsyncIterator[AsyncClient]:
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        async with factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client
    app.dependency_overrides.clear()


@pytest.fixture
def register_payload() -> dict[str, str]:
    return {
        "email": "tester@example.com",
        "password": "verysecret123",
        "full_name": "Тестовый автор",
        "project_name": "Тестовый канал",
    }
