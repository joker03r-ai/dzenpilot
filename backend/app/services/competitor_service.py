"""Конкуренты: добавление, публикации, пересчёт показателей, сравнение.

Показатели считаются только по тем публикациям, которые действительно есть
в базе. Если данных нет, поле остаётся пустым, и интерфейс показывает
«Данные недоступны» — сервис не подставляет выдуманные цифры.
"""

from __future__ import annotations

import csv
import io
import uuid
from collections import Counter
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError, ValidationAppError
from app.models.competitor import Competitor, CompetitorAnalysis, CompetitorPublication
from app.models.enums import CompetitorStatus, DataSource
from app.schemas.common import PaginationParams
from app.schemas.competitor import (
    CompareRequest,
    CompareResponse,
    ComparePoint,
    CompareRow,
    CompetitorCreate,
    CompetitorUpdate,
    CsvImportResult,
    PublicationCreate,
    PublicationUpdate,
)
from app.services import text_analysis

# Названия колонок CSV, которые принимает импорт. Регистр не важен.
CSV_ALIASES: dict[str, tuple[str, ...]] = {
    "title": ("title", "заголовок", "название", "статья"),
    "url": ("url", "ссылка", "адрес"),
    "published_at": ("published_at", "дата", "дата публикации", "date"),
    "views": ("views", "просмотры", "показы"),
    "reactions": ("reactions", "реакции", "лайки", "нравится"),
    "comments_count": ("comments", "comments_count", "комментарии"),
    "topic_guess": ("topic", "тема", "тематика"),
    "format": ("format", "формат", "тип"),
}

DATE_FORMATS = ("%Y-%m-%d", "%d.%m.%Y", "%d.%m.%Y %H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S")


# --------------------------------------------------------------------------
# Конкуренты
# --------------------------------------------------------------------------

async def list_competitors(
    db: AsyncSession,
    project_id: uuid.UUID,
    params: PaginationParams,
    group: str | None = None,
    status: CompetitorStatus | None = None,
) -> tuple[list[Competitor], int]:
    base = select(Competitor).where(
        Competitor.project_id == project_id, Competitor.deleted_at.is_(None)
    )
    if params.search:
        base = base.where(Competitor.name.ilike(f"%{params.search}%"))
    if group:
        base = base.where(Competitor.group_name == group)
    if status:
        base = base.where(Competitor.status == status)

    total = await db.scalar(select(func.count()).select_from(base.subquery())) or 0

    order = Competitor.created_at.desc()
    if params.sort:
        column = getattr(Competitor, params.sort.lstrip("-"), None)
        if column is not None:
            order = column.desc() if params.sort.startswith("-") else column.asc()

    result = await db.execute(base.order_by(order).offset(params.offset).limit(params.size))
    return list(result.scalars().all()), int(total)


async def get_competitor(
    db: AsyncSession, project_id: uuid.UUID, competitor_id: uuid.UUID
) -> Competitor:
    competitor = await db.get(Competitor, competitor_id)
    if competitor is None or competitor.project_id != project_id or competitor.deleted_at:
        raise NotFoundError("Конкурент не найден")
    return competitor


async def create_competitor(
    db: AsyncSession, project_id: uuid.UUID, data: CompetitorCreate, user_id: uuid.UUID
) -> Competitor:
    if data.url:
        exists = await db.execute(
            select(Competitor).where(
                Competitor.project_id == project_id,
                Competitor.url == data.url,
                Competitor.deleted_at.is_(None),
            )
        )
        if exists.scalars().first() is not None:
            raise ConflictError("Конкурент с такой ссылкой уже добавлен")

    competitor = Competitor(
        project_id=project_id,
        name=data.name.strip(),
        url=data.url,
        description=data.description,
        niche=data.niche,
        group_name=data.group_name,
        notes=data.notes,
        data_source=DataSource.MANUAL,
        status=CompetitorStatus.NEW,
        created_by=user_id,
    )
    db.add(competitor)
    await db.flush()
    return competitor


async def update_competitor(
    db: AsyncSession, competitor: Competitor, data: CompetitorUpdate
) -> Competitor:
    for field_name, value in data.model_dump(exclude_unset=True).items():
        setattr(competitor, field_name, value)
    await db.flush()
    return competitor


async def delete_competitor(db: AsyncSession, competitor: Competitor) -> None:
    competitor.deleted_at = datetime.now(UTC)
    await db.flush()


async def count_publications(db: AsyncSession, competitor_id: uuid.UUID) -> int:
    return int(
        await db.scalar(
            select(func.count())
            .select_from(CompetitorPublication)
            .where(CompetitorPublication.competitor_id == competitor_id)
        )
        or 0
    )


async def has_analysis(db: AsyncSession, competitor_id: uuid.UUID) -> bool:
    return bool(
        await db.scalar(
            select(func.count())
            .select_from(CompetitorAnalysis)
            .where(CompetitorAnalysis.competitor_id == competitor_id)
        )
    )


# --------------------------------------------------------------------------
# Публикации
# --------------------------------------------------------------------------

async def list_publications(
    db: AsyncSession, competitor_id: uuid.UUID, params: PaginationParams
) -> tuple[list[CompetitorPublication], int]:
    base = select(CompetitorPublication).where(
        CompetitorPublication.competitor_id == competitor_id
    )
    if params.search:
        base = base.where(CompetitorPublication.title.ilike(f"%{params.search}%"))

    total = await db.scalar(select(func.count()).select_from(base.subquery())) or 0

    order = CompetitorPublication.published_at.desc()
    if params.sort:
        column = getattr(CompetitorPublication, params.sort.lstrip("-"), None)
        if column is not None:
            order = column.desc() if params.sort.startswith("-") else column.asc()

    result = await db.execute(base.order_by(order).offset(params.offset).limit(params.size))
    return list(result.scalars().all()), int(total)


async def add_publication(
    db: AsyncSession,
    competitor: Competitor,
    data: PublicationCreate,
    source: DataSource = DataSource.MANUAL,
) -> CompetitorPublication:
    if data.url:
        exists = await db.execute(
            select(CompetitorPublication).where(
                CompetitorPublication.competitor_id == competitor.id,
                CompetitorPublication.url == data.url,
            )
        )
        if exists.scalars().first() is not None:
            raise ConflictError("Такая публикация уже добавлена")

    analysis = text_analysis.analyze_title(data.title, data.raw_excerpt)
    publication = CompetitorPublication(
        competitor_id=competitor.id,
        title=data.title.strip(),
        url=data.url,
        published_at=data.published_at,
        views=data.views,
        reactions=data.reactions,
        comments_count=data.comments_count,
        topic_guess=data.topic_guess,
        format=data.format,
        audience_guess=data.audience_guess,
        raw_excerpt=data.raw_excerpt,
        data_source=source,
        **analysis,
    )
    db.add(publication)
    await db.flush()
    return publication


async def update_publication(
    db: AsyncSession, publication: CompetitorPublication, data: PublicationUpdate
) -> CompetitorPublication:
    payload = data.model_dump(exclude_unset=True)
    for field_name, value in payload.items():
        setattr(publication, field_name, value)

    if "title" in payload:
        for key, value in text_analysis.analyze_title(
            publication.title, publication.raw_excerpt
        ).items():
            setattr(publication, key, value)

    await db.flush()
    return publication


async def delete_publication(db: AsyncSession, publication: CompetitorPublication) -> None:
    await db.delete(publication)
    await db.flush()


# --------------------------------------------------------------------------
# Пересчёт показателей конкурента
# --------------------------------------------------------------------------

async def recalculate_metrics(db: AsyncSession, competitor: Competitor) -> Competitor:
    """Пересчитывает агрегаты по сохранённым публикациям.

    Показатель остаётся пустым, если исходных данных для него нет.
    """
    result = await db.execute(
        select(CompetitorPublication)
        .where(CompetitorPublication.competitor_id == competitor.id)
        .order_by(CompetitorPublication.published_at)
    )
    publications = list(result.scalars().all())

    competitor.publications_count = len(publications) or None
    if not publications:
        competitor.avg_views = None
        competitor.max_views = None
        competitor.min_views = None
        competitor.avg_engagement_rate = None
        competitor.avg_article_length = None
        competitor.avg_publish_interval_days = None
        competitor.popular_title_words = []
        competitor.frequent_topics = []
        competitor.formats_used = []
        await db.flush()
        return competitor

    views = [item.views for item in publications if item.views is not None]
    if views:
        competitor.avg_views = round(sum(views) / len(views))
        competitor.max_views = max(views)
        competitor.min_views = min(views)
    else:
        competitor.avg_views = competitor.max_views = competitor.min_views = None

    # Вовлечённость: доля реакций и комментариев от просмотров
    engagement_values: list[float] = []
    for item in publications:
        if item.views:
            interactions = (item.reactions or 0) + (item.comments_count or 0)
            engagement_values.append(interactions / item.views * 100)
    competitor.avg_engagement_rate = (
        Decimal(str(round(sum(engagement_values) / len(engagement_values), 3)))
        if engagement_values
        else None
    )

    lengths = [item.body_length for item in publications if item.body_length]
    competitor.avg_article_length = round(sum(lengths) / len(lengths)) if lengths else None

    dates = sorted(item.published_at for item in publications if item.published_at)
    if len(dates) >= 2:
        span_days = (dates[-1] - dates[0]).total_seconds() / 86400
        interval = span_days / (len(dates) - 1)
        competitor.avg_publish_interval_days = Decimal(str(round(interval, 2)))
    else:
        competitor.avg_publish_interval_days = None

    competitor.popular_title_words = text_analysis.popular_title_words(
        [item.title for item in publications]
    )

    topics = Counter(item.topic_guess for item in publications if item.topic_guess)
    competitor.frequent_topics = [
        {"topic": topic, "count": count} for topic, count in topics.most_common(10)
    ]

    formats = Counter(item.format for item in publications if item.format)
    competitor.formats_used = [
        {"format": name, "count": count} for name, count in formats.most_common(10)
    ]

    # Использование изображений и видео автоматически получить нельзя
    competitor.media_usage = {
        "images": "Требуется ручной импорт",
        "video": "Требуется ручной импорт",
    }

    await db.flush()
    return competitor


# --------------------------------------------------------------------------
# Импорт CSV
# --------------------------------------------------------------------------

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


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    raw = value.strip()
    for pattern in DATE_FORMATS:
        try:
            return datetime.strptime(raw, pattern).replace(tzinfo=UTC)
        except ValueError:
            continue
    return None


async def import_publications_csv(
    db: AsyncSession, competitor: Competitor, content: bytes
) -> CsvImportResult:
    """Импорт публикаций из CSV.

    Обязательная колонка одна — заголовок. Остальные подхватываются,
    если найдены; неизвестные колонки игнорируются.
    """
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
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ";" if sample.count(";") > sample.count(",") else ","

    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    try:
        headers = next(reader)
    except StopIteration as exc:
        raise ValidationAppError("Файл пустой") from exc

    mapping = {index: _match_column(header) for index, header in enumerate(headers)}
    if "title" not in mapping.values():
        raise ValidationAppError(
            "В файле нет колонки с заголовком. Добавьте колонку «Заголовок» или «title»."
        )

    existing = await db.execute(
        select(CompetitorPublication.url).where(
            CompetitorPublication.competitor_id == competitor.id,
            CompetitorPublication.url.is_not(None),
        )
    )
    known_urls = {url for url in existing.scalars().all() if url}

    created = 0
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

        title = values.get("title", "").strip()
        if not title:
            skipped += 1
            errors.append(f"Строка {line_number}: пустой заголовок")
            continue

        url = values.get("url") or None
        if url and url in known_urls:
            skipped += 1
            continue

        analysis = text_analysis.analyze_title(title)
        db.add(
            CompetitorPublication(
                competitor_id=competitor.id,
                title=title[:500],
                url=url[:700] if url else None,
                published_at=_parse_date(values.get("published_at")),
                views=_parse_int(values.get("views")),
                reactions=_parse_int(values.get("reactions")),
                comments_count=_parse_int(values.get("comments_count")),
                topic_guess=(values.get("topic_guess") or None),
                format=(values.get("format") or None),
                data_source=DataSource.CSV_IMPORT,
                **analysis,
            )
        )
        if url:
            known_urls.add(url)
        created += 1

        if len(errors) > 50:
            errors.append("Показаны первые 50 замечаний")
            break

    await db.flush()
    await recalculate_metrics(db, competitor)

    message = (
        f"Добавлено публикаций: {created}. Пропущено: {skipped}."
        if created
        else "Новых публикаций не найдено — возможно, все они уже добавлены."
    )
    return CsvImportResult(
        created=created, updated=0, skipped=skipped, errors=errors[:50], message=message
    )


# --------------------------------------------------------------------------
# Сравнение конкурентов
# --------------------------------------------------------------------------

async def compare_competitors(
    db: AsyncSession, project_id: uuid.UUID, request: CompareRequest
) -> CompareResponse:
    since = datetime.now(UTC) - timedelta(days=request.period_days)
    half = datetime.now(UTC) - timedelta(days=request.period_days // 2)

    rows: list[CompareRow] = []
    chart: list[ComparePoint] = []
    missing_data = False

    for competitor_id in request.competitor_ids:
        competitor = await get_competitor(db, project_id, competitor_id)

        result = await db.execute(
            select(CompetitorPublication).where(
                CompetitorPublication.competitor_id == competitor.id
            )
        )
        publications = list(result.scalars().all())
        in_period = [
            item for item in publications if item.published_at and item.published_at >= since
        ]

        views = [item.views for item in in_period if item.views is not None]
        avg_views = round(sum(views) / len(views)) if views else None
        if avg_views is None:
            missing_data = True

        # Динамика: вторая половина периода против первой
        first_half = [
            item.views
            for item in in_period
            if item.views is not None and item.published_at and item.published_at < half
        ]
        second_half = [
            item.views
            for item in in_period
            if item.views is not None and item.published_at and item.published_at >= half
        ]
        dynamics: float | None = None
        if first_half and second_half:
            before = sum(first_half) / len(first_half)
            after = sum(second_half) / len(second_half)
            if before > 0:
                dynamics = round((after - before) / before * 100, 1)

        topics = Counter(item.topic_guess for item in in_period if item.topic_guess)
        best_topics = [topic for topic, _ in topics.most_common(3)]

        engagement_values = [
            ((item.reactions or 0) + (item.comments_count or 0)) / item.views * 100
            for item in in_period
            if item.views
        ]
        engagement = (
            round(sum(engagement_values) / len(engagement_values), 2)
            if engagement_values
            else None
        )

        rating, reason = _rating(avg_views, len(in_period), engagement, dynamics)

        rows.append(
            CompareRow(
                competitor_id=competitor.id,
                name=competitor.name,
                publish_interval_days=(
                    float(competitor.avg_publish_interval_days)
                    if competitor.avg_publish_interval_days is not None
                    else None
                ),
                publications_in_period=len(in_period),
                avg_views=avg_views,
                max_views=max(views) if views else None,
                avg_engagement_rate=engagement,
                avg_article_length=competitor.avg_article_length,
                best_topics=best_topics,
                title_style=text_analysis.describe_title_style(
                    [item.title for item in in_period]
                ),
                dynamics_percent=dynamics,
                rating=rating,
                rating_reason=reason,
            )
        )
        chart.append(
            ComparePoint(
                name=competitor.name,
                avg_views=avg_views,
                publications=len(in_period),
                engagement=engagement,
            )
        )

    rows.sort(key=lambda row: row.rating, reverse=True)

    note = (
        "У части конкурентов нет данных о просмотрах — по ним показатели пустые. "
        "Добавьте публикации вручную или импортируйте CSV."
        if missing_data
        else f"Сравнение построено по публикациям за последние {request.period_days} дней."
    )
    return CompareResponse(period_days=request.period_days, rows=rows, chart=chart, note=note)


def _rating(
    avg_views: int | None,
    publications: int,
    engagement: float | None,
    dynamics: float | None,
) -> tuple[int, str]:
    """Оценка конкурента от 0 до 100 с объяснением.

    Считается только по имеющимся данным. Если данных нет, оценка низкая,
    и это прямо сказано в объяснении — а не выдаётся за слабость канала.
    """
    if avg_views is None and publications == 0:
        return 0, "Данных нет. Добавьте публикации конкурента или импортируйте CSV."

    score = 0
    parts: list[str] = []

    if avg_views is not None:
        views_score = min(40, round(avg_views / 1000 * 4))
        score += views_score
        parts.append(f"средние просмотры {avg_views}")
    else:
        parts.append("просмотры недоступны")

    activity_score = min(25, publications * 2)
    score += activity_score
    parts.append(f"публикаций за период: {publications}")

    if engagement is not None:
        engagement_score = min(20, round(engagement * 4))
        score += engagement_score
        parts.append(f"вовлечённость {engagement}%")

    if dynamics is not None:
        if dynamics > 0:
            score += min(15, round(dynamics / 4))
            parts.append(f"рост {dynamics}%")
        else:
            parts.append(f"спад {abs(dynamics)}%")

    score = max(0, min(100, score))
    return score, f"Оценка {score} из 100: " + ", ".join(parts) + "."
