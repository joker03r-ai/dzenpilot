"""Модуль Publisher.

Сервис поддерживает только законные способы публикации: официальное API,
если пользователь его подключил, партнёрский сервис, экспорт файла,
копирование отформатированного текста и напоминание о ручной публикации.

Обхода защиты, подмены браузера, капчи и чужих cookies здесь нет и не будет.
Публикация никогда не выполняется без явного подтверждения пользователя.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError, ValidationAppError
from app.models.article import Article, ArticleImage
from app.models.calendar import ScheduledPublication
from app.models.enums import (
    RU_LABELS,
    ArticleStatus,
    IntegrationKind,
    PublicationMethod,
    PublicationResult,
    ScheduleStatus,
)
from app.models.integration import Integration
from app.models.publication import PublicationLog
from app.schemas.publication import (
    PreflightCheck,
    PreflightResponse,
    PublishRequest,
    PublishResponse,
)
from app.services import calendar_service, export_service

# Способы, которые работают всегда — они не требуют внешнего подключения
ALWAYS_AVAILABLE = [
    PublicationMethod.MANUAL_EXPORT,
    PublicationMethod.COPY_FORMATTED,
    PublicationMethod.FILE_EXPORT,
    PublicationMethod.REMINDER,
]


def _method_label(method: PublicationMethod) -> str:
    return RU_LABELS["publication_method"].get(method, method)


async def _has_cover(db: AsyncSession, article_id: uuid.UUID) -> bool:
    return bool(
        await db.scalar(
            select(func.count())
            .select_from(ArticleImage)
            .where(ArticleImage.article_id == article_id, ArticleImage.is_cover.is_(True))
        )
    )


async def _channel_integration(
    db: AsyncSession, project_id: uuid.UUID
) -> Integration | None:
    result = await db.execute(
        select(Integration).where(
            Integration.project_id == project_id,
            Integration.kind == IntegrationKind.DZEN_CHANNEL,
            Integration.is_active.is_(True),
        )
    )
    return result.scalars().first()


async def preflight(
    db: AsyncSession, schedule: ScheduledPublication
) -> PreflightResponse:
    """Проверки перед публикацией. Ничего не отправляет — только смотрит."""
    article = await db.get(Article, schedule.article_id)
    if article is None:
        raise NotFoundError("Статья не найдена")

    has_cover = await _has_cover(db, article.id)
    channel = await _channel_integration(db, schedule.project_id)
    local = calendar_service.to_local(schedule.scheduled_at, schedule.timezone)

    checks = [
        PreflightCheck(
            code="body",
            label="Текст статьи заполнен",
            passed=bool(article.body_markdown and article.body_markdown.strip()),
            detail=(
                f"{article.word_count or 0} слов"
                if article.body_markdown
                else "Текста нет. Вернитесь в редактор и сгенерируйте статью."
            ),
        ),
        PreflightCheck(
            code="title",
            label="Заголовок заполнен",
            passed=bool(article.title and len(article.title.strip()) >= 10),
            detail=article.title or "Заголовок пустой",
        ),
        PreflightCheck(
            code="cover",
            label="Обложка добавлена",
            passed=has_cover,
            detail=(
                "Обложка есть"
                if has_cover
                else "Обложки нет. Дзен показывает её в ленте — без неё переходов будет меньше."
            ),
        ),
        PreflightCheck(
            code="channel",
            label="Канал выбран",
            passed=channel is not None or schedule.channel_id is not None,
            detail=(
                f"Канал: {channel.title}"
                if channel
                else "Канал не подключён. Добавьте его в разделе «Интеграции»."
            ),
        ),
        PreflightCheck(
            code="datetime",
            label="Дата и время назначены",
            passed=True,
            detail=(
                f"{local.strftime('%d.%m.%Y в %H:%M')} "
                f"({calendar_service.timezone_label(schedule.timezone)})"
            ),
        ),
        PreflightCheck(
            code="connection",
            label="Способ публикации доступен",
            passed=True,
            detail=(
                "Официальное API не подключено, поэтому доступны экспорт файла, "
                "копирование текста и напоминание."
                if channel is None
                else "Канал подключён. Доступны экспорт и копирование текста."
            ),
        ),
        PreflightCheck(
            code="confirmation",
            label="Публикация подтверждена вами",
            passed=schedule.confirmed_by_user,
            detail=(
                "Подтверждено"
                if schedule.confirmed_by_user
                else "Нажмите «Подтвердить» — без этого публикация не выполняется."
            ),
        ),
    ]

    # Обложка не блокирует ручной экспорт: файл можно отдать и без неё
    blocking = {"body", "title", "confirmation"}
    ready = all(check.passed for check in checks if check.code in blocking)
    failed = [check.label for check in checks if not check.passed]

    methods = [
        {"value": method.value, "label": _method_label(method)} for method in ALWAYS_AVAILABLE
    ]

    return PreflightResponse(
        checks=checks,
        ready=ready,
        available_methods=methods,
        message=(
            "Проверки пройдены. Выберите способ публикации."
            if ready
            else "Не выполнено: " + ", ".join(failed)
        ),
    )


async def _last_success(
    db: AsyncSession, article_id: uuid.UUID
) -> PublicationLog | None:
    result = await db.execute(
        select(PublicationLog)
        .where(
            PublicationLog.article_id == article_id,
            PublicationLog.result == PublicationResult.SUCCESS,
        )
        .order_by(PublicationLog.created_at.desc())
        .limit(1)
    )
    return result.scalars().first()


async def _attempt_number(db: AsyncSession, article_id: uuid.UUID) -> int:
    count = await db.scalar(
        select(func.count())
        .select_from(PublicationLog)
        .where(PublicationLog.article_id == article_id)
    )
    return int(count or 0) + 1


async def publish(
    db: AsyncSession, schedule: ScheduledPublication, request: PublishRequest
) -> PublishResponse:
    """Выполняет публикацию выбранным способом и пишет результат в журнал."""
    article = await db.get(Article, schedule.article_id)
    if article is None:
        raise NotFoundError("Статья не найдена")

    if not schedule.confirmed_by_user:
        raise ValidationAppError(
            "Публикация не подтверждена. Нажмите «Подтвердить» в календаре — "
            "сервис не публикует материалы самостоятельно."
        )
    if not (article.body_markdown or "").strip():
        raise ValidationAppError("У статьи нет текста. Вернитесь в редактор.")

    # Защита от дубля: повторная публикация только по явному запросу
    previous = await _last_success(db, article.id)
    if previous is not None and not request.force:
        raise ConflictError(
            "Эта статья уже была опубликована "
            f"{previous.finished_at.strftime('%d.%m.%Y в %H:%M') if previous.finished_at else ''}. "
            "Чтобы выполнить повторно, включите принудительный режим."
        )

    started = datetime.now(UTC)
    attempt = await _attempt_number(db, article.id)
    schedule.status = ScheduleStatus.PUBLISHING
    schedule.attempts += 1
    await db.flush()

    method = request.method
    payload: dict[str, object] = {}
    result = PublicationResult.SUCCESS
    error_message: str | None = None
    published_url: str | None = None
    next_step = ""

    try:
        if method in (PublicationMethod.MANUAL_EXPORT, PublicationMethod.FILE_EXPORT):
            payload = {
                "markdown": export_service.build_markdown(article),
                "html": export_service.build_html(article),
                "filename_markdown": f"{article.slug or 'article'}.md",
                "filename_html": f"{article.slug or 'article'}.html",
            }
            next_step = (
                "Файл готов. Откройте редактор Дзена, создайте публикацию "
                "и вставьте содержимое файла."
            )

        elif method == PublicationMethod.COPY_FORMATTED:
            payload = {"plain": export_service.build_plain(article)}
            next_step = (
                "Текст готов к копированию. Вставьте его в редактор Дзена "
                "и проверьте разметку."
            )

        elif method == PublicationMethod.REMINDER:
            local = calendar_service.to_local(schedule.scheduled_at, schedule.timezone)
            payload = {
                "remind_at": schedule.scheduled_at.isoformat(),
                "local_time": local.strftime("%d.%m.%Y %H:%M"),
                "timezone": calendar_service.timezone_label(schedule.timezone),
            }
            next_step = (
                f"Напоминание сохранено на {local.strftime('%d.%m.%Y в %H:%M')} "
                f"({calendar_service.timezone_label(schedule.timezone)})."
            )

        elif method in (
            PublicationMethod.OFFICIAL_API,
            PublicationMethod.PARTNER_SERVICE,
        ):
            # Официальный способ подключается пользователем. Пока подключения нет,
            # сервис честно сообщает об этом и не пытается обойти платформу.
            channel = await _channel_integration(db, schedule.project_id)
            result = PublicationResult.SKIPPED
            error_message = (
                "Официальное API Дзена для этого канала не подключено. "
                "Воспользуйтесь экспортом файла или копированием текста, "
                "а когда доступ появится, подключите его в разделе «Интеграции»."
            )
            payload = {"channel_configured": channel is not None}
            next_step = "Выберите способ «Ручной экспорт» или «Копирование текста»."

        else:
            raise ValidationAppError("Неизвестный способ публикации")

    except ValidationAppError:
        raise
    except Exception as exc:  # noqa: BLE001 — текст ошибки показываем пользователю
        result = PublicationResult.ERROR
        error_message = f"Не удалось подготовить публикацию: {exc}"
        next_step = "Попробуйте повторить или выберите другой способ."

    finished = datetime.now(UTC)

    log = PublicationLog(
        scheduled_publication_id=schedule.id,
        article_id=article.id,
        project_id=schedule.project_id,
        method=method,
        result=result,
        published_url=published_url,
        response_payload={
            key: value
            for key, value in payload.items()
            # Тексты статьи в журнал не дублируем: они и так есть в самой статье
            if key not in {"markdown", "html", "plain"}
        },
        error_message=error_message,
        attempt_number=attempt,
        started_at=started,
        finished_at=finished,
    )
    db.add(log)

    if result == PublicationResult.SUCCESS:
        schedule.status = ScheduleStatus.PUBLISHED
        if method != PublicationMethod.REMINDER:
            article.status = ArticleStatus.PUBLISHED
            article.published_at = finished
    elif result == PublicationResult.ERROR:
        schedule.status = ScheduleStatus.FAILED
        article.status = ArticleStatus.FAILED
    else:
        schedule.status = ScheduleStatus.READY

    await db.flush()

    return PublishResponse(
        log_id=log.id,
        method=method,
        method_label=_method_label(method),
        result=result,
        published_url=published_url,
        error_message=error_message,
        can_retry=result != PublicationResult.SUCCESS,
        payload=payload,
        message=(
            "Материал подготовлен."
            if result == PublicationResult.SUCCESS
            else error_message or "Публикация не выполнена."
        ),
        next_step=next_step,
    )


async def list_logs(
    db: AsyncSession, project_id: uuid.UUID, limit: int = 50
) -> list[tuple[PublicationLog, str]]:
    result = await db.execute(
        select(PublicationLog, Article.title)
        .join(Article, Article.id == PublicationLog.article_id)
        .where(PublicationLog.project_id == project_id)
        .order_by(PublicationLog.created_at.desc())
        .limit(min(limit, 200))
    )
    return [(log, title) for log, title in result.all()]
