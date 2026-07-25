"""Часовые пояса для календаря публикаций.

По умолчанию используется Москва (UTC+3). Выбранный пояс всегда показывается
рядом с датой публикации.
"""

from __future__ import annotations

from zoneinfo import available_timezones

DEFAULT_TIMEZONE = "Europe/Moscow"

# Основные пояса вынесены в начало списка — их выбирают чаще всего.
TIMEZONE_CHOICES: list[dict[str, str]] = [
    {"value": "Europe/Moscow", "label": "Москва, UTC+3", "offset": "+03:00"},
    {"value": "Europe/Kaliningrad", "label": "Калининград, UTC+2", "offset": "+02:00"},
    {"value": "Asia/Yekaterinburg", "label": "Екатеринбург, UTC+5", "offset": "+05:00"},
    {"value": "Asia/Novosibirsk", "label": "Новосибирск, UTC+7", "offset": "+07:00"},
    {"value": "Asia/Irkutsk", "label": "Иркутск, UTC+8", "offset": "+08:00"},
    {"value": "Asia/Irkutsk", "label": "Улан-Удэ, UTC+8", "offset": "+08:00"},
    {"value": "Asia/Vladivostok", "label": "Владивосток, UTC+10", "offset": "+10:00"},
    {"value": "Europe/Berlin", "label": "Берлин, UTC+1 или UTC+2 летом", "offset": "+01:00"},
]


def is_valid_timezone(name: str) -> bool:
    return name in available_timezones()


def all_timezones() -> list[str]:
    """Полный список поясов — для пункта «выбрать любой другой»."""
    return sorted(available_timezones())
