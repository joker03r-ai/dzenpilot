"""Статьи: хранение, версии, автосохранение, чек-лист."""

from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models.article import Article, ArticleVersion
from app.models.enums import RU_LABELS, ArticleStatus
from app.models.topic import Topic
from app.schemas.article import (
    ArticleCreate,
    ArticleListItem,
    ArticleResponse,
    ArticleUpdate,
    ChecklistItem,
    ChecklistResponse,
)
from app.schemas.common import PaginationParams
from app.services import text_analysis

# Сколько версий храним на статью, чтобы база не росла бесконечно
MAX_VERSIONS = 30


def _status_label(status: ArticleStatus) -> str:
    return RU_LABELS["article_status"].get(status, status)


async def to_response(db: AsyncSession, article: Article) -> ArticleResponse:
    payload = ArticleResponse.model_validate(article)
    payload.status_label = _status_label(article.status)
    payload.versions_count = int(
        await db.scalar(
            select(func.count())
            .select_from(ArticleVersion)
            .where(ArticleVersion.article_id == article.id)
        )
        or 0
    )
    return payload


def to_list_item(article: Article) -> ArticleListItem:
    payload = ArticleListItem.model_validate(article)
    payload.status_label = _status_label(article.status)
    return payload


async def list_articles(
    db: AsyncSession,
    project_id: uuid.UUID,
    params: PaginationParams,
    status: ArticleStatus | None = None,
) -> tuple[list[Article], int]:
    base = select(Article).where(
        Article.project_id == project_id, Article.deleted_at.is_(None)
    )
    if status:
        base = base.where(Article.status == status)
    if params.search:
        base = base.where(Article.title.ilike(f"%{params.search}%"))

    total = await db.scalar(select(func.count()).select_from(base.subquery())) or 0
    result = await db.execute(
        base.order_by(Article.updated_at.desc()).offset(params.offset).limit(params.size)
    )
    return list(result.scalars().all()), int(total)


async def get_article(
    db: AsyncSession, project_id: uuid.UUID, article_id: uuid.UUID
) -> Article:
    article = await db.get(Article, article_id)
    if article is None or article.project_id != project_id or article.deleted_at:
        raise NotFoundError("Статья не найдена")
    return article


def _slugify(title: str) -> str:
    translit = {
        "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
        "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
        "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
        "ф": "f", "х": "h", "ц": "c", "ч": "ch", "ш": "sh", "щ": "sch",
        "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    }
    lowered = title.lower()
    converted = "".join(translit.get(char, char) for char in lowered)
    slug = re.sub(r"[^a-z0-9]+", "-", converted).strip("-")
    return slug[:200] or "article"


async def create_article(
    db: AsyncSession, project_id: uuid.UUID, data: ArticleCreate, user_id: uuid.UUID
) -> Article:
    """Шаг 1 мастера. Всё, что ввёл пользователь, сохраняется в generation_input."""
    topic: Topic | None = None
    if data.topic_id:
        topic = await db.get(Topic, data.topic_id)
        if topic is not None and topic.project_id != project_id:
            topic = None

    article = Article(
        project_id=project_id,
        topic_id=topic.id if topic else None,
        title=data.title.strip(),
        slug=_slugify(data.title),
        goal=data.goal,
        audience=data.audience or (topic.audience if topic else None),
        tone=data.tone,
        target_length=data.target_length,
        keywords=data.keywords,
        cta=data.cta,
        status=ArticleStatus.DRAFT,
        outline=[],
        checklist={},
        generation_input={
            "region": data.region,
            "required_facts": data.required_facts,
            "source_links": data.source_links,
            "products": data.products,
            "forbidden_words": data.forbidden_words,
        },
        author_id=user_id,
    )
    db.add(article)
    await db.flush()
    return article


async def next_version_number(db: AsyncSession, article_id: uuid.UUID) -> int:
    current = await db.scalar(
        select(func.max(ArticleVersion.version_number)).where(
            ArticleVersion.article_id == article_id
        )
    )
    return int(current or 0) + 1


async def save_version(
    db: AsyncSession,
    article: Article,
    change_note: str,
    user_id: uuid.UUID | None = None,
) -> ArticleVersion:
    """Снимок статьи для истории изменений."""
    version = ArticleVersion(
        article_id=article.id,
        version_number=await next_version_number(db, article.id),
        title=article.title,
        lead=article.lead,
        body_markdown=article.body_markdown,
        outline=article.outline,
        change_note=change_note[:500],
        created_by=user_id,
    )
    db.add(version)
    await db.flush()

    # Оставляем только последние MAX_VERSIONS снимков
    old = await db.execute(
        select(ArticleVersion)
        .where(ArticleVersion.article_id == article.id)
        .order_by(ArticleVersion.version_number.desc())
        .offset(MAX_VERSIONS)
    )
    for item in old.scalars().all():
        await db.delete(item)

    await db.flush()
    return version


def refresh_counters(article: Article) -> None:
    article.word_count = text_analysis.word_count(article.body_markdown)
    article.reading_time_min = text_analysis.reading_time_minutes(article.body_markdown)


async def update_article(
    db: AsyncSession, article: Article, data: ArticleUpdate, user_id: uuid.UUID
) -> Article:
    payload = data.model_dump(exclude_unset=True)
    save_snapshot = payload.pop("save_version", False)
    change_note = payload.pop("change_note", None)

    if save_snapshot and article.body_markdown:
        await save_version(db, article, change_note or "Ручное сохранение", user_id)

    for field_name, value in payload.items():
        setattr(article, field_name, value)

    if "title" in payload:
        article.slug = _slugify(article.title)
    if "body_markdown" in payload:
        refresh_counters(article)

    await db.flush()
    return article


async def list_versions(db: AsyncSession, article_id: uuid.UUID) -> list[ArticleVersion]:
    result = await db.execute(
        select(ArticleVersion)
        .where(ArticleVersion.article_id == article_id)
        .order_by(ArticleVersion.version_number.desc())
    )
    return list(result.scalars().all())


async def restore_version(
    db: AsyncSession, article: Article, version_id: uuid.UUID, user_id: uuid.UUID
) -> Article:
    version = await db.get(ArticleVersion, version_id)
    if version is None or version.article_id != article.id:
        raise NotFoundError("Версия не найдена")

    # Текущее состояние тоже сохраняем, чтобы восстановление можно было отменить
    if article.body_markdown:
        await save_version(
            db, article, f"Перед возвратом к версии {version.version_number}", user_id
        )

    article.title = version.title or article.title
    article.lead = version.lead
    article.body_markdown = version.body_markdown
    article.outline = version.outline
    refresh_counters(article)
    await db.flush()
    return article


async def delete_article(db: AsyncSession, article: Article) -> None:
    article.status = ArticleStatus.ARCHIVED
    article.deleted_at = datetime.now(UTC)
    await db.flush()


# --------------------------------------------------------------------------
# Чек-лист перед публикацией
# --------------------------------------------------------------------------

URL_PATTERN = re.compile(r"https?://[^\s)\"']+")


def build_checklist(article: Article, has_cover: bool) -> ChecklistResponse:
    """Проверка готовности статьи. Ничего не публикует — только показывает состояние."""
    body = article.body_markdown or ""
    forbidden = [
        word
        for word in article.generation_input.get("forbidden_words", [])
        if isinstance(word, str) and word.strip() and word.lower() in body.lower()
    ]
    empty_sections = re.findall(r"#{2,3}\s*\n\s*(?=#{2,3}|\Z)", body)
    unverified = body.count("Требуется проверка факта")
    links = URL_PATTERN.findall(body)

    items = [
        ChecklistItem(
            code="title",
            label="Заголовок заполнен",
            done=bool(article.title and len(article.title.strip()) >= 10),
            hint="Хороший заголовок — от 30 до 90 знаков.",
        ),
        ChecklistItem(
            code="cover",
            label="Обложка добавлена",
            done=has_cover,
            hint="Обложка сильно влияет на переходы из ленты Дзена.",
        ),
        ChecklistItem(
            code="structure",
            label="Структура понятна",
            done=body.count("##") >= 2,
            hint="Нужно минимум два подзаголовка, чтобы текст читался с телефона.",
        ),
        ChecklistItem(
            code="no_empty_blocks",
            label="Нет пустых блоков",
            done=len(empty_sections) == 0,
            hint="Под каждым подзаголовком должен быть текст.",
        ),
        ChecklistItem(
            code="links",
            label="Ссылки проверены",
            done=len(links) == 0 or bool(article.checklist.get("links_checked")),
            hint=(
                f"В тексте {len(links)} ссылок. Откройте каждую и отметьте проверку вручную."
                if links
                else "Ссылок в тексте нет."
            ),
        ),
        ChecklistItem(
            code="facts",
            label="Факты проверены",
            done=unverified == 0 and bool(body),
            hint=(
                f"Осталось пометок «Требуется проверка факта»: {unverified}. "
                "Проверьте их и уберите пометку."
                if unverified
                else "Непроверенных пометок нет."
            ),
        ),
        ChecklistItem(
            code="forbidden",
            label="Нет нежелательных слов",
            done=len(forbidden) == 0,
            hint=(
                "Найдены запрещённые слова: " + ", ".join(forbidden)
                if forbidden
                else "Запрещённых слов не найдено."
            ),
        ),
        ChecklistItem(
            code="cta",
            label="Добавлен призыв к действию",
            done=bool(article.cta and article.cta.strip()),
            hint="Например: «Подпишитесь, если хотите продолжение серии».",
        ),
        ChecklistItem(
            code="schedule",
            label="Выбраны дата и время публикации",
            done=article.planned_publish_at is not None,
            hint="Дата назначается в контент-календаре.",
        ),
    ]

    ready = all(item.done for item in items)
    remaining = sum(1 for item in items if not item.done)

    return ChecklistResponse(
        items=items,
        ready=ready,
        message=(
            "Статья готова к публикации. Опубликовать её можно только вручную — "
            "сервис ничего не отправляет сам."
            if ready
            else f"Осталось выполнить пунктов: {remaining}."
        ),
    )
