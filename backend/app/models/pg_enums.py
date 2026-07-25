"""Типы-перечисления PostgreSQL.

Каждый тип объявляется здесь ровно один раз и переиспользуется во всех моделях.
Иначе SQLAlchemy попытается создать один и тот же тип в базе несколько раз.
"""

from __future__ import annotations

from enum import StrEnum

from sqlalchemy import Enum as SAEnum

from app.models.enums import (
    AIProviderName,
    ArticleStatus,
    CompetitionLevel,
    CompetitorStatus,
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


def pg_enum(enum_cls: type[StrEnum], name: str) -> SAEnum:
    return SAEnum(
        enum_cls,
        name=name,
        values_callable=lambda e: [item.value for item in e],
    )


user_role_enum = pg_enum(UserRole, "user_role")
project_status_enum = pg_enum(ProjectStatus, "project_status")
data_source_enum = pg_enum(DataSource, "data_source")
competitor_status_enum = pg_enum(CompetitorStatus, "competitor_status")
competition_level_enum = pg_enum(CompetitionLevel, "competition_level")
topic_status_enum = pg_enum(TopicStatus, "topic_status")
topic_origin_enum = pg_enum(TopicOrigin, "topic_origin")
article_status_enum = pg_enum(ArticleStatus, "article_status")
schedule_status_enum = pg_enum(ScheduleStatus, "schedule_status")
publication_method_enum = pg_enum(PublicationMethod, "publication_method")
publication_result_enum = pg_enum(PublicationResult, "publication_result")
integration_kind_enum = pg_enum(IntegrationKind, "integration_kind")
ai_provider_name_enum = pg_enum(AIProviderName, "ai_provider_name")
job_status_enum = pg_enum(JobStatus, "job_status")
notification_level_enum = pg_enum(NotificationLevel, "notification_level")
