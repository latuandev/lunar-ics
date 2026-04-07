"""Regression tests for well-known Vietnamese lunar dates."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path


def test_known_cases(full_bundle) -> None:
    fixture_path = Path(__file__).parent / "fixtures" / "known_cases.json"
    cases = json.loads(fixture_path.read_text(encoding="utf-8"))
    for case in cases:
        record = full_bundle.solar_index[date.fromisoformat(case["gregorian_date"])]
        assert record.lunar_day == case["lunar_day"]
        assert record.lunar_month == case["lunar_month"]
        assert record.lunar_year == case["lunar_year"]
        assert record.is_leap_month is case["is_leap_month"]
