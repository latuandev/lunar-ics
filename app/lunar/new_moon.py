"""New moon calculations based on Meeus chapter 49."""

from __future__ import annotations

import math

from app.config import NEW_MOON_EPOCH_JDE
from app.lunar.astronomy import jd_tt_to_ut, sin_deg


def mean_new_moon_jde(k: float) -> float:
    """Return the mean Julian Ephemeris Day for lunation index k."""

    t = k / 1236.85
    return (
        NEW_MOON_EPOCH_JDE
        + 29.530588853 * k
        + 0.0001337 * (t**2)
        - 0.000000150 * (t**3)
        + 0.00000000073 * (t**4)
    )


def true_new_moon_jd_ut(k: int) -> float:
    """Return the Julian Day in UT for a true new moon."""

    t = k / 1236.85
    e = 1 - 0.002516 * t - 0.0000074 * (t**2)
    sun_anomaly = (
        2.5534
        + 29.10535669 * k
        - 0.0000218 * (t**2)
        - 0.00000011 * (t**3)
    )
    moon_anomaly = (
        201.5643
        + 385.81693528 * k
        + 0.0107438 * (t**2)
        + 0.00001239 * (t**3)
        - 0.000000058 * (t**4)
    )
    moon_argument = (
        160.7108
        + 390.67050284 * k
        - 0.0016341 * (t**2)
        - 0.00000227 * (t**3)
        + 0.000000011 * (t**4)
    )
    ascending_node = (
        124.7746
        - 1.56375580 * k
        + 0.0020691 * (t**2)
        + 0.00000215 * (t**3)
    )

    periodic = (
        -0.40720 * sin_deg(moon_anomaly)
        + 0.17241 * e * sin_deg(sun_anomaly)
        + 0.01608 * sin_deg(2 * moon_anomaly)
        + 0.01039 * sin_deg(2 * moon_argument)
        + 0.00739 * e * sin_deg(moon_anomaly - sun_anomaly)
        - 0.00514 * e * sin_deg(moon_anomaly + sun_anomaly)
        + 0.00208 * (e**2) * sin_deg(2 * sun_anomaly)
        - 0.00111 * sin_deg(moon_anomaly - 2 * moon_argument)
        - 0.00057 * sin_deg(moon_anomaly + 2 * moon_argument)
        + 0.00056 * e * sin_deg(2 * moon_anomaly + sun_anomaly)
        - 0.00042 * sin_deg(3 * moon_anomaly)
        + 0.00042 * e * sin_deg(sun_anomaly + 2 * moon_argument)
        + 0.00038 * e * sin_deg(sun_anomaly - 2 * moon_argument)
        - 0.00024 * e * sin_deg(2 * moon_anomaly - sun_anomaly)
        - 0.00017 * sin_deg(ascending_node)
        - 0.00007 * sin_deg(moon_anomaly + 2 * sun_anomaly)
        + 0.00004 * sin_deg(2 * moon_anomaly - 2 * moon_argument)
        + 0.00004 * sin_deg(3 * sun_anomaly)
        + 0.00003 * sin_deg(moon_anomaly + sun_anomaly - 2 * moon_argument)
        + 0.00003 * sin_deg(2 * moon_anomaly + 2 * moon_argument)
        - 0.00003 * sin_deg(moon_anomaly + sun_anomaly + 2 * moon_argument)
        + 0.00003 * sin_deg(moon_anomaly - sun_anomaly + 2 * moon_argument)
        - 0.00002 * sin_deg(moon_anomaly - sun_anomaly - 2 * moon_argument)
        - 0.00002 * sin_deg(3 * moon_anomaly + sun_anomaly)
        + 0.00002 * sin_deg(4 * moon_anomaly)
    )

    a1 = 299.77 + 0.107408 * k - 0.009173 * (t**2)
    a2 = 251.88 + 0.016321 * k
    a3 = 251.83 + 26.651886 * k
    a4 = 349.42 + 36.412478 * k
    a5 = 84.66 + 18.206239 * k
    a6 = 141.74 + 53.303771 * k
    a7 = 207.14 + 2.453732 * k
    a8 = 154.84 + 7.306860 * k
    a9 = 34.52 + 27.261239 * k
    a10 = 207.19 + 0.121824 * k
    a11 = 291.34 + 1.844379 * k
    a12 = 161.72 + 24.198154 * k
    a13 = 239.56 + 25.513099 * k
    a14 = 331.55 + 3.592518 * k
    planetary = (
        0.000325 * sin_deg(a1)
        + 0.000165 * sin_deg(a2)
        + 0.000164 * sin_deg(a3)
        + 0.000126 * sin_deg(a4)
        + 0.000110 * sin_deg(a5)
        + 0.000062 * sin_deg(a6)
        + 0.000060 * sin_deg(a7)
        + 0.000056 * sin_deg(a8)
        + 0.000047 * sin_deg(a9)
        + 0.000042 * sin_deg(a10)
        + 0.000040 * sin_deg(a11)
        + 0.000037 * sin_deg(a12)
        + 0.000035 * sin_deg(a13)
        + 0.000023 * sin_deg(a14)
    )

    jde = mean_new_moon_jde(k) + periodic + planetary
    return jd_tt_to_ut(jde)


def approximate_lunation_index(jd_ut: float) -> int:
    """Return the nearest integer lunation index for a Julian Day."""

    return int(math.floor((jd_ut - NEW_MOON_EPOCH_JDE) / 29.530588853))

