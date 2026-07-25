"""Подготовка статьи к публикации: Markdown, HTML и простой текст.

Собственный конвертер вместо библиотеки выбран сознательно: нужен небольшой
и предсказуемый набор разметки, а главное — обязательное экранирование всего,
что пришло от пользователя или модели. Так в готовый HTML не попадёт
исполняемый код.
"""

from __future__ import annotations

import html
import re
from datetime import UTC, datetime

from app.models.article import Article

# Что именно поддерживается: заголовки, списки, выделение, ссылки, цитаты.
HEADING = re.compile(r"^(#{2,4})\s+(.+)$")
UNORDERED = re.compile(r"^[-*+]\s+(.+)$")
ORDERED = re.compile(r"^\d+[.)]\s+(.+)$")
QUOTE = re.compile(r"^>\s?(.*)$")
BOLD = re.compile(r"\*\*(.+?)\*\*")
ITALIC = re.compile(r"(?<!\*)\*([^*]+?)\*(?!\*)")
LINK = re.compile(r"\[([^\]]+)\]\((https?://[^\s)]+)\)")


def _inline(text: str) -> str:
    """Экранирует текст и затем возвращает разрешённую разметку."""
    escaped = html.escape(text, quote=True)

    escaped = LINK.sub(
        lambda match: (
            f'<a href="{match.group(2)}" target="_blank" rel="noopener noreferrer">'
            f"{match.group(1)}</a>"
        ),
        escaped,
    )
    escaped = BOLD.sub(r"<strong>\1</strong>", escaped)
    escaped = ITALIC.sub(r"<em>\1</em>", escaped)
    return escaped


def markdown_to_html(markdown: str) -> str:
    """Переводит поддерживаемую разметку в безопасный HTML."""
    if not markdown:
        return ""

    lines = markdown.replace("\r\n", "\n").split("\n")
    parts: list[str] = []
    list_type: str | None = None
    paragraph: list[str] = []

    def close_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            parts.append(f"<p>{' '.join(paragraph)}</p>")
            paragraph = []

    def close_list() -> None:
        nonlocal list_type
        if list_type:
            parts.append(f"</{list_type}>")
            list_type = None

    for raw in lines:
        line = raw.rstrip()

        if not line.strip():
            close_paragraph()
            close_list()
            continue

        heading = HEADING.match(line)
        if heading:
            close_paragraph()
            close_list()
            level = len(heading.group(1))
            parts.append(f"<h{level}>{_inline(heading.group(2))}</h{level}>")
            continue

        quote = QUOTE.match(line)
        if quote:
            close_paragraph()
            close_list()
            parts.append(f"<blockquote>{_inline(quote.group(1))}</blockquote>")
            continue

        unordered = UNORDERED.match(line)
        if unordered:
            close_paragraph()
            if list_type != "ul":
                close_list()
                parts.append("<ul>")
                list_type = "ul"
            parts.append(f"<li>{_inline(unordered.group(1))}</li>")
            continue

        ordered = ORDERED.match(line)
        if ordered:
            close_paragraph()
            if list_type != "ol":
                close_list()
                parts.append("<ol>")
                list_type = "ol"
            parts.append(f"<li>{_inline(ordered.group(1))}</li>")
            continue

        close_list()
        paragraph.append(_inline(line.strip()))

    close_paragraph()
    close_list()
    return "\n".join(parts)


def markdown_to_plain(markdown: str) -> str:
    """Текст без разметки — для копирования в редактор Дзена."""
    if not markdown:
        return ""

    lines: list[str] = []
    for raw in markdown.replace("\r\n", "\n").split("\n"):
        line = raw.rstrip()
        line = HEADING.sub(r"\2", line)
        line = UNORDERED.sub(r"• \1", line)
        line = QUOTE.sub(r"\1", line)
        line = LINK.sub(r"\1 (\2)", line)
        line = BOLD.sub(r"\1", line)
        line = ITALIC.sub(r"\1", line)
        lines.append(line)

    return "\n".join(lines).strip()


def build_markdown(article: Article) -> str:
    """Полный файл Markdown вместе с заголовком и вступлением."""
    parts = [f"# {article.title}", ""]
    if article.lead:
        parts += [article.lead.strip(), ""]
    if article.body_markdown:
        parts += [article.body_markdown.strip(), ""]
    if article.cta:
        parts += ["---", "", article.cta.strip(), ""]
    return "\n".join(parts)


def build_html(article: Article) -> str:
    """Готовая HTML-страница со статьёй."""
    title = html.escape(article.title, quote=True)
    lead = f"<p class=\"lead\">{_inline(article.lead)}</p>" if article.lead else ""
    body = markdown_to_html(article.body_markdown or "")
    cta = f"<p class=\"cta\">{_inline(article.cta)}</p>" if article.cta else ""
    generated = datetime.now(UTC).strftime("%d.%m.%Y")

    return f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  body {{ max-width: 720px; margin: 0 auto; padding: 24px;
         font: 17px/1.65 -apple-system, "Segoe UI", Roboto, sans-serif; color: #1a1d26; }}
  h1 {{ font-size: 30px; line-height: 1.25; }}
  h2 {{ font-size: 23px; margin-top: 32px; }}
  h3 {{ font-size: 19px; margin-top: 24px; }}
  p {{ margin: 14px 0; }}
  .lead {{ font-size: 19px; color: #444a58; }}
  .cta {{ margin-top: 32px; padding: 16px; background: #f2f4f9; border-radius: 12px; }}
  blockquote {{ margin: 16px 0; padding-left: 16px; border-left: 3px solid #d6dae5; color: #4a5060; }}
  a {{ color: #3d4bc7; }}
  footer {{ margin-top: 48px; font-size: 13px; color: #8a90a0; }}
</style>
</head>
<body>
<article>
<h1>{title}</h1>
{lead}
{body}
{cta}
</article>
<footer>Подготовлено в DzenPilot, {generated}. Перед публикацией проверьте факты и ссылки.</footer>
</body>
</html>
"""


def build_plain(article: Article) -> str:
    """Отформатированный текст для копирования вручную."""
    parts = [article.title, ""]
    if article.lead:
        parts += [article.lead.strip(), ""]
    parts.append(markdown_to_plain(article.body_markdown or ""))
    if article.cta:
        parts += ["", article.cta.strip()]
    return "\n".join(parts).strip()
