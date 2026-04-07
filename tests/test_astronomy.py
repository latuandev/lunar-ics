"""Astronomy unit tests."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from app.lunar.astronomy import (
    datetime_to_jd,
    gregorian_to_jd,
    jd_to_datetime_utc,
    jd_to_local_datetime,
)
from app.lunar.new_moon import approximate_lunation_index, true_new_moon_jd_ut
from app.lunar.solar_longitude import apparent_solar_longitude_deg, compute_principal_terms


def test_gregorian_to_julian_day_epoch() -> None:
    assert gregorian_to_jd(date(2000, 1, 1)) == pytest.approx(2451544.5)
    noon = datetime(2000, 1, 1, 12, 0, tzinfo=UTC)
    assert datetime_to_jd(noon) == pytest.approx(2451545.0)
    assert jd_to_datetime_utc(2451545.0) == noon


def test_new_moon_february_2024_accuracy() -> None:
    target = datetime(2024, 2, 10, tzinfo=UTC)
    k = approximate_lunation_index(datetime_to_jd(target))
    candidates = [true_new_moon_jd_ut(index) for index in range(k - 2, k + 3)]
    best = min(candidates, key=lambda item: abs(item - datetime_to_jd(target)))
    best_dt = jd_to_datetime_utc(best)
    expected = datetime(2024, 2, 9, 22, 59, tzinfo=UTC)
    assert abs((best_dt - expected).total_seconds()) < 3600
    assert jd_to_local_datetime(best).date() == date(2024, 2, 10)


def test_solar_longitude_and_principal_term() -> None:
    equinox = datetime(2024, 3, 20, 3, 6, tzinfo=UTC)
    assert apparent_solar_longitude_deg(datetime_to_jd(equinox)) == pytest.approx(
        0.0, abs=0.1
    )
    terms = compute_principal_terms(date(2024, 3, 1), date(2024, 4, 1))
    assert any(term.longitude_deg == 0 and term.local_date == date(2024, 3, 20) for term in terms)


def test_timezone_boundary_uses_vietnam_date() -> None:
    jd_ut = true_new_moon_jd_ut(298)
    assert jd_to_datetime_utc(jd_ut).date() == date(2024, 2, 9)
    assert jd_to_local_datetime(jd_ut).date() == date(2024, 2, 10)

