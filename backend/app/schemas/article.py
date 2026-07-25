"""Схемы мастера создания статьи и библиотеки материалов."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.models.enums import ArticleStatus
from app.schemas.common import ORMModel

# Инструменты доработки текста из шага 4
ImproveAction = Literal[
    "shorten",
    "expand",
    "simplify",
    "expertise",
    "change_tone",
    "rewrite_fragment",
    "add_examples",
    "remove_repeats",
    "check_structure",
    "check_title",
    "check_clickability",
    "check_readability",
    "find_unverified",
    "image_description",
    "image_prompts",
]

IMPROVE_LABELS: dict[str, str] = {
    "shorten": "Сократить текст",
    "expand": "Расширить текст",
    "simplify": "Сделать проще",
    "expertise": "Сделать экспертнее",
    "change_tone": "Изменить тон",
    "rewrite_fragment": "Переписать выбранный фрагмент",
    "add_examples": "Добавить примеры",
    "remove_repeats": "Убрать повторы",
    "check_structure": "Проверить структуру",
    "check_title": "Проверить заголовок",
    "check_clickability": "Проверить кликабельность",
    "check_readability": "Проверить читаемость",
    "find_unverified": "Найти неподтверждённые утверждения",
    "image_description": "Подготовить описание для изображения",
    "image_prompts": "Создать промты для генерации изображений",
}

# Инструменты, которые не меняют текст, а выдают заключение
ADVISORY_ACTIONS = {
    "check_structure",
    "check_title",
    "check_clickability",
    "check_readability",
    "find_unverified",
    "image_description",
    "image_prompts",
}


class ArticleCreate(BaseModel):
    """Шаг 1 мастера — основные данные."""

    title: str = Field(min_length=3, max_length=500, description="Тема или рабочий заголовок")
    topic_id: uuid.UUID | None = Field(default=None, description="Тема из раздела «Поиск тем»")
    goal: str | None = Field(default=None, max_length=500, description="Цель статьи")
    audience: str | None = Field(default=None, max_length=500, description="Целевая аудитория")
    tone: str | None = Field(default=None, max_length=120, description="Тон общения")
    target_length: int = Field(default=7000, ge=500, le=50000, description="Примерный объём")
    keywords: list[str] = Field(default_factory=list, max_length=30)
    region: str | None = Field(default=None, max_length=120)
    required_facts: list[str] = Field(
        default_factory=list, max_length=30, description="Факты, которые нужно использовать"
    )
    source_links: list[str] = Field(
        default_factory=list, max_length=30, description="Ссылки на источники"
    )
    products: list[str] = Field(
        default_factory=list, max_length=20, description="Товары или услуги для упоминания"
    )
    forbidden_words: list[str] = Field(default_factory=list, max_length=50)
    cta: str | None = Field(default=None, max_length=500, description="Призыв к действию")


class ArticleUpdate(BaseModel):
    """Правки в редакторе и автосохранение."""

    title: str | None = Field(default=None, min_length=1, max_length=500)
    lead: str | None = Field(default=None, max_length=4000)
    body_markdown: str | None = Field(default=None, max_length=200_000)
    outline: list[Any] | None = None
    keywords: list[str] | None = None
    cta: str | None = Field(default=None, max_length=500)
    status: ArticleStatus | None = None
    tone: str | None = Field(default=None, max_length=120)
    audience: str | None = Field(default=None, max_length=500)
    change_note: str | None = Field(
        default=None, max_length=500, description="Комментарий к версии"
    )
    save_version: bool = Field(default=False, description="Сохранить снимок в историю версий")


class OutlineSection(BaseModel):
    heading: str
    points: list[str] = Field(default_factory=list)


class OutlineResponse(BaseModel):
    """Шаг 2 — структура статьи."""

    title_variants: list[str]
    lead: str
    sections: list[OutlineSection]
    conclusion: str
    cta: str
    message: str


class GenerateRequest(BaseModel):
    """Шаг 3 — генерация полного текста."""

    use_outline: bool = Field(default=True, description="Писать по сохранённому плану")
    extra_instructions: str | None = Field(default=None, max_length=2000)


class ImproveRequest(BaseModel):
    """Шаг 4 — доработка текста."""

    action: ImproveAction
    fragment: str | None = Field(
        default=None, max_length=20000, description="Фрагмент для переписывания"
    )
    instruction: str | None = Field(
        default=None, max_length=1000, description="Уточнение, например новый тон"
    )


class ImproveResponse(BaseModel):
    action: str
    action_label: str
    changes_text: bool
    result: str
    applied: bool
    message: str


class ChecklistItem(BaseModel):
    code: str
    label: str
    done: bool
    hint: str


class ChecklistResponse(BaseModel):
    """Шаг 5 — проверка перед публикацией."""

    items: list[ChecklistItem]
    ready: bool
    message: str


class ArticleVersionResponse(ORMModel):
    id: uuid.UUID
    article_id: uuid.UUID
    version_number: int
    title: str | None
    lead: str | None
    change_note: str | None
    created_at: datetime


class ArticleResponse(ORMModel):
    id: uuid.UUID
    project_id: uuid.UUID
    topic_id: uuid.UUID | None
    title: str
    lead: str | None
    body_markdown: str | None
    outline: list[Any]
    keywords: list[Any]
    cta: str | None
    goal: str | None
    audience: str | None
    tone: str | None
    target_length: int | None
    status: ArticleStatus
    # Русская подпись статуса подставляется сервисом после разбора модели,
    # поэтому у поля есть значение по умолчанию.
    status_label: str = ""
    checklist: dict[str, Any]
    generation_input: dict[str, Any]
    planned_publish_at: datetime | None
    published_at: datetime | None
    published_url: str | None
    ai_provider: str | None
    ai_model: str | None
    tokens_input: int | None
    tokens_output: int | None
    cost_usd: Decimal | None
    word_count: int | None
    reading_time_min: int | None
    created_at: datetime
    updated_at: datetime
    versions_count: int = 0


class ArticleListItem(ORMModel):
    id: uuid.UUID
    title: str
    status: ArticleStatus
    status_label: str = ""
    word_count: int | None
    reading_time_min: int | None
    planned_publish_at: datetime | None
    published_at: datetime | None
    updated_at: datetime
    created_at: datetime
