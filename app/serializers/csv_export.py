"""CSV export helpers."""

from __future__ import annotations

import csv
from pathlib import Path

from app.lunar.models import DayRecord

CSV_COLUMNS = [
    "gregorian_date",
    "lunar_day",
    "lunar_month",
    "lunar_year",
    "is_leap_month",
    "lunar_month_length",
    "month_start_gregorian_date",
    "month_end_gregorian_date",
    "principal_term",
    "principal_term_longitude_deg",
    "principal_term_moment_local",
]


def write_csv_file(path: Path, records: list[DayRecord]) -> None:
    """Write a CSV export for day records."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for record in records:
            writer.writerow(record.to_dict())

