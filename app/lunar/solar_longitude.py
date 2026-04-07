"""Solar longitude and principal term calculations."""

from __future__ import annotations

import math
from datetime import date, timedelta

from app.lunar.astronomy import (
    gregorian_to_jd,
    jd_to_local_datetime,
    jd_ut_to_tt,
    normalize_degrees,
    sin_deg,
)
from app.lunar.models import PrincipalTerm

PRINCIPAL_TERM_NAMES = {
    0: "Xuân phân",
    30: "Cốc vũ",
    60: "Tiểu mãn",
    90: "Hạ chí",
    120: "Đại thử",
    150: "Xử thử",
    180: "Thu phân",
    210: "Sương giáng",
    240: "Tiểu tuyết",
    270: "Đông chí",
    300: "Đại hàn",
    330: "Vũ thủy",
}


def apparent_solar_longitude_deg(jd_ut: float) -> float:
    """Return the Sun's apparent ecliptic longitude in degrees."""

    jd_tt = jd_ut_to_tt(jd_ut)
    t = (jd_tt - 2451545.0) / 36525.0
    mean_longitude = normalize_degrees(
        280.46646 + 36000.76983 * t + 0.0003032 * (t**2)
    )
    mean_anomaly = normalize_degrees(
        357.52911 + 35999.05029 * t - 0.0001537 * (t**2) + (t**3) / 24490000.0
    )
    equation_of_center = (
        (1.914602 - 0.004817 * t - 0.000014 * (t**2)) * sin_deg(mean_anomaly)
        + (0.019993 - 0.000101 * t) * sin_deg(2 * mean_anomaly)
        + 0.000289 * sin_deg(3 * mean_anomaly)
    )
    true_longitude = mean_longitude + equation_of_center
    omega = 125.04 - 1934.136 * t
    apparent = true_longitude - 0.00569 - 0.00478 * sin_deg(omega)
    return normalize_degrees(apparent)


def unwrap_angle(raw_angle: float, reference: float) -> float:
    """Unwrap an angle so it remains close to a reference angle."""

    value = raw_angle
    while value <= reference - 180.0:
        value += 360.0
    while value > reference + 180.0:
        value -= 360.0
    return value


def solar_longitude_unwrapped(jd_ut: float, reference: float) -> float:
    """Return a longitude value continuous around the provided reference."""

    return unwrap_angle(apparent_solar_longitude_deg(jd_ut), reference)


def solve_longitude_crossing(
    left_jd_ut: float,
    right_jd_ut: float,
    target_unwrapped_deg: float,
    reference_deg: float,
    tolerance_days: float = 1e-7,
) -> float:
    """Locate a principal term crossing using bisection."""

    left_value = solar_longitude_unwrapped(left_jd_ut, reference_deg) - target_unwrapped_deg
    right_value = solar_longitude_unwrapped(right_jd_ut, reference_deg) - target_unwrapped_deg
    if left_value > 0 or right_value < 0:
        raise ValueError("Invalid bracketing interval for solar longitude crossing")

    left = left_jd_ut
    right = right_jd_ut
    while right - left > tolerance_days:
        middle = (left + right) / 2.0
        middle_value = (
            solar_longitude_unwrapped(middle, reference_deg) - target_unwrapped_deg
        )
        if middle_value >= 0:
            right = middle
        else:
            left = middle
    return (left + right) / 2.0


def compute_principal_terms(start_date: date, end_date: date) -> list[PrincipalTerm]:
    """Compute principal solar terms between two Gregorian dates."""

    terms: list[PrincipalTerm] = []
    cursor_date = start_date
    current_jd = gregorian_to_jd(cursor_date)
    current_unwrapped = apparent_solar_longitude_deg(current_jd)
    current_sector = math.floor(current_unwrapped / 30.0)

    final_jd = gregorian_to_jd(end_date)
    while current_jd < final_jd:
        next_jd = current_jd + 1.0
        next_unwrapped = solar_longitude_unwrapped(next_jd, current_unwrapped)
        next_sector = math.floor(next_unwrapped / 30.0)

        if next_sector > current_sector:
            target_sector = current_sector + 1
            target_unwrapped = target_sector * 30.0
            crossing_jd = solve_longitude_crossing(
                current_jd,
                next_jd,
                target_unwrapped_deg=target_unwrapped,
                reference_deg=current_unwrapped,
            )
            longitude_deg = int(target_unwrapped % 360.0)
            terms.append(
                PrincipalTerm(
                    index=longitude_deg // 30,
                    longitude_deg=longitude_deg,
                    name=PRINCIPAL_TERM_NAMES[longitude_deg],
                    jd_ut=crossing_jd,
                    local_datetime=jd_to_local_datetime(crossing_jd),
                )
            )

        current_jd = next_jd
        current_unwrapped = next_unwrapped
        current_sector = next_sector
        cursor_date += timedelta(days=1)

    return terms

