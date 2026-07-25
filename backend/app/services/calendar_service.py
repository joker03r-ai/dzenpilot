"""Контент-календарь: планирование, перенос, копирование, отмена.

Время публикации всегда хранится в базе в UTC. Часовой пояс, выбранный
пользователем, хранится рядом отдельным полем — именно в нём время
показывается в интерфейсе. Так перенос между поясами не теряет момент времени.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, ValidationAppError
from app.models.article import Article
from app.models.calendar import ScheduledPublication
from app.models.enums import RU_LABELS, ArticleStatus, ScheduleStatus
from app.schemas.calendar import (
    CalendarResponse,
    CalendarView,
    ScheduleCreate,
    ScheduleResponse,
    ScheduleUpdate,
)
from app.services.timezones import DEFAULT_TIMEZONE, TIMEZONE_CHOICES


def timezone_label(name: str) -> str:
    for item in TIMEZONE_CHOICES:
        if item["value"] == name:
            return item["label"]
    return name


def to_utc(local_value: str, timezone_name: str) -> datetime:
    """Местные дата и время -> момент в UTC."""
    cleaned = local_value.replace("Z", "").split("+")[0].strip()
    try:
        naive = datetime.fromisoformat(cleaned)
    except ValueError as exc:
        raise ValidationAppError(
            "Дата и время указаны неверно. Ожидается формат 2026-08-01T10:00."
        ) from exc

    # Если время пришло уже со сдвигом, приводим к UTC напрямую
    if naive.tzinfo is not None:
        return naive.astimezone(UTC)
    return naive.replace(tzinfo=ZoneInfo(timezone_name)).astimezone(UTC)


def to_local(moment: datetime, timezone_name: str) -> datetime:
    """Момент в UTC -> местное время выбранного пояса."""
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    return moment.astimezone(ZoneInfo(timezone_name))


def to_response(schedule: ScheduledPublication, article: Article) -> ScheduleResponse:
    local = to_local(schedule.scheduled_at, schedule.timezone)
    return ScheduleResponse(
        id=schedule.id,
        project_id=schedule.project_id,
        article_id=schedule.article_id,
        article_title=article.title,
        article_status=RU_LABELS["article_status"].get(article.status, article.status),
        channel_id=schedule.channel_id,
        scheduled_at=schedule.scheduled_at,
        local_datetime=local.strftime("%Y-%m-%dT%H:%M"),
        local_date=local.date(),
        local_time=local.strftime("%H:%M"),
        timezone=schedule.timezone,
        timezone_label=timezone_label(schedule.timezone),
        repeat_rule=schedule.repeat_rule,
        note=schedule.note,
        confirmed_by_user=schedule.confirmed_by_user,
        status=schedule.status,
        status_label=RU_LABELS["schedule_status"].get(schedule.status, schedule.status),
        attempts=schedule.attempts,
        created_at=schedule.created_at,
    )


def period_bounds(view: CalendarView, anchor: date) -> tuple[date, date]:
    """Границы периода для выбранного вида календаря."""
    if view == "day":
        return anchor, anchor
    if view == "week":
        start = anchor - timedelta(days=anchor.weekday())
        return start, start + timedelta(days=6)
    if view == "month":
        start = anchor.replace(day=1)
        next_month = (start + timedelta(days=32)).replace(day=1)
        return start, next_month - timedelta(days=1)
    # Список: ближайшие 90 дней
    return anchor, anchor + timedelta(days=90)


def _repeat_delta(rule: str, index: int) -> timedelta:
    return {
        "daily": timedelta(days=index),
        "weekly": timedelta(weeks=index),
        "biweekly": timedelta(weeks=2 * index),
        "monthly": timedelta(days=30 * index),
    }.get(rule, timedelta())


async def _get_article(
    db: AsyncSession, project_id: uuid.UUID, article_id: uuid.UUID
) -> Article:
    article = await db.get(Article, article_id)
    if article is None or article.project_id != project_id or article.deleted_at:
        raise NotFoundError("Статья не найдена")
    return article


async def get_schedule(
    db: AsyncSession, project_id: uuid.UUID, schedule_id: uuid.UUID
) -> ScheduledPublication:
    schedule = await db.get(ScheduledPublication, schedule_id)
    if schedule is None or schedule.project_id != project_id:
        raise NotFoundError("Запись календаря не найдена")
    return schedule


async def list_calendar(
    db: AsyncSession,
    project_id: uuid.UUID,
    view: CalendarView,
    anchor: date,
    timezone_name: str,
) -> CalendarResponse:
    start, end = period_bounds(view, anchor)

    zone = ZoneInfo(timezone_name)
    start_utc = datetime.combine(start, datetime.min.time()).replace(tzinfo=zone).astimezone(UTC)
    end_utc = (
        datetime.combine(end, datetime.max.time()).replace(tzinfo=zone).astimezone(UTC)
    )

    result = await db.execute(
        select(ScheduledPublication, Article)
        .join(Article, Article.id == ScheduledPublication.article_id)
        .where(
            ScheduledPublication.project_id == project_id,
            ScheduledPublication.scheduled_at >= start_utc,
            ScheduledPublication.scheduled_at <= end_utc,
        )
        .order_by(ScheduledPublication.scheduled_at)
    )
    items = [to_response(schedule, article) for schedule, article in result.all()]

    waiting = sum(1 for item in items if not item.confirmed_by_user)
    note = (
        f"Время показано в поясе «{timezone_label(timezone_name)}». "
        + (
            f"Ждут вашего подтверждения: {waiting}. Без подтверждения публикация не выполняется."
            if waiting
            else "Все записи подтверждены."
        )
    )

    return CalendarResponse(
        view=view,
        period_start=start,
        period_end=end,
        timezone=timezone_name,
        timezone_label=timezone_label(timezone_name),
        items=items,
        note=note,
    )


async def create_schedule(
    db: AsyncSession, project_id: uuid.UUID, data: ScheduleCreate
) -> list[ScheduledPublication]:
    """Создаёт одну или несколько записей, если задано повторение."""
    article = await _get_article(db, project_id, data.article_id)
    base_moment = to_utc(data.local_datetime, data.timezone)

    count = data.repeat_count if data.repeat_rule != "none" else 1
    created: list[ScheduledPublication] = []

    for index in range(count):
        moment = base_moment + _repeat_delta(data.repeat_rule, index)

        # Защита от дубля: та же статья на то же время уже запланирована
        exists = await db.execute(
            select(ScheduledPublication).where(
                ScheduledPublication.article_id == article.id,
                ScheduledPublication.scheduled_at == moment,
                ScheduledPublication.status != ScheduleStatus.CANCELLED,
            )
        )
        if exists.scalars().first() is not None:
            continue

        schedule = ScheduledPublication(
            project_id=project_id,
            article_id=article.id,
            channel_id=data.channel_id,
            scheduled_at=moment,
            timezone=data.timezone,
            repeat_rule=data.repeat_rule if data.repeat_rule != "none" else None,
            note=data.note,
            confirmed_by_user=False,
            status=ScheduleStatus.PLANNED,
        )
        db.add(schedule)
        created.append(schedule)

    if not created:
        raise ValidationAppError(
            "Эта статья уже запланирована на указанное время. Выберите другую дату."
        )

    # Первая запись определяет плановую дату публикации статьи
    article.planned_publish_at = base_moment
    if article.status in (ArticleStatus.DRAFT, ArticleStatus.REVIEW, ArticleStatus.READY):
        article.status = ArticleStatus.SCHEDULED

    await db.flush()
    return created


async def update_schedule(
    db: AsyncSession, schedule: ScheduledPublication, data: ScheduleUpdate
) -> ScheduledPublication:
    payload = data.model_dump(exclude_unset=True)

    new_timezone = payload.pop("timezone", None) or schedule.timezone
    local_value = payload.pop("local_datetime", None)

    if local_value:
        schedule.scheduled_at = to_utc(local_value, new_timezone)
    elif new_timezone != schedule.timezone:
        # Сменили только пояс: показываем то же местное время в новом поясе
        old_local = to_local(schedule.scheduled_at, schedule.timezone)
        schedule.scheduled_at = to_utc(old_local.strftime("%Y-%m-%dT%H:%M"), new_timezone)

    schedule.timezone = new_timezone

    for field_name, value in payload.items():
        setattr(schedule, field_name, value)

    if local_value:
        article = await db.get(Article, schedule.article_id)
        if article is not None:
            article.planned_publish_at = schedule.scheduled_at

    await db.flush()
    return schedule


async def duplicate_schedule(
    db: AsyncSession, schedule: ScheduledPublication, days_offset: int = 7
) -> ScheduledPublication:
    copy = ScheduledPublication(
        project_id=schedule.project_id,
        article_id=schedule.article_id,
        channel_id=schedule.channel_id,
        scheduled_at=schedule.scheduled_at + timedelta(days=days_offset),
        timezone=schedule.timezone,
        repeat_rule=None,
        note=schedule.note,
        confirmed_by_user=False,
        status=ScheduleStatus.PLANNED,
    )
    db.add(copy)
    await db.flush()
    return copy


async def cancel_schedule(db: AsyncSession, schedule: ScheduledPublication) -> None:
    schedule.status = ScheduleStatus.CANCELLED
    schedule.confirmed_by_user = False

    article = await db.get(Article, schedule.article_id)
    if article is not None and article.status == ArticleStatus.SCHEDULED:
        remaining = await db.execute(
            select(ScheduledPublication).where(
                ScheduledPublication.article_id == article.id,
                ScheduledPublication.id != schedule.id,
                ScheduledPublication.status.in_(
                    [ScheduleStatus.PLANNED, ScheduleStatus.READY]
                ),
            )
        )
        if remaining.scalars().first() is None:
            article.status = ArticleStatus.READY
            article.planned_publish_at = None

    await db.flush()
