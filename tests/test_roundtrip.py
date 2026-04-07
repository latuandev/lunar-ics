"""Exhaustive round-trip tests."""

from __future__ import annotations

from app.lunar.validators import ValidationReport, validate_round_trip


def test_full_range_record_count(full_bundle) -> None:
    assert len(full_bundle.records) == 36890
    assert full_bundle.records[0].gregorian_date.isoformat() == "2000-01-01"
    assert full_bundle.records[-1].gregorian_date.isoformat() == "2100-12-31"


def test_exhaustive_round_trip(full_bundle) -> None:
    report = ValidationReport()
    validate_round_trip(full_bundle, report)
    report.assert_valid()


def test_lunar_index_is_bijective(full_bundle) -> None:
    assert len(full_bundle.lunar_index) == len(full_bundle.records)
    assert len(full_bundle.solar_index) == len(full_bundle.records)

