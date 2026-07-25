"""Подключения внешних сервисов. Ключи шифруются и наружу не отдаются."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.factory import build_provider
from app.core.crypto import SecretDecryptionError, decrypt_secret, encrypt_secret, mask_secret
from app.core.errors import ConflictError, NotFoundError
from app.models.enums import RU_LABELS, AIProviderName, IntegrationKind
from app.models.integration import Integration
from app.schemas.integration import (
    IntegrationCreate,
    IntegrationResponse,
    IntegrationTestResult,
    IntegrationUpdate,
)

AI_KINDS = {
    IntegrationKind.ANTHROPIC: AIProviderName.ANTHROPIC,
    IntegrationKind.OPENAI: AIProviderName.OPENAI,
    IntegrationKind.GEMINI: AIProviderName.GEMINI,
}

DEFAULT_TEST_MODEL = {
    IntegrationKind.ANTHROPIC: "claude-sonnet-5",
    IntegrationKind.OPENAI: "gpt-4o-mini",
    IntegrationKind.GEMINI: "gemini-1.5-flash",
}


def to_response(integration: Integration) -> IntegrationResponse:
    """Собирает ответ API: вместо ключа — маска."""
    mask = "не задан"
    if integration.credentials_encrypted:
        try:
            mask = mask_secret(decrypt_secret(integration.credentials_encrypted))
        except SecretDecryptionError:
            mask = "ключ повреждён, подключите заново"
    return IntegrationResponse(
        id=integration.id,
        project_id=integration.project_id,
        kind=integration.kind,
        kind_label=RU_LABELS["integration_kind"].get(integration.kind, integration.kind),
        title=integration.title,
        key_mask=mask,
        has_credentials=bool(integration.credentials_encrypted),
        config=integration.config,
        is_active=integration.is_active,
        last_check_at=integration.last_check_at,
        last_check_result=integration.last_check_result,
        created_at=integration.created_at,
    )


async def list_integrations(db: AsyncSession, project_id: uuid.UUID) -> list[Integration]:
    result = await db.execute(
        select(Integration)
        .where(Integration.project_id == project_id)
        .order_by(Integration.created_at)
    )
    return list(result.scalars().all())


async def get_integration(
    db: AsyncSession, project_id: uuid.UUID, integration_id: uuid.UUID
) -> Integration:
    integration = await db.get(Integration, integration_id)
    if integration is None or integration.project_id != project_id:
        raise NotFoundError("Подключение не найдено")
    return integration


async def create_integration(
    db: AsyncSession, project_id: uuid.UUID, data: IntegrationCreate
) -> Integration:
    exists = await db.execute(
        select(Integration).where(
            Integration.project_id == project_id,
            Integration.kind == data.kind,
            Integration.title == data.title,
        )
    )
    if exists.scalars().first() is not None:
        raise ConflictError("Такое подключение уже добавлено. Измените существующее.")

    integration = Integration(
        project_id=project_id,
        kind=data.kind,
        title=data.title,
        credentials_encrypted=encrypt_secret(data.api_key) if data.api_key else None,
        config=data.config,
        is_active=True,
    )
    db.add(integration)
    await db.flush()
    return integration


async def update_integration(
    db: AsyncSession, integration: Integration, data: IntegrationUpdate
) -> Integration:
    payload = data.model_dump(exclude_unset=True)
    api_key = payload.pop("api_key", None)
    if api_key:
        integration.credentials_encrypted = encrypt_secret(api_key)
    for field_name, value in payload.items():
        setattr(integration, field_name, value)
    await db.flush()
    return integration


async def delete_integration(db: AsyncSession, integration: Integration) -> None:
    await db.delete(integration)
    await db.flush()


async def test_integration(db: AsyncSession, integration: Integration) -> IntegrationTestResult:
    """Проверка подключения. Для моделей ИИ делается короткий запрос."""
    checked_at = datetime.now(UTC)

    if integration.kind in AI_KINDS:
        try:
            api_key = decrypt_secret(integration.credentials_encrypted)
        except SecretDecryptionError as exc:
            return await _save_check(db, integration, False, str(exc), checked_at)
        if not api_key:
            return await _save_check(
                db, integration, False, "Ключ не задан. Введите его и сохраните.", checked_at
            )
        model = integration.config.get("model") or DEFAULT_TEST_MODEL[integration.kind]
        provider = build_provider(AI_KINDS[integration.kind], model, api_key)
        ok, message = await provider.healthcheck()
        return await _save_check(db, integration, ok, message, checked_at)

    if integration.kind == IntegrationKind.WEBHOOK:
        url = integration.config.get("url")
        ok = bool(url)
        message = (
            f"Адрес сохранён: {url}" if ok else "Укажите адрес webhook в настройках подключения"
        )
        return await _save_check(db, integration, ok, message, checked_at)

    if integration.kind == IntegrationKind.DZEN_CHANNEL:
        url = integration.config.get("channel_url")
        ok = bool(url)
        message = (
            "Канал сохранён. Публикация выполняется официальным способом "
            "или через экспорт готовой статьи."
            if ok
            else "Укажите ссылку на канал Дзена"
        )
        return await _save_check(db, integration, ok, message, checked_at)

    has_data = bool(integration.credentials_encrypted or integration.config)
    message = (
        "Настройки сохранены. Автоматическая проверка для этого сервиса недоступна."
        if has_data
        else "Заполните настройки подключения"
    )
    return await _save_check(db, integration, has_data, message, checked_at)


async def _save_check(
    db: AsyncSession,
    integration: Integration,
    ok: bool,
    message: str,
    checked_at: datetime,
) -> IntegrationTestResult:
    integration.last_check_at = checked_at
    integration.last_check_result = message[:1000]
    await db.flush()
    return IntegrationTestResult(ok=ok, message=message, checked_at=checked_at)
