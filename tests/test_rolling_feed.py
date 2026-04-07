"""Rolling calendar window and feed tests."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from app.services.calendar_feed_service import (
    CalendarFeedService,
    get_current_vietnam_year,
    get_rolling_year_window,
)


def test_current_year_uses_vietnam_timezone() -> None:
    assert get_current_vietnam_year(datetime(2026, 12, 31, 16, 30, tzinfo=UTC)) == 2026
    assert get_current_vietnam_year(datetime(2026, 12, 31, 17, 30, tzinfo=UTC)) == 2027


def test_rolling_window_examples() -> None:
    assert get_rolling_year_window(datetime(2026, 4, 7, 1, 0, tzinfo=UTC), years=5) == (
        2026,
        2030,
    )
    assert get_rolling_year_window(datetime(2026, 12, 31, 17, 1, tzinfo=UTC), years=5) == (
        2027,
        2031,
    )


def test_build_calendar_dataset_for_year_range(full_bundle, fixed_now, tmp_path: Path) -> None:
    service = CalendarFeedService(
        bundle=full_bundle,
        data_dir=tmp_path,
        now_provider=lambda: fixed_now,
    )
    window = service.get_rolling_window()
    assert (window.start_year, window.end_year) == (2026, 2030)
    records = service.build_calendar_dataset_for_year_range(window.start_year, window.end_year)
    assert len(records) == 1826

