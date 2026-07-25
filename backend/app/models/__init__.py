"""Все модели базы данных.

Импорт здесь нужен, чтобы Alembic видел таблицы при автогенерации миграций.
"""

from app.models.ai import AIProviderSettings, AIUsage, PromptTemplate
from app.models.analytics import AnalyticsSnapshot
from app.models.article import Article, ArticleImage, ArticleVersion
from app.models.audit import AuditLog
from app.models.base import Base
from app.models.calendar import ContentPlan, ScheduledPublication
from app.models.competitor import Competitor, CompetitorAnalysis, CompetitorPublication
from app.models.enums import (
    ArticleStatus,
    CompetitorStatus,
    CompetitionLevel,
    DataSource,
    IntegrationKind,
    JobStatus,
    NotificationLevel,
    ProjectStatus,
    PublicationMethod,
    PublicationResult,
    ScheduleStatus,
    TopicOrigin,
    TopicStatus,
    UserRole,
)
from app.models.integration import Integration
from app.models.job import JobRun
from app.models.notification import Notification
from app.models.project import Project
from app.models.publication import PublicationLog
from app.models.topic import Topic, TopicScore
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember

__all__ = [
    "AIProviderSettings",
    "AIUsage",
    "AnalyticsSnapshot",
    "Article",
    "ArticleImage",
    "ArticleStatus",
    "ArticleVersion",
    "AuditLog",
    "Base",
    "CompetitionLevel",
    "Competitor",
    "CompetitorAnalysis",
    "CompetitorPublication",
    "CompetitorStatus",
    "ContentPlan",
    "DataSource",
    "Integration",
    "IntegrationKind",
    "JobRun",
    "JobStatus",
    "Notification",
    "NotificationLevel",
    "Project",
    "ProjectStatus",
    "PromptTemplate",
    "PublicationLog",
    "PublicationMethod",
    "PublicationResult",
    "ScheduleStatus",
    "ScheduledPublication",
    "Topic",
    "TopicOrigin",
    "TopicScore",
    "TopicStatus",
    "User",
    "UserRole",
    "Workspace",
    "WorkspaceMember",
]
