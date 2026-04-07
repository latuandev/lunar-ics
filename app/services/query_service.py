"""Query and file-serving service layer."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Callable

from app.config import MAX_RANGE_DAYS
from app.lunar.converter import LunarConverter
from app.lunar.models import DatasetBundle, DayRecord
from app.services.calendar_feed_service import CalendarFeedService
from app.services.dataset_builder import DatasetBuilder


class QueryService:
    """In-memory query facade over the generated dataset."""

    def __init__(
        self,
        bundle: DatasetBundle,
        data_dir: Path,
        *,
        now_provider: Callable[[], datetime] | None = None,
    ) -> None:
        self.bundle = bundle
        self.data_dir = data_dir
        self.converter = LunarConverter(bundle)
        self.calendar_feed_service = CalendarFeedService(
            bundle=bundle,
            data_dir=data_dir,
            now_provider=now_provider,
        )

    @classmethod
    def load(
        cls,
        data_dir: Path,
        *,
        now_provider: Callable[[], datetime] | None = None,
    ) -> "QueryService":
        """Load the canonical dataset from disk."""

        builder = DatasetBuilder(data_dir)
        bundle = builder.load_bundle()
        return cls(bundle=bundle, data_dir=data_dir, now_provider=now_provider)

    def ensure_supported_date(self, value: date) -> None:
        """Validate that a Gregorian date is inside the supported range."""

        if not (self.bundle.metadata.start_date <= value <= self.bundle.metadata.end_date):
            raise ValueError(
                f"Gregorian date out of supported range: {value.isoformat()}"
            )

    def solar_to_lunar(self, value: date) -> DayRecord:
        """Lookup a Gregorian date."""

        self.ensure_supported_date(value)
        return self.converter.solar_to_lunar(value)

    def lunar_to_solar(
        self,
        *,
        lunar_year: int,
        lunar_month: int,
        lunar_day: int,
        is_leap_month: bool,
    ) -> DayRecord:
        """Lookup a lunar date."""

        if lunar_month < 1 or lunar_month > 12:
            raise ValueError("lunar month must be between 1 and 12")
        if lunar_day < 1 or lunar_day > 30:
            raise ValueError("lunar day must be between 1 and 30")
        return self.converter.lunar_to_solar(
            lunar_year=lunar_year,
            lunar_month=lunar_month,
            lunar_day=lunar_day,
            is_leap_month=is_leap_month,
        )

    def year_records(self, year: int) -> list[DayRecord]:
        """Return all records for a Gregorian year."""

        if year < self.bundle.metadata.from_year or year > self.bundle.metadata.to_year:
            raise ValueError(f"Gregorian year out of supported range: {year}")
        return [record for record in self.bundle.records if record.gregorian_date.year == year]

    def month_records(self, year: int, month: int) -> list[DayRecord]:
        """Return all records for a Gregorian month."""

        if month < 1 or month > 12:
            raise ValueError("Gregorian month must be between 1 and 12")
        return [
            record
            for record in self.year_records(year)
            if record.gregorian_date.month == month
        ]

    def range_records(self, start: date, end: date) -> list[DayRecord]:
        """Return all records in a Gregorian date interval."""

        if end < start:
            raise ValueError("end must not be earlier than start")
        if (end - start).days + 1 > MAX_RANGE_DAYS:
            raise ValueError(f"date range must not exceed {MAX_RANGE_DAYS} days")
        self.ensure_supported_date(start)
        self.ensure_supported_date(end)
        return [
            record
            for record in self.bundle.records
            if start <= record.gregorian_date <= end
        ]

    def resolve_download_path(self, relative_path: str) -> Path:
        """Resolve a safe path under the data directory."""

        normalized = Path(relative_path.lstrip("/"))
        if not normalized.parts:
            raise ValueError("filename is required")
        candidate = (self.data_dir / normalized).resolve()
        data_root = self.data_dir.resolve()
        if data_root not in candidate.parents and candidate != data_root:
            raise ValueError("invalid download path")
        if not candidate.exists() or not candidate.is_file():
            raise ValueError("requested file does not exist")
        return candidate
