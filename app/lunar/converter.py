"""High-level date conversion helpers."""

from __future__ import annotations

from bisect import bisect_right
from datetime import date

from app.lunar.models import DatasetBundle, DayRecord


class LunarConverter:
    """Convert between Gregorian and Vietnamese lunar dates."""

    def __init__(self, bundle: DatasetBundle) -> None:
        self.bundle = bundle
        self._month_starts = [month.start_gregorian_date for month in bundle.months]

    def solar_to_lunar(self, value: date) -> DayRecord:
        """Convert a Gregorian date to a lunar day record."""

        try:
            return self.bundle.solar_index[value]
        except KeyError as exc:
            raise ValueError(f"Gregorian date out of range: {value.isoformat()}") from exc

    def lunar_to_solar(
        self,
        *,
        lunar_year: int,
        lunar_month: int,
        lunar_day: int,
        is_leap_month: bool,
    ) -> DayRecord:
        """Convert a lunar date to its Gregorian representation."""

        key = (lunar_year, lunar_month, lunar_day, is_leap_month)
        try:
            return self.bundle.lunar_index[key]
        except KeyError as exc:
            raise ValueError(
                "Invalid lunar date: "
                f"year={lunar_year}, month={lunar_month}, day={lunar_day}, leap={is_leap_month}"
            ) from exc

    def month_for_gregorian_date(self, value: date):
        """Return the lunar month metadata that contains a Gregorian date."""

        position = bisect_right(self._month_starts, value) - 1
        if position < 0:
            raise ValueError(f"Gregorian date out of range: {value.isoformat()}")
        month = self.bundle.months[position]
        if month.start_gregorian_date <= value <= month.end_gregorian_date:
            return month
        raise ValueError(f"Gregorian date out of range: {value.isoformat()}")

