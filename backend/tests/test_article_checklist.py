"""Тесты чек-листа перед публикацией.

Чек-лист работает без ИИ и без базы, поэтому проверяется напрямую.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.models.article import Article
from app.services.article_service import build_checklist


def make_article(**overrides) -> Article:
    defaults = {
        "title": "Сколько стоила жизнь в 1900 году: цены и зарплаты",
        "cta": "Подпишитесь, если хотите продолжение",
        "body_markdown": (
            "## Зарплаты\n\nОбычный рабочий получал около рубля в день.\n\n"
            "## Цены\n\nХлеб стоил копейки, жильё съедало треть дохода.\n"
        ),
        "generation_input": {"forbidden_words": []},
        "checklist": {},
        "planned_publish_at": datetime.now(UTC),
    }
    defaults.update(overrides)
    return Article(**defaults)


def get_item(result, code: str):
    return next(item for item in result.items if item.code == code)


def test_ready_article_passes_all_checks() -> None:
    result = build_checklist(make_article(), has_cover=True)

    assert result.ready is True
    assert "готова к публикации" in result.message
    assert all(item.done for item in result.items)


def test_missing_cover_blocks_readiness() -> None:
    result = build_checklist(make_article(), has_cover=False)

    assert result.ready is False
    assert get_item(result, "cover").done is False


def test_short_title_is_rejected() -> None:
    result = build_checklist(make_article(title="Быт"), has_cover=True)

    assert get_item(result, "title").done is False


def test_structure_requires_two_subheadings() -> None:
    result = build_checklist(
        make_article(body_markdown="Просто текст без подзаголовков"), has_cover=True
    )

    assert get_item(result, "structure").done is False


def test_unverified_facts_are_counted() -> None:
    body = (
        "## Раздел\n\nВ 1900 году зарплата была 25 рублей.\n"
        "Требуется проверка факта\n\n## Второй\n\nЕщё текст.\n"
        "Требуется проверка факта\n"
    )
    result = build_checklist(make_article(body_markdown=body), has_cover=True)

    facts = get_item(result, "facts")
    assert facts.done is False
    assert "2" in facts.hint


def test_forbidden_words_are_detected() -> None:
    result = build_checklist(
        make_article(
            body_markdown="## Раздел\n\nЭто гарантированный доход.\n\n## Второй\n\nТекст.",
            generation_input={"forbidden_words": ["гарантированный"]},
        ),
        has_cover=True,
    )

    forbidden = get_item(result, "forbidden")
    assert forbidden.done is False
    assert "гарантированный" in forbidden.hint


def test_missing_cta_blocks_readiness() -> None:
    result = build_checklist(make_article(cta=None), has_cover=True)

    assert get_item(result, "cta").done is False


def test_missing_schedule_blocks_readiness() -> None:
    result = build_checklist(make_article(planned_publish_at=None), has_cover=True)

    assert get_item(result, "schedule").done is False
    assert result.ready is False


def test_links_require_manual_confirmation() -> None:
    body = "## Раздел\n\nИсточник: https://example.ru/page\n\n## Второй\n\nТекст."
    result = build_checklist(make_article(body_markdown=body), has_cover=True)

    links = get_item(result, "links")
    assert links.done is False
    assert "1 ссылок" in links.hint

    confirmed = build_checklist(
        make_article(body_markdown=body, checklist={"links_checked": True}), has_cover=True
    )
    assert get_item(confirmed, "links").done is True
