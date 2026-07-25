"""Фабрика провайдеров ИИ.

Модель выбирается в настройках проекта. Ключ берётся из интеграции проекта
(зашифрован в базе), а если её нет — из переменных окружения.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import AIProvider
from app.ai.providers.anthropic import AnthropicProvider
from app.ai.providers.gemini import GeminiProvider
from app.ai.providers.local import LocalProvider
from app.ai.providers.openai import OpenAIProvider
from app.core.config import settings
from app.core.crypto import decrypt_secret
from app.models.ai import AIProviderSettings
from app.models.enums import AIProviderName, IntegrationKind
from app.models.integration import Integration

PROVIDER_CLASSES: dict[str, type[AIProvider]] = {
    AIProviderName.ANTHROPIC: AnthropicProvider,
    AIProviderName.OPENAI: OpenAIProvider,
    AIProviderName.GEMINI: GeminiProvider,
    AIProviderName.LOCAL: LocalProvider,
}

INTEGRATION_BY_PROVIDER: dict[str, IntegrationKind] = {
    AIProviderName.ANTHROPIC: IntegrationKind.ANTHROPIC,
    AIProviderName.OPENAI: IntegrationKind.OPENAI,
    AIProviderName.GEMINI: IntegrationKind.GEMINI,
}

# Каталог для раздела «Настройки» — что можно выбрать в интерфейсе.
PROVIDER_CATALOG: list[dict] = [
    {
        "provider": AIProviderName.ANTHROPIC,
        "title": "Anthropic Claude",
        "description": "Основная модель сервиса. Лучше всего подходит для длинных статей.",
        "models": [
            {"id": "claude-opus-5", "title": "Claude Opus 5 — максимальное качество"},
            {"id": "claude-sonnet-5", "title": "Claude Sonnet 5 — баланс качества и цены",
             "recommended": True},
            {"id": "claude-haiku-4-5-20251001", "title": "Claude Haiku 4.5 — самый быстрый"},
        ],
    },
    {
        "provider": AIProviderName.OPENAI,
        "title": "OpenAI",
        "description": "Резервный провайдер. Подключается своим ключом.",
        "models": [
            {"id": "gpt-4o", "title": "GPT-4o"},
            {"id": "gpt-4o-mini", "title": "GPT-4o mini"},
        ],
    },
    {
        "provider": AIProviderName.GEMINI,
        "title": "Google Gemini",
        "description": "Резервный провайдер. Подключается своим ключом.",
        "models": [
            {"id": "gemini-1.5-pro", "title": "Gemini 1.5 Pro"},
            {"id": "gemini-1.5-flash", "title": "Gemini 1.5 Flash"},
        ],
    },
    {
        "provider": AIProviderName.LOCAL,
        "title": "Локальная модель",
        "description": "Ollama, LM Studio или vLLM с OpenAI-совместимым интерфейсом.",
        "models": [{"id": "llama3.1", "title": "Любая модель вашего сервера"}],
    },
]


def env_key_for(provider: str) -> str | None:
    return {
        AIProviderName.ANTHROPIC: settings.anthropic_api_key,
        AIProviderName.OPENAI: settings.openai_api_key,
        AIProviderName.GEMINI: settings.gemini_api_key,
        AIProviderName.LOCAL: None,
    }.get(provider)


def build_provider(provider: str, model: str, api_key: str | None, base_url: str | None = None
                   ) -> AIProvider:
    provider_class = PROVIDER_CLASSES.get(provider)
    if provider_class is None:
        raise ValueError(f"Неизвестный провайдер ИИ: {provider}")
    return provider_class(api_key=api_key, model=model, base_url=base_url)


async def get_project_api_key(
    db: AsyncSession, project_id: uuid.UUID, provider: str
) -> str | None:
    """Ключ проекта из интеграции, иначе — глобальный ключ из окружения."""
    kind = INTEGRATION_BY_PROVIDER.get(provider)
    if kind is not None:
        result = await db.execute(
            select(Integration).where(
                Integration.project_id == project_id,
                Integration.kind == kind,
                Integration.is_active.is_(True),
            )
        )
        integration = result.scalars().first()
        if integration and integration.credentials_encrypted:
            key = decrypt_secret(integration.credentials_encrypted)
            if key:
                return key
    return env_key_for(provider)


async def get_project_provider(db: AsyncSession, project_id: uuid.UUID) -> AIProvider:
    """Провайдер, настроенный для проекта, с подставленным ключом."""
    result = await db.execute(
        select(AIProviderSettings)
        .where(AIProviderSettings.project_id == project_id)
        .order_by(AIProviderSettings.is_default.desc(), AIProviderSettings.created_at.desc())
    )
    config = result.scalars().first()
    provider_name = config.provider if config else settings.ai_default_provider
    model = config.model if config else settings.ai_default_model

    api_key = await get_project_api_key(db, project_id, provider_name)
    base_url = settings.local_ai_base_url if provider_name == AIProviderName.LOCAL else None
    return build_provider(provider_name, model, api_key, base_url)
