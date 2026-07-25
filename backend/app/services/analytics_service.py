"""Аналитика проекта.

Все показатели строятся по срезам статистики, которые пользователь ввёл вручную
или импортировал из CSV. Автоматических источников у сервиса нет: получать
статистику Дзена без официального доступа он не пытается. Если данных нет,
показатель возвращается пустым, а не нулевым.
"""

from __future__ import annotations

import csv
import io
import uuid
from collections import Counter, defaultdict
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, ValidationAppError
from app.models.analytics import AnalyticsSnapshot
from app.models.article import Article
from app.models.competitor import Competitor, CompetitorPublication
from app.models.enums import ArticleStatus, DataSource
from app.schemas.analytics import (
    ComparisonResponse,
    CompetitorComparison,
    CsvImportSummary,
    HourStat,
    ManualStatInput,
    MetricValue,
    OverviewResponse,
    TimeseriesPoint,
    TimeseriesResponse,
    TopArticle,
    TopResponse,
    TopTitleWord,
    TopTopic,
    WeekdayStat,
)
from app.services import text_analysis

WEEKDAY_LABELS = [
    "Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье",
]

NO_DATA_NOTE = (
    "Автоматических источников статистики нет. Введите данные вручную "
    "или импортируйте CSV из личного кабинета Дзена."
)

CSV_ALIASES: dict[str, tuple[str, ...]] = {
    "captured_for": ("date", "дата", "день", "captured_for"),
    "views": ("views", "просмотры", "показы"),
    "reads": ("reads", "дочитывания", "прочтения"),
    "subscribers": ("subscribers", "подписчики", "подписки"),
    "reactions": ("reactions", "реакции", "лайки"),
    "comments_count": ("comments", "комментарии", "comments_count"),
    "title": ("title", "заголовок", "статья", "название"),
}

DATE_FORMATS = ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y")


def _change(current: float | None, previous: float | None) -> float | None:
    if current is None or previous is None or previous == 0:
        return None
    return round((current - previous) / previous * 100, 1)


def _metric(value: float | int | None, previous: float | int | None = None) -> MetricValue:
    if value is None:
        return MetricValue(value=None, available=False, note="Данные недоступны")
    return MetricValue(value=value, change_percent=_change(value, previous), available=True)


async def _snapshots(
    db: AsyncSession, project_id: uuid.UUID, start: date, end: date
) -> list[AnalyticsSnapshot]:
    result = await db.execute(
        select(AnalyticsSnapshot).where(
            AnalyticsSnapshot.project_id == project_id,
            AnalyticsSnapshot.captured_for >= start,
            AnalyticsSnapshot.captured_for <= end,
        )
    )
    return list(result.scalars().all())


async def _published_articles(
    db: AsyncSession, project_id: uuid.UUID, start: date, end: date
) -> list[Article]:
    start_dt = datetime.combine(start, datetime.min.time()).replace(tzinfo=UTC)
    end_dt = datetime.combine(end, datetime.max.time()).replace(tzinfo=UTC)

    result = await db.execute(
        select(Article).where(
            Article.project_id == project_id,
            Article.deleted_at.is_(None),
            Article.status == ArticleStatus.PUBLISHED,
            Article.published_at.is_not(None),
            Article.published_at >= start_dt,
            Article.published_at <= end_dt,
        )
    )
    return list(result.scalars().all())


def resolve_period(
    period: str, custom_start: date | None, custom_end: date | None
) -> tuple[date, date]:
    today = date.today()
    if period == "custom":
        if not custom_start or not custom_end:
            raise ValidationAppError("Для произвольного периода укажите обе даты.")
        if custom_start > custom_end:
            raise ValidationAppError("Начальная дата не может быть позже конечной.")
        return custom_start, custom_end

    days = {"7d": 7, "30d": 30, "90d": 90}.get(period, 30)
    return today - timedelta(days=days - 1), today


async def build_overview(
    db: AsyncSession, project_id: uuid.UUID, start: date, end: date
) -> OverviewResponse:
    span = (end - start).days + 1
    previous_start = start - timedelta(days=span)
    previous_end = start - timedelta(days=1)

    current = await _snapshots(db, project_id, start, end)
    previous = await _snapshots(db, project_id, previous_start, previous_end)

    def total_views(items: list[AnalyticsSnapshot]) -> int | None:
        values = [item.views for item in items if item.views is not None]
        return sum(values) if values else None

    def latest_subscribers(items: list[AnalyticsSnapshot]) -> int | None:
        with_value = [item for item in items if item.subscribers is not None]
        if not with_value:
            return None
        return max(with_value, key=lambda item: item.captured_for).subscribers

    def engagement(items: list[AnalyticsSnapshot]) -> float | None:
        pairs = [
            ((item.reactions or 0) + (item.comments_count or 0)) / item.views * 100
            for item in items
            if item.views
        ]
        return round(sum(pairs) / len(pairs), 2) if pairs else None

    articles_now = await _published_articles(db, project_id, start, end)
    articles_before = await _published_articles(db, project_id, previous_start, previous_end)

    views_now = total_views(current)
    views_before = total_views(previous)

    per_article_now = (
        round(views_now / len(articles_now)) if views_now and articles_now else None
    )
    per_article_before = (
        round(views_before / len(articles_before)) if views_before and articles_before else None
    )

    frequency = round(len(articles_now) / max(1, span / 7), 1) if articles_now else None

    return OverviewResponse(
        period_start=start,
        period_end=end,
        published_articles=_metric(len(articles_now), len(articles_before)),
        total_views=_metric(views_now, views_before),
        avg_views=_metric(per_article_now, per_article_before),
        subscribers=_metric(latest_subscribers(current), latest_subscribers(previous)),
        avg_engagement=_metric(engagement(current), engagement(previous)),
        publish_frequency=_metric(frequency),
        data_source_note=(
            f"Показатели построены по {len(current)} срезам статистики."
            if current
            else NO_DATA_NOTE
        ),
    )


async def build_timeseries(
    db: AsyncSession, project_id: uuid.UUID, start: date, end: date
) -> TimeseriesResponse:
    snapshots = await _snapshots(db, project_id, start, end)
    articles = await _published_articles(db, project_id, start, end)

    views_by_day: dict[date, int] = defaultdict(int)
    subscribers_by_day: dict[date, int] = {}
    has_views = False

    for item in snapshots:
        if item.views is not None:
            views_by_day[item.captured_for] += item.views
            has_views = True
        if item.subscribers is not None:
            subscribers_by_day[item.captured_for] = item.subscribers

    published_by_day: Counter[date] = Counter(
        item.published_at.date() for item in articles if item.published_at
    )

    points: list[TimeseriesPoint] = []
    cursor = start
    while cursor <= end:
        points.append(
            TimeseriesPoint(
                day=cursor,
                views=views_by_day.get(cursor) if has_views else None,
                subscribers=subscribers_by_day.get(cursor),
                published=published_by_day.get(cursor, 0),
            )
        )
        cursor += timedelta(days=1)

    return TimeseriesResponse(
        points=points,
        has_data=has_views or bool(subscribers_by_day),
        note=(
            "Динамика построена по введённым данным."
            if has_views or subscribers_by_day
            else NO_DATA_NOTE
        ),
    )


async def _article_views(
    db: AsyncSession, project_id: uuid.UUID, start: date, end: date
) -> dict[uuid.UUID, int]:
    """Максимальные просмотры по каждой статье за период."""
    result = await db.execute(
        select(AnalyticsSnapshot.article_id, func.max(AnalyticsSnapshot.views))
        .where(
            AnalyticsSnapshot.project_id == project_id,
            AnalyticsSnapshot.article_id.is_not(None),
            AnalyticsSnapshot.views.is_not(None),
            AnalyticsSnapshot.captured_for >= start,
            AnalyticsSnapshot.captured_for <= end,
        )
        .group_by(AnalyticsSnapshot.article_id)
    )
    return {article_id: views for article_id, views in result.all() if article_id}


async def build_weekday_stats(
    db: AsyncSession, project_id: uuid.UUID, start: date, end: date
) -> list[WeekdayStat]:
    articles = await _published_articles(db, project_id, start, end)
    views = await _article_views(db, project_id, start, end)

    grouped: dict[int, list[Article]] = defaultdict(list)
    for article in articles:
        if article.published_at:
            grouped[article.published_at.weekday()].append(article)

    stats: list[WeekdayStat] = []
    for weekday in range(7):
        items = grouped.get(weekday, [])
        values = [views[item.id] for item in items if item.id in views]
        stats.append(
            WeekdayStat(
                weekday=weekday,
                label=WEEKDAY_LABELS[weekday],
                published=len(items),
                avg_views=round(sum(values) / len(values)) if values else None,
            )
        )
    return stats


async def build_hour_stats(
    db: AsyncSession, project_id: uuid.UUID, start: date, end: date
) -> list[HourStat]:
    articles = await _published_articles(db, project_id, start, end)
    views = await _article_views(db, project_id, start, end)

    grouped: dict[int, list[Article]] = defaultdict(list)
    for article in articles:
        if article.published_at:
            grouped[article.published_at.hour].append(article)

    stats: list[HourStat] = []
    for hour in range(24):
        items = grouped.get(hour, [])
        values = [views[item.id] for item in items if item.id in views]
        stats.append(
            HourStat(
                hour=hour,
                label=f"{hour:02d}:00",
                published=len(items),
                avg_views=round(sum(values) / len(values)) if values else None,
            )
        )
    return stats


async def build_top(
    db: AsyncSession, project_id: uuid.UUID, start: date, end: date
) -> TopResponse:
    articles = await _published_articles(db, project_id, start, end)
    views = await _article_views(db, project_id, start, end)

    ranked = sorted(articles, key=lambda item: views.get(item.id, -1), reverse=True)

    top_articles = [
        TopArticle(
            article_id=item.id,
            title=item.title,
            views=views.get(item.id),
            published_at=item.published_at.date() if item.published_at else None,
            reading_time_min=item.reading_time_min,
        )
        for item in ranked[:10]
    ]

    # Лучшие темы: группировка по теме статьи
    topics: dict[str, list[int]] = defaultdict(list)
    topic_counts: Counter[str] = Counter()
    for item in articles:
        key = item.audience or item.goal or "Без темы"
        topic_counts[key] += 1
        if item.id in views:
            topics[key].append(views[item.id])

    top_topics = [
        TopTopic(
            title=name,
            articles=count,
            avg_views=(
                round(sum(topics[name]) / len(topics[name])) if topics.get(name) else None
            ),
        )
        for name, count in topic_counts.most_common(10)
    ]

    # Лучшие слова в заголовках опубликованных статей
    word_views: dict[str, list[int]] = defaultdict(list)
    for entry in text_analysis.popular_title_words([item.title for item in articles], limit=15):
        word = str(entry["word"])
        for item in articles:
            if word in item.title.lower() and item.id in views:
                word_views[word].append(views[item.id])

    title_words = [
        TopTitleWord(
            word=str(entry["word"]),
            count=int(entry["count"]),
            avg_views=(
                round(sum(word_views[str(entry["word"])]) / len(word_views[str(entry["word"])]))
                if word_views.get(str(entry["word"]))
                else None
            ),
        )
        for entry in text_analysis.popular_title_words(
            [item.title for item in articles], limit=15
        )
    ]

    return TopResponse(
        articles=top_articles,
        topics=top_topics,
        title_words=title_words,
        note=(
            "Лучшие материалы определены по введённым просмотрам."
            if views
            else "Просмотры не введены, поэтому порядок условный. " + NO_DATA_NOTE
        ),
    )


async def build_comparison(
    db: AsyncSession, project_id: uuid.UUID, start: date, end: date
) -> ComparisonResponse:
    """Сравнение вашего канала с конкурентами по среднему числу просмотров."""
    articles = await _published_articles(db, project_id, start, end)
    views = await _article_views(db, project_id, start, end)
    own_values = [views[item.id] for item in articles if item.id in views]

    rows = [
        CompetitorComparison(
            name="Ваш канал",
            avg_views=round(sum(own_values) / len(own_values)) if own_values else None,
            publications=len(articles),
            is_you=True,
        )
    ]

    start_dt = datetime.combine(start, datetime.min.time()).replace(tzinfo=UTC)
    end_dt = datetime.combine(end, datetime.max.time()).replace(tzinfo=UTC)

    result = await db.execute(
        select(Competitor).where(
            Competitor.project_id == project_id, Competitor.deleted_at.is_(None)
        )
    )
    for competitor in result.scalars().all():
        publications = await db.execute(
            select(CompetitorPublication).where(
                CompetitorPublication.competitor_id == competitor.id,
                CompetitorPublication.published_at >= start_dt,
                CompetitorPublication.published_at <= end_dt,
            )
        )
        items = list(publications.scalars().all())
        competitor_views = [item.views for item in items if item.views is not None]
        rows.append(
            CompetitorComparison(
                name=competitor.name,
                avg_views=(
                    round(sum(competitor_views) / len(competitor_views))
                    if competitor_views
                    else None
                ),
                publications=len(items),
            )
        )

    return ComparisonResponse(
        rows=rows,
        note=(
            "Сравнение построено по данным, которые есть в проекте. "
            "Пустые значения означают, что просмотры не введены."
        ),
    )


# --------------------------------------------------------------------------
# Ручной ввод и импорт
# --------------------------------------------------------------------------

async def save_manual(
    db: AsyncSession, project_id: uuid.UUID, data: ManualStatInput
) -> AnalyticsSnapshot:
    if data.article_id is not None:
        article = await db.get(Article, data.article_id)
        if article is None or article.project_id != project_id:
            raise NotFoundError("Статья не найдена")

    result = await db.execute(
        select(AnalyticsSnapshot).where(
            AnalyticsSnapshot.project_id == project_id,
            AnalyticsSnapshot.article_id == data.article_id,
            AnalyticsSnapshot.captured_for == data.captured_for,
            AnalyticsSnapshot.source == DataSource.MANUAL,
        )
    )
    snapshot = result.scalars().first()

    if snapshot is None:
        snapshot = AnalyticsSnapshot(
            project_id=project_id,
            article_id=data.article_id,
            captured_for=data.captured_for,
            source=DataSource.MANUAL,
        )
        db.add(snapshot)

    snapshot.views = data.views
    snapshot.reads = data.reads
    snapshot.subscribers = data.subscribers
    snapshot.reactions = data.reactions
    snapshot.comments_count = data.comments_count

    await db.flush()
    return snapshot


def _match_column(header: str) -> str | None:
    normalized = header.strip().lower()
    for field_name, aliases in CSV_ALIASES.items():
        if normalized in aliases:
            return field_name
    return None


def _parse_int(value: str | None) -> int | None:
    if not value:
        return None
    digits = "".join(char for char in value if char.isdigit())
    return int(digits) if digits else None


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    raw = value.strip()
    for pattern in DATE_FORMATS:
        try:
            return datetime.strptime(raw, pattern).date()
        except ValueError:
            continue
    return None


async def import_csv(
    db: AsyncSession, project_id: uuid.UUID, content: bytes
) -> CsvImportSummary:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            text = content.decode("cp1251")
        except UnicodeDecodeError as exc:
            raise ValidationAppError(
                "Не удалось прочитать файл. Сохраните CSV в кодировке UTF-8."
            ) from exc

    sample = text[:4096]
    delimiter = ";" if sample.count(";") > sample.count(",") else ","

    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    try:
        headers = next(reader)
    except StopIteration as exc:
        raise ValidationAppError("Файл пустой") from exc

    mapping = {index: _match_column(header) for index, header in enumerate(headers)}
    if "captured_for" not in mapping.values():
        raise ValidationAppError(
            "В файле нет колонки с датой. Добавьте колонку «Дата» или «date»."
        )

    # Сопоставление по заголовку статьи, если он указан в файле
    articles = await db.execute(
        select(Article).where(Article.project_id == project_id, Article.deleted_at.is_(None))
    )
    by_title = {item.title.strip().lower(): item.id for item in articles.scalars().all()}

    created = 0
    updated = 0
    skipped = 0
    errors: list[str] = []

    for line_number, row in enumerate(reader, start=2):
        if not any(cell.strip() for cell in row):
            continue

        values: dict[str, str] = {}
        for index, cell in enumerate(row):
            field_name = mapping.get(index)
            if field_name:
                values[field_name] = cell.strip()

        captured = _parse_date(values.get("captured_for"))
        if captured is None:
            skipped += 1
            if len(errors) < 20:
                errors.append(f"Строка {line_number}: не удалось разобрать дату")
            continue

        article_id = by_title.get((values.get("title") or "").strip().lower())

        existing = await db.execute(
            select(AnalyticsSnapshot).where(
                AnalyticsSnapshot.project_id == project_id,
                AnalyticsSnapshot.article_id == article_id,
                AnalyticsSnapshot.captured_for == captured,
                AnalyticsSnapshot.source == DataSource.CSV_IMPORT,
            )
        )
        snapshot = existing.scalars().first()
        is_new = snapshot is None

        if snapshot is None:
            snapshot = AnalyticsSnapshot(
                project_id=project_id,
                article_id=article_id,
                captured_for=captured,
                source=DataSource.CSV_IMPORT,
            )
            db.add(snapshot)

        snapshot.views = _parse_int(values.get("views"))
        snapshot.reads = _parse_int(values.get("reads"))
        snapshot.subscribers = _parse_int(values.get("subscribers"))
        snapshot.reactions = _parse_int(values.get("reactions"))
        snapshot.comments_count = _parse_int(values.get("comments_count"))

        if is_new:
            created += 1
        else:
            updated += 1

    await db.flush()

    return CsvImportSummary(
        created=created,
        updated=updated,
        skipped=skipped,
        errors=errors,
        message=(
            f"Добавлено записей: {created}, обновлено: {updated}, пропущено: {skipped}."
            if created or updated
            else "Новых данных не найдено. Проверьте формат файла."
        ),
    )


async def export_csv(db: AsyncSession, project_id: uuid.UUID, start: date, end: date) -> str:
    snapshots = await _snapshots(db, project_id, start, end)

    articles = await db.execute(
        select(Article).where(Article.project_id == project_id)
    )
    titles = {item.id: item.title for item in articles.scalars().all()}

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(
        ["Дата", "Статья", "Просмотры", "Дочитывания", "Подписчики", "Реакции", "Комментарии", "Источник"]
    )

    for item in sorted(snapshots, key=lambda snapshot: snapshot.captured_for):
        writer.writerow(
            [
                item.captured_for.strftime("%d.%m.%Y"),
                titles.get(item.article_id, "Сводка по проекту") if item.article_id else "Сводка по проекту",
                item.views if item.views is not None else "",
                item.reads if item.reads is not None else "",
                item.subscribers if item.subscribers is not None else "",
                item.reactions if item.reactions is not None else "",
                item.comments_count if item.comments_count is not None else "",
                item.source,
            ]
        )

    return output.getvalue()
