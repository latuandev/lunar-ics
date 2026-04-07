"""Date parsing and formatting helpers."""

from __future__ import annotations

from datetime import date, datetime

ISO_DATE = "%Y-%m-%d"


def parse_iso_date(value: str) -> date:
    """Parse an ISO-8601 calendar date."""

    return datetime.strptime(value, ISO_DATE).date()


def format_iso_date(value: date) -> str:
    """Format a date as YYYY-MM-DD."""

    return value.isoformat()

