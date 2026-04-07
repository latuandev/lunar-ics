"""Astronomical primitives used by the lunar calendar engine."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from app.config import resolve_zoneinfo

JULIAN_DAY_UNIX_EPOCH = 2440587.5
SECONDS_PER_DAY = 86400.0


def normalize_degrees(value: float) -> float:
    """Wrap an angle to the [0, 360) interval."""

    return value % 360.0


def sin_deg(value: float) -> float:
    """Return sine for an angle in degrees."""

    return math.sin(math.radians(value))


def cos_deg(value: float) -> float:
    """Return cosine for an angle in degrees."""

    return math.cos(math.radians(value))


def gregorian_to_jd(value: date) -> float:
    """Return the Julian Day for 00:00 UTC of a Gregorian date."""

    year = value.year
    month = value.month
    day = value.day

    if month <= 2:
        year -= 1
        month += 12

    century = year // 100
    correction = 2 - century + century // 4
    jd = (
        math.floor(365.25 * (year + 4716))
        + math.floor(30.6001 * (month + 1))
        + day
        + correction
        - 1524.5
    )
    return jd


def datetime_to_jd(value: datetime) -> float:
    """Convert an aware datetime to Julian Day in UTC."""

    if value.tzinfo is None:
        raise ValueError("datetime_to_jd requires a timezone-aware datetime")
    utc_value = value.astimezone(UTC)
    unix_seconds = utc_value.timestamp()
    return JULIAN_DAY_UNIX_EPOCH + unix_seconds / SECONDS_PER_DAY


def jd_to_datetime_utc(jd_ut: float) -> datetime:
    """Convert a Julian Day in UT to a timezone-aware UTC datetime."""

    unix_seconds = (jd_ut - JULIAN_DAY_UNIX_EPOCH) * SECONDS_PER_DAY
    return datetime.fromtimestamp(unix_seconds, tz=UTC)


def jd_to_local_datetime(jd_ut: float) -> datetime:
    """Convert a Julian Day in UT to Vietnam local time."""

    timezone_obj = resolve_zoneinfo()
    return jd_to_datetime_utc(jd_ut).astimezone(timezone_obj)


def local_date_from_jd(jd_ut: float) -> date:
    """Return the Vietnam local civil date for a Julian Day in UT."""

    return jd_to_local_datetime(jd_ut).date()


def decimal_year_from_jd(jd_ut: float) -> float:
    """Return a decimal Gregorian year approximation for Delta T."""

    moment = jd_to_datetime_utc(jd_ut)
    year_start = datetime(moment.year, 1, 1, tzinfo=UTC)
    next_year_start = datetime(moment.year + 1, 1, 1, tzinfo=UTC)
    span = (next_year_start - year_start).total_seconds()
    offset = (moment - year_start).total_seconds()
    return moment.year + (offset / span)


def delta_t_seconds(jd_ut: float) -> float:
    """Approximate Delta T in seconds using Espenak-Meeus polynomials."""

    year = decimal_year_from_jd(jd_ut)
    if 1986 <= year < 2005:
        t = year - 2000.0
        return (
            63.86
            + 0.3345 * t
            - 0.060374 * (t**2)
            + 0.0017275 * (t**3)
            + 0.000651814 * (t**4)
            + 0.00002373599 * (t**5)
        )
    if year < 2050:
        t = year - 2000.0
        return 62.92 + 0.32217 * t + 0.005589 * (t**2)
    t = (year - 1820.0) / 100.0
    return -20.0 + 32.0 * (t**2) - 0.5628 * (2150.0 - year)


def jd_ut_to_tt(jd_ut: float) -> float:
    """Convert Julian Day in UT to Terrestrial Time."""

    return jd_ut + delta_t_seconds(jd_ut) / SECONDS_PER_DAY


def jd_tt_to_ut(jd_tt: float) -> float:
    """Approximate UT from a Julian Day in TT."""

    estimate = jd_tt
    for _ in range(3):
        estimate = jd_tt - delta_t_seconds(estimate) / SECONDS_PER_DAY
    return estimate


def next_date(value: date, days: int = 1) -> date:
    """Add whole civil days to a date."""

    return value + timedelta(days=days)


@dataclass(slots=True)
class Interval:
    """A closed-open Julian Day interval."""

    start_jd_ut: float
    end_jd_ut: float

    def contains(self, jd_ut: float) -> bool:
        """Return whether the interval contains the provided instant."""

        return self.start_jd_ut <= jd_ut < self.end_jd_ut

