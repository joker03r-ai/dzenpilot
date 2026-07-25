"""Тесты подготовки статьи к публикации.

Главное здесь — экранирование: в готовый HTML не должен попадать
исполняемый код из текста статьи.
"""

from __future__ import annotations

from app.models.article import Article
from app.services import export_service


def make_article(**overrides) -> Article:
    defaults = {
        "title": "Как жили города в 1900 году",
        "slug": "kak-zhili-goroda",
        "lead": "Короткое вступление.",
        "body_markdown": "## Раздел\n\nАбзац текста.\n",
        "cta": "Подпишитесь на канал",
    }
    defaults.update(overrides)
    return Article(**defaults)


def test_headings_are_converted() -> None:
    html = export_service.markdown_to_html("## Заголовок\n\nТекст")

    assert "<h2>Заголовок</h2>" in html
    assert "<p>Текст</p>" in html


def test_script_tag_is_escaped() -> None:
    html = export_service.markdown_to_html("<script>alert('взлом')</script>")

    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_script_in_heading_is_escaped() -> None:
    html = export_service.markdown_to_html("## <img src=x onerror=alert(1)>")

    assert "onerror=alert(1)>" not in html
    assert "&lt;img" in html


def test_bold_and_italic_work() -> None:
    html = export_service.markdown_to_html("Это **важно** и *интересно*")

    assert "<strong>важно</strong>" in html
    assert "<em>интересно</em>" in html


def test_links_get_safe_attributes() -> None:
    html = export_service.markdown_to_html("[Источник](https://example.ru/page)")

    assert 'href="https://example.ru/page"' in html
    assert 'rel="noopener noreferrer"' in html


def test_javascript_link_is_not_created() -> None:
    """Ссылка с javascript: не должна превратиться в кликабельный тег."""
    html = export_service.markdown_to_html("[Клик](javascript:alert(1))")

    assert "<a href" not in html


def test_unordered_list_is_built() -> None:
    html = export_service.markdown_to_html("- первый\n- второй")

    assert html.count("<li>") == 2
    assert "<ul>" in html and "</ul>" in html


def test_ordered_list_is_built() -> None:
    html = export_service.markdown_to_html("1. первый\n2. второй")

    assert "<ol>" in html and "</ol>" in html


def test_quote_is_converted() -> None:
    html = export_service.markdown_to_html("> Цитата из источника")

    assert "<blockquote>Цитата из источника</blockquote>" in html


def test_empty_markdown_gives_empty_html() -> None:
    assert export_service.markdown_to_html("") == ""


def test_plain_text_strips_markup() -> None:
    plain = export_service.markdown_to_plain("## Заголовок\n\n**Жирный** и [ссылка](https://a.ru)")

    assert "##" not in plain
    assert "**" not in plain
    assert "Заголовок" in plain
    assert "ссылка (https://a.ru)" in plain


def test_full_markdown_includes_title_and_cta() -> None:
    markdown = export_service.build_markdown(make_article())

    assert markdown.startswith("# Как жили города в 1900 году")
    assert "Подпишитесь на канал" in markdown


def test_full_html_page_is_valid() -> None:
    html = export_service.build_html(make_article())

    assert html.startswith("<!doctype html>")
    assert 'lang="ru"' in html
    assert "<h1>Как жили города в 1900 году</h1>" in html
    assert "DzenPilot" in html


def test_title_with_quotes_is_escaped_in_page() -> None:
    html = export_service.build_html(make_article(title='Статья "с кавычками" <b>'))

    assert "<b>" not in html.split("<style>")[0]
    assert "&lt;b&gt;" in html
