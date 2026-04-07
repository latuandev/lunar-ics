"""Dataset invariant tests."""

from __future__ import annotations

from collections import defaultdict

from app.lunar.validators import validate_bundle


def test_bundle_validates_exhaustively(full_bundle) -> None:
    report = validate_bundle(full_bundle)
    report.assert_valid()


def test_each_lunar_month_is_29_or_30_days(full_bundle) -> None:
    assert {month.month_length for month in full_bundle.months}.issubset({29, 30})


def test_complete_anchor_years_follow_month_11_and_leap_rules(full_bundle) -> None:
    spans = defaultdict(list)
    for month in full_bundle.months:
        spans[month.anchor_year].append(month)

    checked = 0
    for anchor_year, months in sorted(spans.items()):
        if not months or months[0].lunar_month != 11 or len(months) not in (12, 13):
            continue
        checked += 1
        assert months[0].principal_term is not None
        assert months[0].principal_term.longitude_deg == 270
        leap_months = [month for month in months if month.is_leap_month]
        if len(months) == 13:
            assert len(leap_months) == 1
            assert leap_months[0].contains_principal_term is False
        else:
            assert not leap_months

    assert checked >= 100


def test_lunar_day_progression_is_continuous(full_bundle) -> None:
    for current, following in zip(full_bundle.records, full_bundle.records[1:]):
        if current.lunar_day < current.lunar_month_length:
            assert following.lunar_day == current.lunar_day + 1
        else:
            assert following.lunar_day == 1

