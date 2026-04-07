"""Calendar feed helpers for rolling and fixed ICS exports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from threading import Lock
from typing import Callable

from app.config import TIMEZONE_NAME, resolve_zoneinfo
from app.lunar.models import DatasetBundle, DayRecord
from app.serializers.ics_export import write_ics_file
from app.types import JSONDict

DEFAULT_ROLLING_YEARS = 5
MIN_ROLLING_YEARS = 1
MAX_ROLLING_YEARS = 10


def get_current_vietnam_datetime(now: datetime | None = None) -> datetime:
    """Return the current Vietnam local datetime."""

    moment = now or datetime.now(tz=UTC)
    if moment.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    return moment.astimezone(resolve_zoneinfo())


def get_current_vietnam_year(now: datetime | None = None) -> int:
    """Return the current Gregorian year in Vietnam local time."""

    return get_current_vietnam_datetime(now).year


def validate_rolling_years(years: int) -> int:
    """Validate the rolling window size."""

    if years < MIN_ROLLING_YEARS or years > MAX_ROLLING_YEARS:
        raise ValueError(
            f"years must be between {MIN_ROLLING_YEARS} and {MAX_ROLLING_YEARS}"
        )
    return years


def get_rolling_year_window(
    now: datetime | None = None,
    *,
    years: int = DEFAULT_ROLLING_YEARS,
) -> tuple[int, int]:
    """Return the start and end year for a rolling Gregorian window."""

    validated_years = validate_rolling_years(years)
    start_year = get_current_vietnam_year(now)
    return start_year, start_year + validated_years - 1


def rolling_feed_filename(years: int = DEFAULT_ROLLING_YEARS) -> str:
    """Return the file name for a rolling ICS feed."""

    validated_years = validate_rolling_years(years)
    return f"vn_lunar_{validated_years}y.ics"


def rolling_feed_url(years: int = DEFAULT_ROLLING_YEARS) -> str:
    """Return the public URL for a rolling ICS feed."""

    validated_years = validate_rolling_years(years)
    if validated_years == DEFAULT_ROLLING_YEARS:
        return "/calendar/vn_lunar_5y.ics"
    return f"/calendar/rolling/{validated_years}.ics"


def rolling_calendar_name(years: int) -> str:
    """Return the calendar name displayed in rolling ICS feeds."""

    validated_years = validate_rolling_years(years)
    return f"Lịch âm Việt Nam rolling {validated_years} years"


@dataclass(frozen=True, slots=True)
class RollingWindow:
    """Metadata describing a rolling calendar feed window."""

    timezone: str
    current_local_date: date
    start_year: int
    end_year: int
    years: int
    feed_url: str

    def to_dict(self) -> JSONDict:
        """Serialize the rolling window for API responses."""

        return {
            "timezone": self.timezone,
            "current_local_date": self.current_local_date.isoformat(),
            "start_year": self.start_year,
            "end_year": self.end_year,
            "years": self.years,
            "feed_url": self.feed_url,
        }


class CalendarFeedService:
    """Manage rolling ICS feeds backed by the existing dataset bundle."""

    def __init__(
        self,
        *,
        bundle: DatasetBundle,
        data_dir: Path,
        now_provider: Callable[[], datetime] | None = None,
    ) -> None:
        self.bundle = bundle
        self.data_dir = data_dir
        self.now_provider = now_provider or (lambda: datetime.now(tz=UTC))
        self._lock = Lock()
        self._cached_start_years: dict[int, int] = {}

    def get_rolling_window(self, years: int = DEFAULT_ROLLING_YEARS) -> RollingWindow:
        """Return rolling window metadata for the given feed length."""

        local_now = get_current_vietnam_datetime(self.now_provider())
        start_year, end_year = get_rolling_year_window(local_now, years=years)
        return RollingWindow(
            timezone=TIMEZONE_NAME,
            current_local_date=local_now.date(),
            start_year=start_year,
            end_year=end_year,
            years=validate_rolling_years(years),
            feed_url=rolling_feed_url(years),
        )

    def build_calendar_dataset_for_year_range(
        self,
        start_year: int,
        end_year: int,
    ) -> list[DayRecord]:
        """Return records covering an inclusive Gregorian year range."""

        if start_year > end_year:
            raise ValueError("start_year must not be greater than end_year")
        if start_year < self.bundle.metadata.from_year or end_year > self.bundle.metadata.to_year:
            raise ValueError(
                f"Gregorian year range out of supported bounds: {start_year}..{end_year}"
            )
        return [
            record
            for record in self.bundle.records
            if start_year <= record.gregorian_date.year <= end_year
        ]

    def rolling_feed_path(self, years: int = DEFAULT_ROLLING_YEARS) -> Path:
        """Return the filesystem path for a rolling ICS feed."""

        return self.data_dir / "ics" / rolling_feed_filename(years)

    def export_rolling_ics(self, years: int = DEFAULT_ROLLING_YEARS) -> Path:
        """Write the rolling ICS feed for the current Vietnam-year window."""

        window = self.get_rolling_window(years)
        records = self.build_calendar_dataset_for_year_range(
            window.start_year,
            window.end_year,
        )
        output_path = self.rolling_feed_path(window.years)
        write_ics_file(
            output_path,
            records=records,
            metadata=self.bundle.metadata,
            calendar_name=rolling_calendar_name(window.years),
        )
        return output_path

    def ensure_rolling_ics(self, years: int = DEFAULT_ROLLING_YEARS) -> Path:
        """Return a rolling ICS path, regenerating only when the year window changes."""

        window = self.get_rolling_window(years)
        output_path = self.rolling_feed_path(window.years)
        with self._lock:
            cached_start_year = self._cached_start_years.get(window.years)
            if cached_start_year == window.start_year and output_path.exists():
                return output_path
            output_path = self.export_rolling_ics(window.years)
            self._cached_start_years[window.years] = window.start_year
            return output_path
