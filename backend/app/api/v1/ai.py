"""Настройки модели ИИ и тестовый запрос."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select

from app.ai.base import AIRequest
from app.ai.factory import PROVIDER_CATALOG, build_provider, get_project_api_key
from app.api.deps import CurrentUser, DbSession
from app.core.config import settings
from app.core.rate_limit import ai_rate_limit
from app.models.ai import AIProviderSettings, AIUsage
from app.models.enums import AIProviderName, UserRole
from app.models.project import Project
from app.schemas.ai import (
    AISettingsResponse,
    AISettingsUpdate,
    AITestRequest,
    AITestResponse,
    ModelInfo,
    ProviderInfo,
)
from app.services import project_service

router = APIRouter()


@router.get("/providers", response_model=list[ProviderInfo], summary="Доступные модели")
async def providers(_: CurrentUser) -> list[ProviderInfo]:
    """Список провайдеров. `available` показывает, задан ли глобальный ключ."""
    env_keys = {
        AIProviderName.ANTHROPIC: bool(settings.anthropic_api_key),
        AIProviderName.OPENAI: bool(settings.openai_api_key),
        AIProviderName.GEMINI: bool(settings.gemini_api_key),
        AIProviderName.LOCAL: bool(settings.local_ai_base_url),
    }
    return [
        ProviderInfo(
            provider=item["provider"],
            title=item["title"],
            description=item["description"],
            available=env_keys.get(item["provider"], False),
            models=[ModelInfo(**model) for model in item["models"]],
        )
        for item in PROVIDER_CATALOG
    ]


async def _get_settings(db: DbSession, project_id: uuid.UUID) -> AIProviderSettings | None:
    result = await db.execute(
        select(AIProviderSettings)
        .where(AIProviderSettings.project_id == project_id)
        .order_by(AIProviderSettings.is_default.desc(), AIProviderSettings.created_at.desc())
    )
    return result.scalars().first()


@router.get("/settings", response_model=AISettingsResponse, summary="Настройки ИИ проекта")
async def get_ai_settings(
    db: DbSession, user: CurrentUser, project_id: uuid.UUID = Query(...)
) -> AISettingsResponse:
    project = await project_service.get_project_for_user(db, project_id, user.id)
    config = await _get_settings(db, project.id)
    provider = config.provider if config else AIProviderName(settings.ai_default_provider)
    key = await get_project_api_key(db, project.id, provider)
    return AISettingsResponse(
        id=config.id if config else None,
        project_id=project.id,
        provider=provider,
        model=config.model if config else settings.ai_default_model,
        temperature=config.temperature if config else 0.7,
        max_tokens=config.max_tokens if config else 4096,
        key_configured=bool(key),
    )


@router.put("/settings", response_model=AISettingsResponse, summary="Сохранить настройки ИИ")
async def update_ai_settings(
    data: AISettingsUpdate,
    db: DbSession,
    user: CurrentUser,
    project_id: uuid.UUID = Query(...),
) -> AISettingsResponse:
    project: Project = await project_service.get_project_for_user(
        db, project_id, user.id, min_role=UserRole.EDITOR
    )
    existing = await db.execute(
        select(AIProviderSettings).where(AIProviderSettings.project_id == project.id)
    )
    for item in existing.scalars().all():
        item.is_default = False

    result = await db.execute(
        select(AIProviderSettings).where(
            AIProviderSettings.project_id == project.id,
            AIProviderSettings.provider == data.provider,
            AIProviderSettings.model == data.model,
        )
    )
    config = result.scalars().first()
    if config is None:
        config = AIProviderSettings(project_id=project.id, provider=data.provider, model=data.model)
        db.add(config)

    config.temperature = data.temperature
    config.max_tokens = data.max_tokens
    config.is_default = True
    await db.commit()
    await db.refresh(config)

    key = await get_project_api_key(db, project.id, config.provider)
    return AISettingsResponse(
        id=config.id,
        project_id=project.id,
        provider=config.provider,
        model=config.model,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        key_configured=bool(key),
    )


@router.post(
    "/test",
    response_model=AITestResponse,
    summary="Тестовый запрос к модели",
    dependencies=[Depends(ai_rate_limit)],
)
async def test_model(
    data: AITestRequest,
    db: DbSession,
    user: CurrentUser,
    project_id: uuid.UUID = Query(..., description="Проект, чьи настройки проверяем"),
) -> AITestResponse:
    project = await project_service.get_project_for_user(
        db, project_id, user.id, min_role=UserRole.EDITOR
    )
    config = await _get_settings(db, project.id)
    provider_name = config.provider if config else AIProviderName(settings.ai_default_provider)
    model = config.model if config else settings.ai_default_model
    api_key = await get_project_api_key(db, project.id, provider_name)

    provider = build_provider(
        provider_name,
        model,
        api_key,
        settings.local_ai_base_url if provider_name == AIProviderName.LOCAL else None,
    )
    response = await provider.complete(AIRequest(prompt=data.prompt, max_tokens=512))

    db.add(
        AIUsage(
            project_id=project.id,
            provider=response.provider,
            model=response.model,
            operation="test",
            tokens_input=response.tokens_input,
            tokens_output=response.tokens_output,
            cost_usd=response.cost_usd,
        )
    )
    await db.commit()

    return AITestResponse(
        ok=True,
        provider=response.provider,
        model=response.model,
        text=response.text,
        tokens_input=response.tokens_input,
        tokens_output=response.tokens_output,
    )
