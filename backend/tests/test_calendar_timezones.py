"""Тесты часовых поясов календаря.

Момент времени хранится в UTC, а пояс — отдельно. Проверяем, что перевод
туда и обратно не теряет время и что вид периода считается верно.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

from app.services import calendar_service
from app.services.timezones import is_valid_timezone


def test_moscow_is_three_hours_ahead_of_utc() -> None:
    moment = calendar_service.to_utc("2026-08-01T10:00", "Europe/Moscow")

    assert moment.tzinfo is not None
    assert moment.astimezone(UTC).hour == 7
    assert moment.astimezone(UTC).date() == date(2026, 8, 1)


def test_vladivostok_crosses_the_date_line_backwards() -> None:
    """Полночь во Владивостоке — это ещё предыдущий день по UTC."""
    moment = calendar_service.to_utc("2026-08-02T01:00", "Asia/Vladivostok")
    as_utc = moment.astimezone(UTC)

    assert as_utc.date() == date(2026, 8, 1)
    assert as_utc.hour == 15


def test_roundtrip_keeps_local_time() -> None:
    for zone in ("Europe/Moscow", "Asia/Irkutsk", "Europe/Kaliningrad", "Europe/Berlin"):
        moment = calendar_service.to_utc("2026-03-15T18:30", zone)
        local = calendar_service.to_local(moment, zone)

        assert local.strftime("%Y-%m-%dT%H:%M") == "2026-03-15T18:30"


def test_same_instant_shows_different_local_time() -> None:
    moment = datetime(2026, 8, 1, 7, 0, tzinfo=UTC)

    moscow = calendar_service.to_local(moment, "Europe/Moscow")
    irkutsk = calendar_service.to_local(moment, "Asia/Irkutsk")

    assert moscow.hour == 10
    assert irkutsk.hour == 15


def test_berlin_summer_time_is_handled() -> None:
    """Летом Берлин на два часа впереди UTC, зимой — на один."""
    summer = calendar_service.to_utc("2026-07-01T12:00", "Europe/Berlin").astimezone(UTC)
    winter = calendar_service.to_utc("2026-01-01T12:00", "Europe/Berlin").astimezone(UTC)

    assert summer.hour == 10
    assert winter.hour == 11


def test_day_period_is_single_day() -> None:
    start, end = calendar_service.period_bounds("day", date(2026, 8, 5))

    assert start == end == date(2026, 8, 5)


def test_week_starts_on_monday() -> None:
    # 5 августа 2026 года — среда
    start, end = calendar_service.period_bounds("week", date(2026, 8, 5))

    assert start == date(2026, 8, 3)
    assert end == date(2026, 8, 9)
    assert start.weekday() == 0


def test_month_covers_whole_month() -> None:
    start, end = calendar_service.period_bounds("month", date(2026, 2, 14))

    assert start == date(2026, 2, 1)
    assert end == date(2026, 2, 28)


def test_list_view_covers_next_ninety_days() -> None:
    start, end = calendar_service.period_bounds("list", date(2026, 8, 1))

    assert start == date(2026, 8, 1)
    assert (end - start).days == 90


def test_default_timezone_is_moscow() -> None:
    from app.services.timezones import DEFAULT_TIMEZONE

    assert DEFAULT_TIMEZONE == "Europe/Moscow"
    assert is_valid_timezone(DEFAULT_TIMEZONE)


def test_required_timezones_are_available() -> None:
    """Все пояса из задания должны существовать в системе."""
    for zone in (
        "Europe/Moscow",
        "Asia/Irkutsk",
        "Europe/Kaliningrad",
        "Asia/Yekaterinburg",
        "Asia/Novosibirsk",
        "Asia/Vladivostok",
        "Europe/Berlin",
    ):
        assert is_valid_timezone(zone), f"Пояс {zone} недоступен"


def test_timezone_label_is_russian() -> None:
    assert calendar_service.timezone_label("Europe/Moscow") == "Москва, UTC+3"
    # Неизвестный пояс возвращается как есть, без ошибки
    assert calendar_service.timezone_label("Africa/Cairo") == "Africa/Cairo"
