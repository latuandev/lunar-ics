"""Dataclasses shared across the lunar calendar engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any


@dataclass(slots=True)
class PrincipalTerm:
    """A principal solar term event."""

    index: int
    longitude_deg: int
    name: str
    jd_ut: float
    local_datetime: datetime

    @property
    def local_date(self) -> date:
        """Return the local civil date of the event."""

        return self.local_datetime.date()

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-friendly data."""

        return {
            "index": self.index,
            "longitude_deg": self.longitude_deg,
            "name": self.name,
            "jd_ut": round(self.jd_ut, 8),
            "local_datetime": self.local_datetime.isoformat(),
            "local_date": self.local_date.isoformat(),
        }


@dataclass(slots=True)
class NewMoon:
    """A new moon event used to bound lunar months."""

    index: int
    jd_ut: float
    local_datetime: datetime

    @property
    def local_date(self) -> date:
        """Return the local civil date containing the conjunction."""

        return self.local_datetime.date()


@dataclass(slots=True)
class LunarMonth:
    """A Vietnamese lunar month."""

    start_jd_ut: float
    end_jd_ut: float
    start_gregorian_date: date
    end_gregorian_date: date
    month_length: int
    lunar_month: int = 0
    lunar_year: int = 0
    is_leap_month: bool = False
    contains_principal_term: bool = False
    principal_term: PrincipalTerm | None = None
    is_month_11: bool = False
    anchor_year: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize month metadata to JSON-friendly data."""

        return {
            "start_jd_ut": round(self.start_jd_ut, 8),
            "end_jd_ut": round(self.end_jd_ut, 8),
            "start_gregorian_date": self.start_gregorian_date.isoformat(),
            "end_gregorian_date": self.end_gregorian_date.isoformat(),
            "month_length": self.month_length,
            "lunar_month": self.lunar_month,
            "lunar_year": self.lunar_year,
            "is_leap_month": self.is_leap_month,
            "contains_principal_term": self.contains_principal_term,
            "principal_term": self.principal_term.to_dict() if self.principal_term else None,
            "is_month_11": self.is_month_11,
            "anchor_year": self.anchor_year,
        }


@dataclass(slots=True)
class DayRecord:
    """A fully materialized mapping between Gregorian and lunar dates."""

    gregorian_date: date
    lunar_day: int
    lunar_month: int
    lunar_year: int
    is_leap_month: bool
    lunar_month_length: int
    month_start_gregorian_date: date
    month_end_gregorian_date: date
    principal_term: str | None = None
    principal_term_longitude_deg: int | None = None
    principal_term_moment_local: str | None = None

    def lunar_key(self) -> tuple[int, int, int, bool]:
        """Return the unique lunar identity for reverse lookup."""

        return (
            self.lunar_year,
            self.lunar_month,
            self.lunar_day,
            self.is_leap_month,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-friendly data."""

        return {
            "gregorian_date": self.gregorian_date.isoformat(),
            "lunar_day": self.lunar_day,
            "lunar_month": self.lunar_month,
            "lunar_year": self.lunar_year,
            "is_leap_month": self.is_leap_month,
            "lunar_month_length": self.lunar_month_length,
            "month_start_gregorian_date": self.month_start_gregorian_date.isoformat(),
            "month_end_gregorian_date": self.month_end_gregorian_date.isoformat(),
            "principal_term": self.principal_term,
            "principal_term_longitude_deg": self.principal_term_longitude_deg,
            "principal_term_moment_local": self.principal_term_moment_local,
        }


@dataclass(slots=True)
class DatasetMetadata:
    """Metadata attached to a generated dataset."""

    from_year: int
    to_year: int
    start_date: date
    end_date: date
    generated_at_utc: datetime
    timezone_name: str
    reference_longitude_deg: float
    algorithm_version: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-friendly data."""

        return {
            "from_year": self.from_year,
            "to_year": self.to_year,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "generated_at_utc": self.generated_at_utc.isoformat(),
            "timezone_name": self.timezone_name,
            "reference_longitude_deg": self.reference_longitude_deg,
            "algorithm_version": self.algorithm_version,
        }


@dataclass(slots=True)
class DatasetBundle:
    """A generated calendar dataset with month metadata."""

    metadata: DatasetMetadata
    months: list[LunarMonth]
    records: list[DayRecord]
    solar_index: dict[date, DayRecord] = field(default_factory=dict)
    lunar_index: dict[tuple[int, int, int, bool], DayRecord] = field(default_factory=dict)

    def build_indexes(self) -> None:
        """Populate in-memory lookup indexes."""

        self.solar_index = {record.gregorian_date: record for record in self.records}
        self.lunar_index = {record.lunar_key(): record for record in self.records}

    def to_dict(self) -> dict[str, Any]:
        """Serialize the full bundle."""

        return {
            "metadata": self.metadata.to_dict(),
            "months": [month.to_dict() for month in self.months],
            "records": [record.to_dict() for record in self.records],
        }
