"""Vietnamese lunar calendar construction rules."""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta

from app.config import (
    ALGORITHM_VERSION,
    REFERENCE_LONGITUDE_DEGREES,
    SYNODIC_MONTH_DAYS,
    TIMEZONE_NAME,
)
from app.lunar.astronomy import gregorian_to_jd, jd_to_local_datetime
from app.lunar.models import DatasetBundle, DatasetMetadata, DayRecord, LunarMonth, NewMoon
from app.lunar.new_moon import approximate_lunation_index, true_new_moon_jd_ut
from app.lunar.solar_longitude import compute_principal_terms


def compute_new_moons(start_date: date, end_date: date) -> list[NewMoon]:
    """Compute new moon instants that cover the requested Gregorian span."""

    start_jd = gregorian_to_jd(start_date - timedelta(days=60))
    end_jd = gregorian_to_jd(end_date + timedelta(days=60))
    k_start = approximate_lunation_index(start_jd) - 2
    k_end = int(math.ceil((end_jd - 2451550.09765) / SYNODIC_MONTH_DAYS)) + 2

    new_moons: list[NewMoon] = []
    for index in range(k_start, k_end + 1):
        jd_ut = true_new_moon_jd_ut(index)
        local_datetime = jd_to_local_datetime(jd_ut)
        new_moons.append(NewMoon(index=index, jd_ut=jd_ut, local_datetime=local_datetime))
    new_moons.sort(key=lambda item: item.jd_ut)
    return new_moons


def build_month_skeleton(
    start_date: date,
    end_date: date,
) -> tuple[list[LunarMonth], dict[int, list[int]]]:
    """Build unlabeled lunar months and principal term indexes."""

    new_moons = compute_new_moons(start_date, end_date)
    principal_terms = compute_principal_terms(
        start_date=start_date - timedelta(days=120),
        end_date=end_date + timedelta(days=120),
    )

    term_indexes_by_month: dict[int, list[int]] = defaultdict(list)
    months: list[LunarMonth] = []

    term_cursor = 0
    for month_index in range(len(new_moons) - 1):
        start = new_moons[month_index]
        end = new_moons[month_index + 1]
        while (
            term_cursor < len(principal_terms)
            and principal_terms[term_cursor].jd_ut < start.jd_ut
        ):
            term_cursor += 1

        term = None
        if term_cursor < len(principal_terms):
            candidate = principal_terms[term_cursor]
            if start.jd_ut <= candidate.jd_ut < end.jd_ut:
                term = candidate
                term_indexes_by_month[month_index].append(term_cursor)

        month = LunarMonth(
            start_jd_ut=start.jd_ut,
            end_jd_ut=end.jd_ut,
            start_gregorian_date=start.local_date,
            end_gregorian_date=end.local_date - timedelta(days=1),
            month_length=(end.local_date - start.local_date).days,
            contains_principal_term=term is not None,
            principal_term=term,
        )
        months.append(month)

    return months, term_indexes_by_month


def identify_month_11_indices(
    months: list[LunarMonth],
    start_year: int,
    end_year: int,
) -> dict[int, int]:
    """Identify the lunar month containing the winter solstice of each year."""

    month11_indices: dict[int, int] = {}
    for year in range(start_year - 1, end_year + 2):
        for index, month in enumerate(months):
            term = month.principal_term
            if term and term.longitude_deg == 270 and term.local_datetime.year == year:
                month11_indices[year] = index
                month.is_month_11 = True
                break
        if year not in month11_indices:
            raise ValueError(f"Could not locate month 11 for Gregorian year {year}")
    return month11_indices


def assign_lunar_month_numbers(
    months: list[LunarMonth],
    start_year: int,
    end_year: int,
) -> None:
    """Assign lunar month numbers, leap flags, and lunar years."""

    month11_indices = identify_month_11_indices(months, start_year, end_year)

    for anchor_year in range(start_year - 1, end_year + 1):
        start_index = month11_indices[anchor_year]
        end_index = month11_indices[anchor_year + 1]
        span = months[start_index:end_index]
        span_length = len(span)
        if span_length not in (12, 13):
            raise ValueError(
                f"Unexpected lunar year span for {anchor_year}: {span_length} months"
            )

        current_number = 11
        leap_assigned = False
        first_month = span[0]
        first_month.lunar_month = 11
        first_month.lunar_year = anchor_year
        first_month.is_leap_month = False
        first_month.anchor_year = anchor_year

        for month in span[1:]:
            if span_length == 13 and not leap_assigned and not month.contains_principal_term:
                month.lunar_month = current_number
                month.is_leap_month = True
                leap_assigned = True
            else:
                current_number = 1 if current_number == 12 else current_number + 1
                month.lunar_month = current_number
                month.is_leap_month = False

            month.lunar_year = anchor_year if month.lunar_month >= 11 else anchor_year + 1
            month.anchor_year = anchor_year


def build_day_records(
    months: list[LunarMonth],
    start_date: date,
    end_date: date,
) -> list[DayRecord]:
    """Materialize day-level Gregorian to lunar mappings."""

    records: list[DayRecord] = []
    for month in months:
        cursor = month.start_gregorian_date
        while cursor <= month.end_gregorian_date:
            if start_date <= cursor <= end_date:
                lunar_day = (cursor - month.start_gregorian_date).days + 1
                principal_term = None
                principal_term_longitude = None
                principal_term_moment = None
                if month.principal_term and month.principal_term.local_date == cursor:
                    principal_term = month.principal_term.name
                    principal_term_longitude = month.principal_term.longitude_deg
                    principal_term_moment = month.principal_term.local_datetime.isoformat()

                records.append(
                    DayRecord(
                        gregorian_date=cursor,
                        lunar_day=lunar_day,
                        lunar_month=month.lunar_month,
                        lunar_year=month.lunar_year,
                        is_leap_month=month.is_leap_month,
                        lunar_month_length=month.month_length,
                        month_start_gregorian_date=month.start_gregorian_date,
                        month_end_gregorian_date=month.end_gregorian_date,
                        principal_term=principal_term,
                        principal_term_longitude_deg=principal_term_longitude,
                        principal_term_moment_local=principal_term_moment,
                    )
                )
            cursor += timedelta(days=1)
    return records


def build_dataset_bundle(from_year: int, to_year: int) -> DatasetBundle:
    """Build the full dataset bundle for a year span."""

    start_date = date(from_year, 1, 1)
    end_date = date(to_year, 12, 31)
    extended_start = date(from_year - 1, 1, 1)
    extended_end = date(to_year + 1, 12, 31)

    months, _ = build_month_skeleton(extended_start, extended_end)
    assign_lunar_month_numbers(months, from_year, to_year)
    records = build_day_records(months, start_date, end_date)
    metadata = DatasetMetadata(
        from_year=from_year,
        to_year=to_year,
        start_date=start_date,
        end_date=end_date,
        generated_at_utc=datetime.now(tz=UTC),
        timezone_name=TIMEZONE_NAME,
        reference_longitude_deg=REFERENCE_LONGITUDE_DEGREES,
        algorithm_version=ALGORITHM_VERSION,
    )
    filtered_months = [
        month
        for month in months
        if month.end_gregorian_date >= start_date and month.start_gregorian_date <= end_date
    ]
    bundle = DatasetBundle(metadata=metadata, months=filtered_months, records=records)
    bundle.build_indexes()
    return bundle
