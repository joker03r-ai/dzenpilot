"""Перечисления, общие для базы данных и API.

У каждого значения есть русская подпись — интерфейс берёт её отсюда,
чтобы названия статусов не расходились между backend и frontend.
"""

from __future__ import annotations

from enum import StrEnum


class UserRole(StrEnum):
    OWNER = "owner"
    EDITOR = "editor"
    AUTHOR = "author"
    VIEWER = "viewer"


class ProjectStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class DataSource(StrEnum):
    MANUAL = "manual"
    CSV_IMPORT = "csv_import"
    PUBLIC_PAGE = "public_page"
    OFFICIAL_API = "official_api"
    AI_ESTIMATE = "ai_estimate"


class CompetitorStatus(StrEnum):
    NEW = "new"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    ERROR = "error"


class CompetitionLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TopicStatus(StrEnum):
    SUGGESTED = "suggested"
    SAVED = "saved"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    USED = "used"
    HIDDEN = "hidden"


class TopicOrigin(StrEnum):
    AI_SEARCH = "ai_search"
    MANUAL = "manual"
    CSV_IMPORT = "csv_import"
    COMPETITOR_GAP = "competitor_gap"


class ArticleStatus(StrEnum):
    DRAFT = "draft"
    REVIEW = "review"
    READY = "ready"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"
    ARCHIVED = "archived"


class ScheduleStatus(StrEnum):
    PLANNED = "planned"
    READY = "ready"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PublicationMethod(StrEnum):
    OFFICIAL_API = "official_api"
    PARTNER_SERVICE = "partner_service"
    MANUAL_EXPORT = "manual_export"
    COPY_FORMATTED = "copy_formatted"
    FILE_EXPORT = "file_export"
    REMINDER = "reminder"


class PublicationResult(StrEnum):
    SUCCESS = "success"
    ERROR = "error"
    SKIPPED = "skipped"


class IntegrationKind(StrEnum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GEMINI = "gemini"
    YANDEX_METRIKA = "yandex_metrika"
    TELEGRAM = "telegram"
    EMAIL = "email"
    WEBHOOK = "webhook"
    STORAGE = "storage"
    DZEN_CHANNEL = "dzen_channel"
    CSV = "csv"


class AIProviderName(StrEnum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GEMINI = "gemini"
    LOCAL = "local"


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    CANCELLED = "cancelled"


class NotificationLevel(StrEnum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


# --- Русские подписи для интерфейса ---

RU_LABELS: dict[str, dict[str, str]] = {
    "user_role": {
        UserRole.OWNER: "Владелец",
        UserRole.EDITOR: "Редактор",
        UserRole.AUTHOR: "Автор",
        UserRole.VIEWER: "Наблюдатель",
    },
    "project_status": {
        ProjectStatus.ACTIVE: "Активен",
        ProjectStatus.PAUSED: "Приостановлен",
        ProjectStatus.ARCHIVED: "В архиве",
    },
    "data_source": {
        DataSource.MANUAL: "Введено вручную",
        DataSource.CSV_IMPORT: "Импорт CSV",
        DataSource.PUBLIC_PAGE: "Публичная страница",
        DataSource.OFFICIAL_API: "Официальное API",
        DataSource.AI_ESTIMATE: "Оценка ИИ",
    },
    "competitor_status": {
        CompetitorStatus.NEW: "Новый",
        CompetitorStatus.ANALYZING: "Анализируется",
        CompetitorStatus.ANALYZED: "Проанализирован",
        CompetitorStatus.ERROR: "Ошибка анализа",
    },
    "competition_level": {
        CompetitionLevel.LOW: "Низкая",
        CompetitionLevel.MEDIUM: "Средняя",
        CompetitionLevel.HIGH: "Высокая",
    },
    "topic_status": {
        TopicStatus.SUGGESTED: "Предложена",
        TopicStatus.SAVED: "Сохранена",
        TopicStatus.PLANNED: "В плане",
        TopicStatus.IN_PROGRESS: "В работе",
        TopicStatus.USED: "Использована",
        TopicStatus.HIDDEN: "Скрыта",
    },
    "article_status": {
        ArticleStatus.DRAFT: "Черновик",
        ArticleStatus.REVIEW: "На проверке",
        ArticleStatus.READY: "Готова",
        ArticleStatus.SCHEDULED: "Запланирована",
        ArticleStatus.PUBLISHED: "Опубликована",
        ArticleStatus.FAILED: "Ошибка публикации",
        ArticleStatus.ARCHIVED: "Архив",
    },
    "schedule_status": {
        ScheduleStatus.PLANNED: "Запланирована",
        ScheduleStatus.READY: "Готова к публикации",
        ScheduleStatus.PUBLISHING: "Публикуется",
        ScheduleStatus.PUBLISHED: "Опубликована",
        ScheduleStatus.FAILED: "Ошибка",
        ScheduleStatus.CANCELLED: "Отменена",
    },
    "publication_method": {
        PublicationMethod.OFFICIAL_API: "Официальное API",
        PublicationMethod.PARTNER_SERVICE: "Партнёрский сервис",
        PublicationMethod.MANUAL_EXPORT: "Ручной экспорт",
        PublicationMethod.COPY_FORMATTED: "Копирование текста",
        PublicationMethod.FILE_EXPORT: "Файл Markdown или HTML",
        PublicationMethod.REMINDER: "Напоминание о публикации",
    },
    "integration_kind": {
        IntegrationKind.ANTHROPIC: "Anthropic Claude API",
        IntegrationKind.OPENAI: "OpenAI API",
        IntegrationKind.GEMINI: "Google Gemini API",
        IntegrationKind.YANDEX_METRIKA: "Яндекс Метрика",
        IntegrationKind.TELEGRAM: "Telegram",
        IntegrationKind.EMAIL: "Email",
        IntegrationKind.WEBHOOK: "Webhook",
        IntegrationKind.STORAGE: "Хранилище изображений",
        IntegrationKind.DZEN_CHANNEL: "Канал Яндекс Дзена",
        IntegrationKind.CSV: "Импорт и экспорт CSV",
    },
    "job_status": {
        JobStatus.PENDING: "В очереди",
        JobStatus.RUNNING: "Выполняется",
        JobStatus.SUCCESS: "Завершена",
        JobStatus.ERROR: "Ошибка",
        JobStatus.CANCELLED: "Отменена",
    },
}
