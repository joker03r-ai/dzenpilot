"""Данные главной страницы: показатели, шаги настройки и последняя активность."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, nulls_last, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.models.calendar import ScheduledPublication
from app.models.competitor import Competitor, CompetitorPublication
from app.models.enums import (
    RU_LABELS,
    ArticleStatus,
    IntegrationKind,
    PublicationResult,
    ScheduleStatus,
    TopicStatus,
)
from app.models.integration import Integration
from app.models.project import Project
from app.models.publication import PublicationLog
from app.models.topic import Topic, TopicScore
from app.models.user import User
from app.schemas.dashboard import (
    ActivityItem,
    DashboardCounters,
    DashboardResponse,
    SetupStep,
)


async def _count(db: AsyncSession, statement) -> int:
    return int(await db.scalar(select(func.count()).select_from(statement.subquery())) or 0)


async def build_dashboard(db: AsyncSession, project: Project, user: User) -> DashboardResponse:
    competitors = await _count(
        db,
        select(Competitor.id).where(
            Competitor.project_id == project.id, Competitor.deleted_at.is_(None)
        ),
    )
    topics = await _count(
        db,
        select(Topic.id).where(
            Topic.project_id == project.id,
            Topic.deleted_at.is_(None),
            Topic.status != TopicStatus.HIDDEN,
        ),
    )
    articles = await _count(
        db,
        select(Article.id).where(
            Article.project_id == project.id, Article.deleted_at.is_(None)
        ),
    )
    scheduled = await _count(
        db,
        select(ScheduledPublication.id).where(
            ScheduledPublication.project_id == project.id,
            ScheduledPublication.status.in_(
                [ScheduleStatus.PLANNED, ScheduleStatus.READY]
            ),
        ),
    )
    published = await _count(
        db,
        select(Article.id).where(
            Article.project_id == project.id,
            Article.status == ArticleStatus.PUBLISHED,
            Article.deleted_at.is_(None),
        ),
    )

    channel_connected = bool(
        await db.scalar(
            select(func.count())
            .select_from(Integration)
            .where(
                Integration.project_id == project.id,
                Integration.kind.in_(
                    [IntegrationKind.DZEN_CHANNEL, IntegrationKind.ANTHROPIC]
                ),
                Integration.is_active.is_(True),
            )
        )
    )

    steps = [
        SetupStep(
            code="competitors",
            title="Добавьте первых конкурентов",
            description=(
                "Выберите 3–5 каналов вашей тематики. Сервис разберёт их публикации "
                "и покажет, что у них работает."
            ),
            done=competitors > 0,
            progress=min(100, competitors * 33),
            action_label="Добавить конкурента",
            action_href="/competitors",
        ),
        SetupStep(
            code="topics",
            title="Найдите прибыльную тему",
            description=(
                "Укажите нишу и аудиторию — сервис подберёт темы с оценкой "
                "перспективности от 0 до 100."
            ),
            done=topics > 0,
            progress=min(100, topics * 20),
            action_label="Найти темы",
            action_href="/topics",
        ),
        SetupStep(
            code="article",
            title="Создайте первую статью",
            description="Пошаговый мастер: тема, структура, текст, проверка перед публикацией.",
            done=articles > 0,
            progress=min(100, articles * 50),
            action_label="Создать статью",
            action_href="/articles/new",
        ),
        SetupStep(
            code="channel",
            title="Подключите канал и модель ИИ",
            description=(
                "Введите ключ Claude и ссылку на канал Дзена. "
                "Ключи хранятся на сервере в зашифрованном виде."
            ),
            done=channel_connected,
            progress=100 if channel_connected else 0,
            action_label="Открыть интеграции",
            action_href="/integrations",
        ),
        SetupStep(
            code="schedule",
            title="Запланируйте публикацию",
            description="Выберите дату, время и часовой пояс. Публикация всегда требует подтверждения.",
            done=scheduled > 0,
            progress=100 if scheduled > 0 else 0,
            action_label="Открыть календарь",
            action_href="/calendar",
        ),
    ]
    setup_progress = round(sum(1 for step in steps if step.done) / len(steps) * 100)

    return DashboardResponse(
        project_id=project.id,
        project_name=project.name,
        user_name=user.full_name or user.email,
        counters=DashboardCounters(
            competitors=competitors,
            topics=topics,
            articles=articles,
            scheduled=scheduled,
            published=published,
        ),
        setup_progress=setup_progress,
        steps=steps,
        activity=await _build_activity(db, project.id),
    )


async def _build_activity(db: AsyncSession, project_id: uuid.UUID) -> list[ActivityItem]:
    items: list[ActivityItem] = []

    top_topics = await db.execute(
        select(Topic, TopicScore.total_score)
        .join(TopicScore, TopicScore.topic_id == Topic.id)
        .where(Topic.project_id == project_id, Topic.deleted_at.is_(None))
        .order_by(TopicScore.total_score.desc(), Topic.created_at.desc())
        .limit(3)
    )
    for topic, score in top_topics.all():
        items.append(
            ActivityItem(
                kind="topic",
                title=topic.title,
                subtitle=f"Перспективная тема, оценка {score} из 100",
                href=f"/topics/{topic.id}",
                level="success",
                happened_at=topic.created_at,
                entity_id=topic.id,
            )
        )

    recent_articles = await db.execute(
        select(Article)
        .where(Article.project_id == project_id, Article.deleted_at.is_(None))
        .order_by(Article.updated_at.desc())
        .limit(3)
    )
    for article in recent_articles.scalars().all():
        items.append(
            ActivityItem(
                kind="article",
                title=article.title,
                subtitle=(
                    "Статья, статус: "
                    f"{RU_LABELS['article_status'].get(article.status, article.status)}"
                ),
                href=f"/articles/{article.id}",
                happened_at=article.updated_at,
                entity_id=article.id,
            )
        )

    competitor_posts = await db.execute(
        select(CompetitorPublication, Competitor.name)
        .join(Competitor, Competitor.id == CompetitorPublication.competitor_id)
        .where(Competitor.project_id == project_id, Competitor.deleted_at.is_(None))
        .order_by(nulls_last(CompetitorPublication.published_at.desc()))
        .limit(3)
    )
    for publication, competitor_name in competitor_posts.all():
        items.append(
            ActivityItem(
                kind="competitor_publication",
                title=publication.title,
                subtitle=f"Новая публикация конкурента: {competitor_name}",
                href=f"/competitors/{publication.competitor_id}",
                happened_at=publication.published_at or publication.created_at,
                entity_id=publication.id,
            )
        )

    failures = await db.execute(
        select(PublicationLog)
        .where(
            PublicationLog.project_id == project_id,
            PublicationLog.result == PublicationResult.ERROR,
        )
        .order_by(PublicationLog.created_at.desc())
        .limit(3)
    )
    for log in failures.scalars().all():
        items.append(
            ActivityItem(
                kind="publication_error",
                title="Ошибка публикации",
                subtitle=log.error_message or "Публикация не выполнена",
                href="/calendar",
                level="error",
                happened_at=log.finished_at or log.created_at,
                entity_id=log.article_id,
            )
        )

    upcoming = await db.execute(
        select(ScheduledPublication, Article.title)
        .join(Article, Article.id == ScheduledPublication.article_id)
        .where(
            ScheduledPublication.project_id == project_id,
            ScheduledPublication.status.in_([ScheduleStatus.PLANNED, ScheduleStatus.READY]),
        )
        .order_by(ScheduledPublication.scheduled_at)
        .limit(3)
    )
    for schedule, title in upcoming.all():
        items.append(
            ActivityItem(
                kind="scheduled",
                title=title,
                subtitle=f"Запланировано, часовой пояс: {schedule.timezone}",
                href="/calendar",
                level="info",
                happened_at=schedule.scheduled_at,
                entity_id=schedule.id,
            )
        )

    oldest = datetime.min.replace(tzinfo=UTC)
    items.sort(key=lambda item: item.happened_at or oldest, reverse=True)
    return items[:10]
