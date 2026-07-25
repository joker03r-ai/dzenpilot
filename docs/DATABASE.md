# DzenPilot — схема базы данных

СУБД: PostgreSQL 16. Все таблицы имеют `id UUID PRIMARY KEY`, `created_at`, `updated_at`.
Удаление пользовательских сущностей — мягкое (`deleted_at`), чтобы можно было восстановить.

## 1. Пользователи и доступ

### users
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID PK | |
| email | citext UNIQUE NOT NULL | логин |
| password_hash | text NOT NULL | bcrypt, открытый пароль не хранится |
| full_name | text | |
| is_active | bool default true | |
| is_superuser | bool default false | |
| last_login_at | timestamptz | |
| created_at / updated_at | timestamptz | |

Индексы: `ix_users_email` (unique).

### workspaces
`id`, `name`, `owner_id → users.id`, `created_at`, `updated_at`.
Индекс: `ix_workspaces_owner_id`.

### workspace_members
`id`, `workspace_id → workspaces.id`, `user_id → users.id`,
`role ENUM(owner, editor, author, viewer)`, `invited_at`, `accepted_at`.
Уникальный индекс: `(workspace_id, user_id)`.

### projects
`id`, `workspace_id`, `name`, `description`, `niche`, `target_audience`,
`tone_of_voice`, `region`, `timezone` (default `Europe/Moscow`), `dzen_channel_url`,
`status ENUM(active, paused, archived)`, `settings JSONB`, `created_at`, `updated_at`, `deleted_at`.
Индексы: `(workspace_id, status)`, `ix_projects_deleted_at`.

## 2. Конкуренты

### competitors
`id`, `project_id`, `name`, `url`, `description`, `niche`, `group_name`, `notes`,
`subscribers_count`, `publications_count`, `avg_publish_interval_days`,
`avg_views`, `max_views`, `min_views`, `avg_engagement_rate`,
`avg_article_length`, `formats_used JSONB`, `frequent_topics JSONB`,
`popular_title_words JSONB`, `media_usage JSONB`,
`data_source ENUM(manual, csv_import, public_page, official_api, ai_estimate)`,
`last_analyzed_at`, `status ENUM(new, analyzing, analyzed, error)`,
`created_by`, `created_at`, `updated_at`, `deleted_at`.

Все числовые показатели допускают `NULL` — это означает «Данные недоступны».
Индексы: `(project_id, status)`, `(project_id, group_name)`, unique `(project_id, url)`.

### competitor_publications
`id`, `competitor_id`, `title`, `url`, `published_at`, `views`, `reactions`, `comments_count`,
`topic_guess`, `format`, `title_length`, `body_length`, `title_emotionality` (0–100),
`has_numbers bool`, `has_question bool`, `has_cta bool`, `audience_guess`,
`raw_excerpt`, `data_source`, `created_at`, `updated_at`.
Индексы: `(competitor_id, published_at DESC)`, unique `(competitor_id, url)`.

### competitor_analyses
`id`, `competitor_id`, `project_id`, `summary`, `why_it_works`, `working_topics JSONB`,
`working_titles JSONB`, `failed_posts JSONB`, `publish_rhythm`, `formats JSONB`,
`strengths JSONB`, `weaknesses JSONB`, `content_gaps JSONB`, `differentiation JSONB`,
`adaptable_ideas JSONB`, `ai_provider`, `ai_model`, `prompt_used`,
`tokens_input`, `tokens_output`, `cost_usd`, `created_at`.
Индекс: `(competitor_id, created_at DESC)`.

## 3. Темы

### topics
`id`, `project_id`, `title`, `description`, `niche`, `audience`, `region`, `format`,
`competition_level ENUM(low, medium, high)`, `seasonality`, `recommended_length`,
`title_variants JSONB`, `reader_questions JSONB`, `series_ideas JSONB`,
`monetization JSONB`, `risks JSONB`, `sources JSONB`,
`status ENUM(suggested, saved, planned, in_progress, used, hidden)`,
`origin ENUM(ai_search, manual, csv_import, competitor_gap)`,
`created_by`, `created_at`, `updated_at`, `deleted_at`.
Индексы: `(project_id, status)`, `(project_id, created_at DESC)`.

### topic_scores
`id`, `topic_id`, `total_score` (0–100), а также частные оценки:
`interest_score`, `growth_score`, `competition_score`, `seasonality_score`,
`competitor_success_score`, `series_potential_score`, `commercial_score`,
`difficulty_score`, `decay_risk_score`, `audience_fit_score`,
`explanation` (текст объяснения), `formula_version`, `created_at`.
Индекс: `(topic_id, created_at DESC)`.

## 4. Статьи

### articles
`id`, `project_id`, `topic_id`, `title`, `slug`, `lead`, `body_markdown`, `body_html`,
`outline JSONB`, `keywords JSONB`, `cta`, `goal`, `audience`, `tone`, `target_length`,
`status ENUM(draft, review, ready, scheduled, published, failed, archived)`,
`checklist JSONB`, `planned_publish_at`, `published_at`, `published_url`,
`channel_id`, `ai_provider`, `ai_model`, `prompt_used`,
`tokens_input`, `tokens_output`, `cost_usd`, `word_count`, `reading_time_min`,
`author_id`, `created_at`, `updated_at`, `deleted_at`.
Индексы: `(project_id, status)`, `(project_id, planned_publish_at)`, `ix_articles_topic_id`.

### article_versions
`id`, `article_id`, `version_number`, `title`, `body_markdown`, `outline JSONB`,
`change_note`, `created_by`, `created_at`.
Уникальный индекс: `(article_id, version_number)`. Служит для автосохранения и отката.

### article_images
`id`, `article_id`, `url`, `storage_key`, `alt_text`, `prompt_used`, `is_cover bool`,
`position`, `width`, `height`, `created_at`.
Индекс: `(article_id, position)`.

## 5. План и публикации

### content_plans
`id`, `project_id`, `name`, `period_start`, `period_end`, `notes`, `created_at`, `updated_at`.

### scheduled_publications
`id`, `project_id`, `article_id`, `content_plan_id`, `channel_id`,
`scheduled_at timestamptz` (хранится в UTC), `timezone` (например `Europe/Moscow`),
`repeat_rule`, `note`, `confirmed_by_user bool default false`,
`status ENUM(planned, ready, publishing, published, failed, cancelled)`,
`attempts int default 0`, `created_at`, `updated_at`.
Индексы: `(project_id, scheduled_at)`, `(status, scheduled_at)`.

### publication_logs
`id`, `scheduled_publication_id`, `article_id`, `method ENUM(official_api, partner_service,
manual_export, copy_formatted, file_export, reminder)`,
`result ENUM(success, error, skipped)`, `published_url`, `response_payload JSONB`,
`error_message`, `attempt_number`, `started_at`, `finished_at`.
Индекс: `(article_id, started_at DESC)`.

## 6. Интеграции и ИИ

### integrations
`id`, `project_id`, `kind ENUM(anthropic, openai, gemini, yandex_metrika, telegram, email,
webhook, storage, dzen_channel, csv)`, `title`, `credentials_encrypted bytea`,
`config JSONB`, `is_active bool`, `last_check_at`, `last_check_result`,
`created_at`, `updated_at`.
Уникальный индекс: `(project_id, kind, title)`. Ключи хранятся только в зашифрованном виде.

### ai_provider_settings
`id`, `project_id`, `provider ENUM(anthropic, openai, gemini, local)`, `model`,
`temperature`, `max_tokens`, `is_default bool`, `params JSONB`, `created_at`, `updated_at`.

### prompt_templates
`id`, `project_id` (NULL — системный шаблон), `code`, `title`, `description`,
`template`, `variables JSONB`, `is_system bool`, `version`, `created_at`, `updated_at`.
Уникальный индекс: `(project_id, code, version)`.

### ai_usage
`id`, `project_id`, `provider`, `model`, `operation`, `tokens_input`, `tokens_output`,
`cost_usd`, `entity_type`, `entity_id`, `created_at`.

## 7. Аналитика, уведомления, аудит, задачи

### analytics_snapshots
`id`, `project_id`, `article_id` (NULL — сводка по проекту), `captured_for date`,
`views`, `reads`, `subscribers`, `reactions`, `comments_count`, `ctr`,
`source ENUM(manual, csv_import, official_api)`, `created_at`.
Уникальный индекс: `(project_id, article_id, captured_for, source)`.

### notifications
`id`, `user_id`, `project_id`, `kind`, `title`, `body`, `level ENUM(info, success, warning, error)`,
`is_read bool`, `payload JSONB`, `created_at`.
Индекс: `(user_id, is_read, created_at DESC)`.

### audit_logs
`id`, `user_id`, `project_id`, `action`, `entity_type`, `entity_id`,
`ip_address`, `user_agent`, `payload JSONB`, `created_at`.
Индекс: `(project_id, created_at DESC)`.

### job_runs
`id`, `project_id`, `task_name`, `celery_task_id`,
`status ENUM(pending, running, success, error, cancelled)`, `progress int (0–100)`,
`started_at`, `finished_at`, `result JSONB`, `error_message`, `retries int`,
`created_at`, `updated_at`.
Индекс: `(project_id, status, created_at DESC)`.

## 8. Правила целостности

* Каскадное удаление `ON DELETE CASCADE` внутри проекта (конкурент → публикации → анализы).
* Валюта затрат — доллар США (`cost_usd numeric(10,4)`), поле необязательное.
* Все даты в базе — `timestamptz` в UTC. Часовой пояс отображения хранится отдельно строкой.
