"""Точка сбора метаданных для Alembic.

Импортирует Base и все модели, чтобы `alembic revision --autogenerate`
видел полную схему.
"""

from app.models import Base  # noqa: F401
from app.models import (  # noqa: F401
    AIProviderSettings,
    AIUsage,
    AnalyticsSnapshot,
    Article,
    ArticleImage,
    ArticleVersion,
    AuditLog,
    Competitor,
    CompetitorAnalysis,
    CompetitorPublication,
    ContentPlan,
    Integration,
    JobRun,
    Notification,
    Project,
    PromptTemplate,
    PublicationLog,
    ScheduledPublication,
    Topic,
    TopicScore,
    User,
    Workspace,
    WorkspaceMember,
)

target_metadata = Base.metadata
