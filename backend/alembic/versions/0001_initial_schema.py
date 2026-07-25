"""Начальная схема DzenPilot: все 20 сущностей MVP.

Revision ID: 0001
Revises:
Create Date: 2026-07-25
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# --- Типы-перечисления ---
user_role = postgresql.ENUM(
    "owner", "editor", "author", "viewer", name="user_role", create_type=False
)
project_status = postgresql.ENUM(
    "active", "paused", "archived", name="project_status", create_type=False
)
data_source = postgresql.ENUM(
    "manual", "csv_import", "public_page", "official_api", "ai_estimate",
    name="data_source", create_type=False,
)
competitor_status = postgresql.ENUM(
    "new", "analyzing", "analyzed", "error", name="competitor_status", create_type=False
)
competition_level = postgresql.ENUM(
    "low", "medium", "high", name="competition_level", create_type=False
)
topic_status = postgresql.ENUM(
    "suggested", "saved", "planned", "in_progress", "used", "hidden",
    name="topic_status", create_type=False,
)
topic_origin = postgresql.ENUM(
    "ai_search", "manual", "csv_import", "competitor_gap",
    name="topic_origin", create_type=False,
)
article_status = postgresql.ENUM(
    "draft", "review", "ready", "scheduled", "published", "failed", "archived",
    name="article_status", create_type=False,
)
schedule_status = postgresql.ENUM(
    "planned", "ready", "publishing", "published", "failed", "cancelled",
    name="schedule_status", create_type=False,
)
publication_method = postgresql.ENUM(
    "official_api", "partner_service", "manual_export", "copy_formatted",
    "file_export", "reminder",
    name="publication_method", create_type=False,
)
publication_result = postgresql.ENUM(
    "success", "error", "skipped", name="publication_result", create_type=False
)
integration_kind = postgresql.ENUM(
    "anthropic", "openai", "gemini", "yandex_metrika", "telegram", "email",
    "webhook", "storage", "dzen_channel", "csv",
    name="integration_kind", create_type=False,
)
ai_provider_name = postgresql.ENUM(
    "anthropic", "openai", "gemini", "local", name="ai_provider_name", create_type=False
)
job_status = postgresql.ENUM(
    "pending", "running", "success", "error", "cancelled",
    name="job_status", create_type=False,
)
notification_level = postgresql.ENUM(
    "info", "success", "warning", "error", name="notification_level", create_type=False
)

ALL_ENUMS = [
    user_role, project_status, data_source, competitor_status, competition_level,
    topic_status, topic_origin, article_status, schedule_status, publication_method,
    publication_result, integration_kind, ai_provider_name, job_status, notification_level,
]

NOW = sa.text("now()")


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
    ]


def upgrade() -> None:
    bind = op.get_bind()
    for enum_type in ALL_ENUMS:
        enum_type.create(bind, checkfirst=True)

    # ---------------- users ----------------
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        *_timestamps(),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ---------------- workspaces ----------------
    op.create_table(
        "workspaces",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        *_timestamps(),
    )
    op.create_index("ix_workspaces_owner_id", "workspaces", ["owner_id"])

    op.create_table(
        "workspace_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", user_role, nullable=False, server_default="owner"),
        sa.Column("invited_at", sa.DateTime(timezone=True)),
        sa.Column("accepted_at", sa.DateTime(timezone=True)),
        *_timestamps(),
        sa.UniqueConstraint(
            "workspace_id", "user_id", name="uq_workspace_members_workspace_user"
        ),
    )
    op.create_index("ix_workspace_members_workspace_id", "workspace_members", ["workspace_id"])
    op.create_index("ix_workspace_members_user_id", "workspace_members", ["user_id"])

    # ---------------- projects ----------------
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("niche", sa.String(255)),
        sa.Column("target_audience", sa.Text()),
        sa.Column("tone_of_voice", sa.String(255)),
        sa.Column("region", sa.String(120)),
        sa.Column("timezone", sa.String(64), nullable=False, server_default="Europe/Moscow"),
        sa.Column("dzen_channel_url", sa.String(500)),
        sa.Column("status", project_status, nullable=False, server_default="active"),
        sa.Column("settings", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        *_timestamps(),
    )
    op.create_index("ix_projects_workspace_id", "projects", ["workspace_id"])
    op.create_index("ix_projects_deleted_at", "projects", ["deleted_at"])
    op.create_index("ix_projects_workspace_status", "projects", ["workspace_id", "status"])

    # ---------------- integrations ----------------
    op.create_table(
        "integrations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", integration_kind, nullable=False),
        sa.Column("title", sa.String(255), nullable=False, server_default="Основное"),
        sa.Column("credentials_encrypted", sa.LargeBinary()),
        sa.Column("config", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_check_at", sa.DateTime(timezone=True)),
        sa.Column("last_check_result", sa.Text()),
        *_timestamps(),
        sa.UniqueConstraint(
            "project_id", "kind", "title", name="uq_integrations_project_kind_title"
        ),
    )
    op.create_index("ix_integrations_project_id", "integrations", ["project_id"])

    # ---------------- competitors ----------------
    op.create_table(
        "competitors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("url", sa.String(500)),
        sa.Column("description", sa.Text()),
        sa.Column("niche", sa.String(255)),
        sa.Column("group_name", sa.String(120)),
        sa.Column("notes", sa.Text()),
        sa.Column("subscribers_count", sa.Integer()),
        sa.Column("publications_count", sa.Integer()),
        sa.Column("avg_publish_interval_days", sa.Numeric(8, 2)),
        sa.Column("avg_views", sa.Integer()),
        sa.Column("max_views", sa.Integer()),
        sa.Column("min_views", sa.Integer()),
        sa.Column("avg_engagement_rate", sa.Numeric(6, 3)),
        sa.Column("avg_article_length", sa.Integer()),
        sa.Column("formats_used", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("frequent_topics", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("popular_title_words", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("media_usage", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("data_source", data_source, nullable=False, server_default="manual"),
        sa.Column("status", competitor_status, nullable=False, server_default="new"),
        sa.Column("last_analyzed_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        *_timestamps(),
        sa.UniqueConstraint("project_id", "url", name="uq_competitors_project_url"),
    )
    op.create_index("ix_competitors_project_id", "competitors", ["project_id"])
    op.create_index("ix_competitors_deleted_at", "competitors", ["deleted_at"])
    op.create_index("ix_competitors_project_status", "competitors", ["project_id", "status"])
    op.create_index("ix_competitors_project_group", "competitors", ["project_id", "group_name"])

    op.create_table(
        "competitor_publications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "competitor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("competitors.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("url", sa.String(700)),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("views", sa.Integer()),
        sa.Column("reactions", sa.Integer()),
        sa.Column("comments_count", sa.Integer()),
        sa.Column("topic_guess", sa.String(255)),
        sa.Column("format", sa.String(120)),
        sa.Column("title_length", sa.Integer()),
        sa.Column("body_length", sa.Integer()),
        sa.Column("title_emotionality", sa.Integer()),
        sa.Column("has_numbers", sa.Boolean()),
        sa.Column("has_question", sa.Boolean()),
        sa.Column("has_cta", sa.Boolean()),
        sa.Column("audience_guess", sa.String(255)),
        sa.Column("raw_excerpt", sa.Text()),
        sa.Column("data_source", data_source, nullable=False, server_default="manual"),
        *_timestamps(),
        sa.UniqueConstraint("competitor_id", "url", name="uq_competitor_publications_url"),
    )
    op.create_index(
        "ix_competitor_publications_competitor_id", "competitor_publications", ["competitor_id"]
    )
    op.create_index(
        "ix_competitor_publications_date",
        "competitor_publications",
        ["competitor_id", "published_at"],
    )

    op.create_table(
        "competitor_analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "competitor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("competitors.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("summary", sa.Text()),
        sa.Column("why_it_works", sa.Text()),
        sa.Column("publish_rhythm", sa.Text()),
        sa.Column("working_topics", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("working_titles", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("failed_posts", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("formats", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("strengths", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("weaknesses", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("content_gaps", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("differentiation", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("adaptable_ideas", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("ai_provider", sa.String(60)),
        sa.Column("ai_model", sa.String(120)),
        sa.Column("prompt_used", sa.Text()),
        sa.Column("tokens_input", sa.Integer()),
        sa.Column("tokens_output", sa.Integer()),
        sa.Column("cost_usd", sa.Numeric(10, 4)),
        *_timestamps(),
    )
    op.create_index(
        "ix_competitor_analyses_competitor_id", "competitor_analyses", ["competitor_id"]
    )
    op.create_index("ix_competitor_analyses_project_id", "competitor_analyses", ["project_id"])
    op.create_index(
        "ix_competitor_analyses_recent", "competitor_analyses", ["competitor_id", "created_at"]
    )

    # ---------------- topics ----------------
    op.create_table(
        "topics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("niche", sa.String(255)),
        sa.Column("audience", sa.String(500)),
        sa.Column("region", sa.String(120)),
        sa.Column("format", sa.String(120)),
        sa.Column("competition_level", competition_level),
        sa.Column("seasonality", sa.String(255)),
        sa.Column("recommended_length", sa.Integer()),
        sa.Column("title_variants", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("reader_questions", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("series_ideas", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("monetization", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("risks", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("sources", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("status", topic_status, nullable=False, server_default="suggested"),
        sa.Column("origin", topic_origin, nullable=False, server_default="manual"),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        *_timestamps(),
    )
    op.create_index("ix_topics_project_id", "topics", ["project_id"])
    op.create_index("ix_topics_deleted_at", "topics", ["deleted_at"])
    op.create_index("ix_topics_project_status", "topics", ["project_id", "status"])
    op.create_index("ix_topics_project_created", "topics", ["project_id", "created_at"])

    op.create_table(
        "topic_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "topic_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("topics.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("total_score", sa.Integer(), nullable=False),
        sa.Column("interest_score", sa.Integer()),
        sa.Column("growth_score", sa.Integer()),
        sa.Column("competition_score", sa.Integer()),
        sa.Column("seasonality_score", sa.Integer()),
        sa.Column("competitor_success_score", sa.Integer()),
        sa.Column("series_potential_score", sa.Integer()),
        sa.Column("commercial_score", sa.Integer()),
        sa.Column("difficulty_score", sa.Integer()),
        sa.Column("decay_risk_score", sa.Integer()),
        sa.Column("audience_fit_score", sa.Integer()),
        sa.Column("explanation", sa.Text()),
        sa.Column("formula_version", sa.String(20), nullable=False, server_default="1.0"),
        *_timestamps(),
    )
    op.create_index("ix_topic_scores_topic_id", "topic_scores", ["topic_id"])
    op.create_index("ix_topic_scores_recent", "topic_scores", ["topic_id", "created_at"])

    # ---------------- articles ----------------
    op.create_table(
        "articles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "topic_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("topics.id", ondelete="SET NULL"),
        ),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("slug", sa.String(500)),
        sa.Column("lead", sa.Text()),
        sa.Column("body_markdown", sa.Text()),
        sa.Column("body_html", sa.Text()),
        sa.Column("outline", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("keywords", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("cta", sa.Text()),
        sa.Column("goal", sa.String(500)),
        sa.Column("audience", sa.String(500)),
        sa.Column("tone", sa.String(120)),
        sa.Column("target_length", sa.Integer()),
        sa.Column("status", article_status, nullable=False, server_default="draft"),
        sa.Column("checklist", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("generation_input", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("planned_publish_at", sa.DateTime(timezone=True)),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("published_url", sa.String(700)),
        sa.Column(
            "channel_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("integrations.id", ondelete="SET NULL"),
        ),
        sa.Column("ai_provider", sa.String(60)),
        sa.Column("ai_model", sa.String(120)),
        sa.Column("prompt_used", sa.Text()),
        sa.Column("tokens_input", sa.Integer()),
        sa.Column("tokens_output", sa.Integer()),
        sa.Column("cost_usd", sa.Numeric(10, 4)),
        sa.Column("word_count", sa.Integer()),
        sa.Column("reading_time_min", sa.Integer()),
        sa.Column(
            "author_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        *_timestamps(),
    )
    op.create_index("ix_articles_project_id", "articles", ["project_id"])
    op.create_index("ix_articles_topic_id", "articles", ["topic_id"])
    op.create_index("ix_articles_deleted_at", "articles", ["deleted_at"])
    op.create_index("ix_articles_project_status", "articles", ["project_id", "status"])
    op.create_index("ix_articles_project_planned", "articles", ["project_id", "planned_publish_at"])

    op.create_table(
        "article_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "article_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("articles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(500)),
        sa.Column("lead", sa.Text()),
        sa.Column("body_markdown", sa.Text()),
        sa.Column("outline", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("change_note", sa.String(500)),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        *_timestamps(),
        sa.UniqueConstraint("article_id", "version_number", name="uq_article_versions_number"),
    )
    op.create_index("ix_article_versions_article_id", "article_versions", ["article_id"])

    op.create_table(
        "article_images",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "article_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("articles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("url", sa.String(700)),
        sa.Column("storage_key", sa.String(500)),
        sa.Column("alt_text", sa.String(500)),
        sa.Column("prompt_used", sa.Text()),
        sa.Column("is_cover", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("width", sa.Integer()),
        sa.Column("height", sa.Integer()),
        *_timestamps(),
    )
    op.create_index("ix_article_images_article_id", "article_images", ["article_id"])
    op.create_index("ix_article_images_order", "article_images", ["article_id", "position"])

    # ---------------- календарь ----------------
    op.create_table(
        "content_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("period_start", sa.Date()),
        sa.Column("period_end", sa.Date()),
        sa.Column("notes", sa.Text()),
        *_timestamps(),
    )
    op.create_index("ix_content_plans_project_id", "content_plans", ["project_id"])

    op.create_table(
        "scheduled_publications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "article_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("articles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "content_plan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("content_plans.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "channel_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("integrations.id", ondelete="SET NULL"),
        ),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("timezone", sa.String(64), nullable=False, server_default="Europe/Moscow"),
        sa.Column("repeat_rule", sa.String(255)),
        sa.Column("note", sa.Text()),
        sa.Column(
            "confirmed_by_user", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column("status", schedule_status, nullable=False, server_default="planned"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        *_timestamps(),
    )
    op.create_index("ix_scheduled_publications_project_id", "scheduled_publications", ["project_id"])
    op.create_index("ix_scheduled_publications_article_id", "scheduled_publications", ["article_id"])
    op.create_index(
        "ix_scheduled_publications_project_time",
        "scheduled_publications",
        ["project_id", "scheduled_at"],
    )
    op.create_index(
        "ix_scheduled_publications_status_time",
        "scheduled_publications",
        ["status", "scheduled_at"],
    )

    op.create_table(
        "publication_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "scheduled_publication_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("scheduled_publications.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "article_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("articles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("method", publication_method, nullable=False),
        sa.Column("result", publication_result, nullable=False),
        sa.Column("published_url", sa.String(700)),
        sa.Column("response_payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("error_message", sa.Text()),
        sa.Column("attempt_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        *_timestamps(),
    )
    op.create_index(
        "ix_publication_logs_scheduled_publication_id",
        "publication_logs",
        ["scheduled_publication_id"],
    )
    op.create_index("ix_publication_logs_article_id", "publication_logs", ["article_id"])
    op.create_index("ix_publication_logs_project_id", "publication_logs", ["project_id"])
    op.create_index(
        "ix_publication_logs_article_time", "publication_logs", ["article_id", "started_at"]
    )

    # ---------------- ИИ ----------------
    op.create_table(
        "ai_provider_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider", ai_provider_name, nullable=False),
        sa.Column("model", sa.String(120), nullable=False),
        sa.Column("temperature", sa.Numeric(3, 2), nullable=False, server_default="0.70"),
        sa.Column("max_tokens", sa.Integer(), nullable=False, server_default="4096"),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("params", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_timestamps(),
        sa.UniqueConstraint("project_id", "provider", "model", name="uq_ai_settings_project_model"),
    )
    op.create_index("ix_ai_provider_settings_project_id", "ai_provider_settings", ["project_id"])

    op.create_table(
        "prompt_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
        ),
        sa.Column("code", sa.String(120), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("template", sa.Text(), nullable=False),
        sa.Column("variables", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        *_timestamps(),
        sa.UniqueConstraint("project_id", "code", "version", name="uq_prompt_templates_code"),
    )
    op.create_index("ix_prompt_templates_project_id", "prompt_templates", ["project_id"])

    op.create_table(
        "ai_usage",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
        ),
        sa.Column("provider", sa.String(60), nullable=False),
        sa.Column("model", sa.String(120), nullable=False),
        sa.Column("operation", sa.String(120), nullable=False),
        sa.Column("tokens_input", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tokens_output", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Numeric(10, 4)),
        sa.Column("entity_type", sa.String(60)),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True)),
        *_timestamps(),
    )
    op.create_index("ix_ai_usage_project_id", "ai_usage", ["project_id"])
    op.create_index("ix_ai_usage_project_created", "ai_usage", ["project_id", "created_at"])

    # ---------------- аналитика, уведомления, аудит, задачи ----------------
    op.create_table(
        "analytics_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "article_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("articles.id", ondelete="CASCADE"),
        ),
        sa.Column("captured_for", sa.Date(), nullable=False),
        sa.Column("views", sa.Integer()),
        sa.Column("reads", sa.Integer()),
        sa.Column("subscribers", sa.Integer()),
        sa.Column("reactions", sa.Integer()),
        sa.Column("comments_count", sa.Integer()),
        sa.Column("ctr", sa.Numeric(6, 3)),
        sa.Column("source", data_source, nullable=False, server_default="manual"),
        *_timestamps(),
        sa.UniqueConstraint(
            "project_id", "article_id", "captured_for", "source", name="uq_analytics_snapshots_day"
        ),
    )
    op.create_index("ix_analytics_snapshots_project_id", "analytics_snapshots", ["project_id"])
    op.create_index("ix_analytics_snapshots_article_id", "analytics_snapshots", ["article_id"])
    op.create_index(
        "ix_analytics_snapshots_project_day", "analytics_snapshots", ["project_id", "captured_for"]
    )

    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
        ),
        sa.Column("kind", sa.String(120), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text()),
        sa.Column("level", notification_level, nullable=False, server_default="info"),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_timestamps(),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_project_id", "notifications", ["project_id"])
    op.create_index(
        "ix_notifications_user_unread", "notifications", ["user_id", "is_read", "created_at"]
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
        ),
        sa.Column("action", sa.String(120), nullable=False),
        sa.Column("entity_type", sa.String(60)),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True)),
        sa.Column("ip_address", sa.String(64)),
        sa.Column("user_agent", sa.String(500)),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_timestamps(),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_project_id", "audit_logs", ["project_id"])
    op.create_index("ix_audit_logs_project_created", "audit_logs", ["project_id", "created_at"])

    op.create_table(
        "job_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column("task_name", sa.String(120), nullable=False),
        sa.Column("celery_task_id", sa.String(120)),
        sa.Column("status", job_status, nullable=False, server_default="pending"),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("result", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("error_message", sa.Text()),
        sa.Column("retries", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("entity_type", sa.String(60)),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True)),
        *_timestamps(),
    )
    op.create_index("ix_job_runs_project_id", "job_runs", ["project_id"])
    op.create_index("ix_job_runs_celery_task_id", "job_runs", ["celery_task_id"])
    op.create_index("ix_job_runs_project_status", "job_runs", ["project_id", "status", "created_at"])


def downgrade() -> None:
    for table in [
        "job_runs",
        "audit_logs",
        "notifications",
        "analytics_snapshots",
        "ai_usage",
        "prompt_templates",
        "ai_provider_settings",
        "publication_logs",
        "scheduled_publications",
        "content_plans",
        "article_images",
        "article_versions",
        "articles",
        "topic_scores",
        "topics",
        "competitor_analyses",
        "competitor_publications",
        "competitors",
        "integrations",
        "projects",
        "workspace_members",
        "workspaces",
        "users",
    ]:
        op.drop_table(table)

    bind = op.get_bind()
    for enum_type in reversed(ALL_ENUMS):
        enum_type.drop(bind, checkfirst=True)
