"""Настройки приложения. Все значения читаются из переменных окружения."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---------- Общее ----------
    app_name: str = "DzenPilot"
    app_env: Literal["development", "staging", "production", "test"] = "development"
    app_debug: bool = True
    api_prefix: str = "/api/v1"

    # ---------- База данных ----------
    postgres_user: str = "dzenpilot"
    postgres_password: str = "dzenpilot"
    postgres_db: str = "dzenpilot"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    database_url: str | None = None

    # ---------- Redis и очередь ----------
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # ---------- Безопасность ----------
    secret_key: str = "insecure-development-key-change-me"
    app_encryption_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30
    cookie_secure: bool = False
    cookie_domain: str | None = None
    access_cookie_name: str = "dp_access"
    refresh_cookie_name: str = "dp_refresh"

    # Хранится строкой, а не списком: значения из .env вида
    # "http://a,http://b" библиотека настроек пытается разобрать как JSON
    # и падает ещё до валидации. Разбор делается в свойстве cors_origins.
    cors_origins_raw: str = Field(
        default="http://localhost:3000",
        validation_alias="CORS_ORIGINS",
    )

    # ---------- Ограничение частоты ----------
    rate_limit_default_per_minute: int = 120
    rate_limit_auth_per_minute: int = 10
    rate_limit_ai_per_minute: int = 20

    # ---------- ИИ ----------
    ai_default_provider: Literal["anthropic", "openai", "gemini", "local"] = "anthropic"
    ai_default_model: str = "claude-sonnet-5"
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    gemini_api_key: str | None = None
    local_ai_base_url: str | None = None
    ai_request_timeout_seconds: int = 180

    # ---------- Тестовые данные ----------
    seed_demo_data: bool = True
    seed_user_email: str = "demo@dzenpilot.ru"
    seed_user_password: str = "demo12345"

    @property
    def cors_origins(self) -> list[str]:
        """CORS_ORIGINS задаётся строкой через запятую."""
        return [item.strip() for item in self.cors_origins_raw.split(",") if item.strip()]

    @field_validator("cookie_domain", mode="before")
    @classmethod
    def _empty_domain_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @property
    def sqlalchemy_url(self) -> str:
        """Асинхронная строка подключения для SQLAlchemy."""
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def alembic_url(self) -> str:
        """Синхронная строка подключения для миграций Alembic."""
        return self.sqlalchemy_url.replace("+asyncpg", "")

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
