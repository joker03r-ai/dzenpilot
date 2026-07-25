"""Тесты периодов аналитики и вспомогательных расчётов."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.core.errors import ValidationAppError
from app.services import analytics_service


def test_seven_day_period_covers_seven_days() -> None:
    start, end = analytics_service.resolve_period("7d", None, None)

    assert end == date.today()
    assert (end - start).days == 6  # включая сегодня получается семь дней


def test_thirty_and_ninety_day_periods() -> None:
    start30, end30 = analytics_service.resolve_period("30d", None, None)
    start90, end90 = analytics_service.resolve_period("90d", None, None)

    assert (end30 - start30).days == 29
    assert (end90 - start90).days == 89


def test_custom_period_is_used_as_is() -> None:
    start, end = analytics_service.resolve_period(
        "custom", date(2026, 1, 1), date(2026, 3, 31)
    )

    assert start == date(2026, 1, 1)
    assert end == date(2026, 3, 31)


def test_custom_period_requires_both_dates() -> None:
    with pytest.raises(ValidationAppError) as error:
        analytics_service.resolve_period("custom", date(2026, 1, 1), None)

    assert "обе даты" in str(error.value)


def test_custom_period_rejects_reversed_dates() -> None:
    with pytest.raises(ValidationAppError) as error:
        analytics_service.resolve_period("custom", date(2026, 5, 1), date(2026, 4, 1))

    assert "позже конечной" in str(error.value)


def test_missing_value_is_marked_unavailable() -> None:
    metric = analytics_service._metric(None)

    assert metric.available is False
    assert metric.value is None
    assert metric.note == "Данные недоступны"


def test_zero_is_a_real_value_not_missing() -> None:
    """Ноль — это результат, а не отсутствие данных."""
    metric = analytics_service._metric(0)

    assert metric.available is True
    assert metric.value == 0


def test_change_percent_is_calculated() -> None:
    metric = analytics_service._metric(150, 100)

    assert metric.change_percent == 50.0


def test_change_is_none_without_previous_value() -> None:
    assert analytics_service._metric(150, None).change_percent is None
    assert analytics_service._metric(150, 0).change_percent is None


def test_negative_change_is_reported() -> None:
    metric = analytics_service._metric(80, 100)

    assert metric.change_percent == -20.0


def test_weekday_labels_are_russian_and_start_with_monday() -> None:
    assert analytics_service.WEEKDAY_LABELS[0] == "Понедельник"
    assert analytics_service.WEEKDAY_LABELS[6] == "Воскресенье"
    assert len(analytics_service.WEEKDAY_LABELS) == 7


def test_date_parsing_supports_russian_format() -> None:
    assert analytics_service._parse_date("15.03.2026") == date(2026, 3, 15)
    assert analytics_service._parse_date("2026-03-15") == date(2026, 3, 15)
    assert analytics_service._parse_date("не дата") is None
    assert analytics_service._parse_date(None) is None


def test_int_parsing_ignores_separators() -> None:
    assert analytics_service._parse_int("12 500") == 12500
    assert analytics_service._parse_int("1,200") == 1200
    assert analytics_service._parse_int("") is None
    assert analytics_service._parse_int("нет") is None


def test_csv_columns_are_matched_by_russian_names() -> None:
    assert analytics_service._match_column("Дата") == "captured_for"
    assert analytics_service._match_column("Просмотры") == "views"
    assert analytics_service._match_column("подписчики") == "subscribers"
    assert analytics_service._match_column("Неизвестная") is None


def test_period_days_mapping_matches_spec() -> None:
    from app.schemas.analytics import PERIOD_DAYS

    assert PERIOD_DAYS == {"7d": 7, "30d": 30, "90d": 90}


def test_yesterday_is_inside_thirty_day_period() -> None:
    start, end = analytics_service.resolve_period("30d", None, None)
    yesterday = date.today() - timedelta(days=1)

    assert start <= yesterday <= end
