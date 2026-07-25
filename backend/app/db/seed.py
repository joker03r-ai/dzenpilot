"""Тестовые данные для быстрого знакомства с сервисом.

Запуск: python -m app.db.seed
Скрипт безопасно запускать повторно — если демо-пользователь уже есть,
данные не дублируются.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.config import settings
from app.db.session import AsyncSessionLocal, dispose_engine
from app.models.ai import PromptTemplate
from app.models.article import Article, ArticleVersion
from app.models.calendar import ScheduledPublication
from app.models.competitor import Competitor, CompetitorPublication
from app.models.enums import (
    ArticleStatus,
    CompetitionLevel,
    CompetitorStatus,
    DataSource,
    ScheduleStatus,
    TopicOrigin,
    TopicStatus,
)
from app.models.topic import Topic, TopicScore
from app.models.user import User
from app.services.auth_service import register_user

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("dzenpilot.seed")

SYSTEM_PROMPTS = [
    {
        "code": "competitor_analysis",
        "title": "Анализ конкурента",
        "description": "Разбор канала конкурента по собранным публикациям.",
        "template": (
            "Проанализируй канал «{competitor_name}» в Яндекс Дзене.\n"
            "Данные о публикациях:\n{publications}\n\n"
            "Если каких-то показателей нет, так и напиши «Данные недоступны»."
        ),
        "variables": ["competitor_name", "publications"],
    },
    {
        "code": "topic_search",
        "title": "Подбор тем",
        "description": "Поиск перспективных тем по нише и аудитории.",
        "template": (
            "Ниша: {niche}\nАудитория: {audience}\nРегион: {region}\n"
            "Формат: {format}\nЗапрещённые темы: {forbidden}\nЦель: {goal}\n\n"
            "Предложи темы статей и объясни перспективность каждой."
        ),
        "variables": ["niche", "audience", "region", "format", "forbidden", "goal"],
    },
    {
        "code": "article_outline",
        "title": "Структура статьи",
        "description": "Заголовки, лид, план, тезисы, заключение и призыв.",
        "template": (
            "Тема: {topic}\nЦель: {goal}\nАудитория: {audience}\nТон: {tone}\n"
            "Объём: около {length} знаков\nКлючевые слова: {keywords}\n\n"
            "Составь структуру статьи."
        ),
        "variables": ["topic", "goal", "audience", "tone", "length", "keywords"],
    },
    {
        "code": "article_write",
        "title": "Написание статьи",
        "description": "Полный текст по утверждённому плану.",
        "template": (
            "План статьи:\n{outline}\n\nОбязательные факты:\n{facts}\n"
            "Призыв к действию: {cta}\nЗапрещённые слова: {stopwords}\n\n"
            "Напиши готовую статью."
        ),
        "variables": ["outline", "facts", "cta", "stopwords"],
    },
]


async def seed() -> None:
    if not settings.seed_demo_data:
        logger.info("SEED_DEMO_DATA=false — тестовые данные не создаются")
        return

    async with AsyncSessionLocal() as db:
        await _seed_prompt_templates(db)

        existing = await db.execute(
            select(User).where(User.email == settings.seed_user_email.lower())
        )
        if existing.scalars().first() is not None:
            await db.commit()
            logger.info("Демо-пользователь уже существует, данные не дублируются")
            return

        user, _workspace, project = await register_user(
            db,
            email=settings.seed_user_email,
            password=settings.seed_user_password,
            full_name="Демо-автор",
            project_name="Канал про историю",
        )
        project.niche = "История и культура"
        project.target_audience = "Взрослые читатели 30–60 лет, интересующиеся историей"
        project.tone_of_voice = "Живой рассказ без academic-канцелярита"
        project.description = "Демонстрационный проект с примерами данных"

        competitor = Competitor(
            project_id=project.id,
            name="Хроники прошлого",
            url="https://dzen.ru/demo_history_chronicles",
            description="Канал о событиях XIX–XX веков, длинные разборы с фотографиями",
            niche="История",
            group_name="Основные конкуренты",
            notes="Публикует по будням, сильные заголовки с числами",
            subscribers_count=48_000,
            publications_count=312,
            avg_publish_interval_days=1.4,
            avg_views=21_500,
            max_views=184_000,
            min_views=1_200,
            avg_engagement_rate=4.8,
            avg_article_length=6_800,
            formats_used=["Разбор", "Подборка", "Личная история"],
            frequent_topics=["Быт XIX века", "Военная история", "Забытые изобретения"],
            popular_title_words=["почему", "как", "тайна", "правда"],
            media_usage={"images_per_article": 4, "video_share_percent": 6},
            data_source=DataSource.MANUAL,
            status=CompetitorStatus.ANALYZED,
            last_analyzed_at=datetime.now(UTC) - timedelta(days=2),
            created_by=user.id,
        )
        second_competitor = Competitor(
            project_id=project.id,
            name="Дневник краеведа",
            url="https://dzen.ru/demo_local_history",
            description="Региональная история, короткие заметки",
            niche="История",
            group_name="Основные конкуренты",
            subscribers_count=None,  # Данные недоступны — сервис их не выдумывает
            publications_count=96,
            avg_views=4_300,
            avg_article_length=2_400,
            formats_used=["Заметка", "Фотоподборка"],
            data_source=DataSource.MANUAL,
            status=CompetitorStatus.NEW,
            created_by=user.id,
        )
        db.add_all([competitor, second_competitor])
        await db.flush()

        demo_posts = [
            ("Почему в XIX веке письма шли месяцами: 7 причин", 184_000, 3_900, 610),
            ("Как жили простые крестьяне: 5 фактов, которые удивляют", 96_400, 2_100, 380),
            ("Тайна пропавшей экспедиции: что говорят документы", 54_200, 1_400, 205),
            ("Забытые изобретения, которые опередили время", 12_800, 340, 44),
            ("Короткая заметка о городском архиве", 1_200, 18, 3),
        ]
        for index, (title, views, reactions, comments) in enumerate(demo_posts):
            db.add(
                CompetitorPublication(
                    competitor_id=competitor.id,
                    title=title,
                    url=f"https://dzen.ru/demo_history_chronicles/post-{index + 1}",
                    published_at=datetime.now(UTC) - timedelta(days=3 * (index + 1)),
                    views=views,
                    reactions=reactions,
                    comments_count=comments,
                    topic_guess="Быт и повседневность",
                    format="Разбор",
                    title_length=len(title),
                    body_length=6_000 + index * 400,
                    title_emotionality=70 - index * 8,
                    has_numbers=any(char.isdigit() for char in title),
                    has_question="?" in title or title.lower().startswith("почему"),
                    has_cta=False,
                    audience_guess="Читатели 35–60 лет",
                    data_source=DataSource.MANUAL,
                )
            )

        topic = Topic(
            project_id=project.id,
            title="Как жили города Российской империи: быт, цены и зарплаты",
            description=(
                "Подробный разбор повседневной жизни горожан с конкретными цифрами "
                "и сравнением с современностью."
            ),
            niche="История",
            audience="Взрослые читатели, интересующиеся историей быта",
            region="Россия",
            format="Разбор с иллюстрациями",
            competition_level=CompetitionLevel.MEDIUM,
            seasonality="Ровный интерес круглый год",
            recommended_length=7_000,
            title_variants=[
                "Сколько стоила жизнь в 1900 году: цены, зарплаты, быт",
                "Как жили горожане Российской империи: 9 фактов",
                "Быт до революции: что могли позволить себе обычные люди",
            ],
            reader_questions=[
                "Сколько зарабатывал рабочий и что мог купить?",
                "Как выглядела квартира обычной семьи?",
                "Что было дорогим, а что дешёвым?",
            ],
            series_ideas=[
                "Цены и зарплаты по десятилетиям",
                "Быт разных сословий",
                "Транспорт и связь",
            ],
            monetization=["Партнёрские книги по истории", "Подписка на канал"],
            risks=["Нужны проверенные источники цифр", "Легко скатиться в пересказ учебника"],
            sources=[
                "Публикации конкурентов из раздела «Конкуренты»",
                "Данные, введённые пользователем",
            ],
            status=TopicStatus.SAVED,
            origin=TopicOrigin.MANUAL,
            created_by=user.id,
        )
        db.add(topic)
        await db.flush()

        db.add(
            TopicScore(
                topic_id=topic.id,
                total_score=84,
                interest_score=88,
                growth_score=72,
                competition_score=60,
                seasonality_score=80,
                competitor_success_score=90,
                series_potential_score=95,
                commercial_score=65,
                difficulty_score=55,
                decay_risk_score=25,
                audience_fit_score=92,
                explanation=(
                    "Оценка: 84 из 100. Тема растёт, конкуренция средняя, у конкурентов "
                    "есть успешные публикации, но мало подробных материалов для новичков."
                ),
            )
        )

        article = Article(
            project_id=project.id,
            topic_id=topic.id,
            title="Сколько стоила жизнь в 1900 году: цены, зарплаты и быт",
            lead=(
                "Разбираем, сколько зарабатывал городской рабочий, во что обходилась "
                "квартира и что считалось роскошью."
            ),
            body_markdown=(
                "## Зарплаты\n\nЭто демонстрационный черновик. Замените его своим текстом "
                "или сгенерируйте статью заново в мастере.\n\n"
                "Требуется проверка факта: конкретные суммы нужно сверить с источником.\n\n"
                "## Цены\n\nЗдесь будет сравнение цен на продукты, жильё и транспорт.\n"
            ),
            outline=["Зарплаты", "Цены", "Жильё", "Транспорт", "Выводы"],
            keywords=["история быта", "цены 1900", "зарплаты в империи"],
            cta="Подпишитесь, если хотите продолжение серии",
            goal="Дать читателю понятную картину повседневной жизни",
            audience="Взрослые читатели 30–60 лет",
            tone="Живой рассказ",
            target_length=7_000,
            status=ArticleStatus.DRAFT,
            checklist={
                "title": True,
                "cover": False,
                "structure": True,
                "links": False,
                "facts_checked": False,
                "cta": True,
                "schedule": False,
            },
            word_count=64,
            reading_time_min=1,
            author_id=user.id,
        )
        db.add(article)
        await db.flush()

        db.add(
            ArticleVersion(
                article_id=article.id,
                version_number=1,
                title=article.title,
                lead=article.lead,
                body_markdown=article.body_markdown,
                outline=article.outline,
                change_note="Первая версия из тестовых данных",
                created_by=user.id,
            )
        )
        db.add(
            ScheduledPublication(
                project_id=project.id,
                article_id=article.id,
                scheduled_at=datetime.now(UTC) + timedelta(days=1, hours=3),
                timezone="Europe/Moscow",
                note="Демонстрационная запись календаря",
                confirmed_by_user=False,
                status=ScheduleStatus.PLANNED,
            )
        )

        await db.commit()
        logger.info(
            "Тестовые данные созданы. Вход: %s / %s",
            settings.seed_user_email,
            settings.seed_user_password,
        )


async def _seed_prompt_templates(db) -> None:
    for item in SYSTEM_PROMPTS:
        exists = await db.execute(
            select(PromptTemplate).where(
                PromptTemplate.code == item["code"],
                PromptTemplate.project_id.is_(None),
                PromptTemplate.version == 1,
            )
        )
        if exists.scalars().first() is None:
            db.add(
                PromptTemplate(
                    project_id=None,
                    code=item["code"],
                    title=item["title"],
                    description=item["description"],
                    template=item["template"],
                    variables=item["variables"],
                    is_system=True,
                    version=1,
                )
            )


async def main() -> None:
    try:
        await seed()
    finally:
        await dispose_engine()


if __name__ == "__main__":
    asyncio.run(main())
