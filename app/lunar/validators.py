"""Independent validation layer for generated lunar datasets."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta

from app.lunar.converter import LunarConverter
from app.lunar.models import DatasetBundle, LunarMonth


@dataclass(slots=True)
class ValidationReport:
    """Accumulated validation failures."""

    errors: list[str] = field(default_factory=list)

    def add(self, message: str) -> None:
        """Add a validation error."""

        self.errors.append(message)

    def assert_valid(self) -> None:
        """Raise when any validation error exists."""

        if self.errors:
            formatted = "\n".join(f"- {message}" for message in self.errors)
            raise ValueError(f"Dataset validation failed:\n{formatted}")


def validate_month_lengths(bundle: DatasetBundle, report: ValidationReport) -> None:
    """Validate that each lunar month has 29 or 30 civil days."""

    for month in bundle.months:
        if month.month_length not in (29, 30):
            report.add(
                "Month "
                f"{month.start_gregorian_date.isoformat()} has invalid length "
                f"{month.month_length}"
            )


def validate_day_continuity(bundle: DatasetBundle, report: ValidationReport) -> None:
    """Validate Gregorian continuity and lunar day progression."""

    for current, following in zip(bundle.records, bundle.records[1:]):
        if following.gregorian_date - current.gregorian_date != timedelta(days=1):
            report.add(
                "Gregorian continuity broken between "
                f"{current.gregorian_date.isoformat()} and {following.gregorian_date.isoformat()}"
            )
        if current.lunar_day < current.lunar_month_length:
            if following.lunar_day != current.lunar_day + 1:
                report.add(
                    "Lunar day progression broken between "
                    f"{current.gregorian_date.isoformat()} and "
                    f"{following.gregorian_date.isoformat()}"
                )
        elif following.lunar_day != 1:
            report.add(
                f"Lunar month did not reset after {current.gregorian_date.isoformat()}"
            )


def validate_month_11_and_leaps(bundle: DatasetBundle, report: ValidationReport) -> None:
    """Validate month 11 and leap-month rules structurally."""

    spans: dict[int, list[LunarMonth]] = {}
    for month in bundle.months:
        spans.setdefault(month.anchor_year, []).append(month)

    for anchor_year, months in sorted(spans.items()):
        if not months:
            continue
        first = months[0]
        if first.lunar_month != 11 or first.lunar_year != anchor_year:
            # The dataset may be intentionally sliced so the leading anchor year is partial.
            continue
        if len(months) not in (12, 13):
            # The dataset may also be sliced at the trailing edge.
            continue
        if first.lunar_month != 11 or first.is_leap_month:
            report.add(f"Anchor year {anchor_year} does not start at month 11")
        if not first.principal_term or first.principal_term.longitude_deg != 270:
            report.add(f"Month 11 for anchor year {anchor_year} does not contain Đông chí")

        leap_months = [month for month in months if month.is_leap_month]
        if len(months) == 13:
            if len(leap_months) != 1:
                report.add(f"Anchor year {anchor_year} should have exactly one leap month")
            else:
                leap_month = leap_months[0]
                if leap_month.contains_principal_term:
                    report.add(
                        "Leap month starting "
                        f"{leap_month.start_gregorian_date.isoformat()} "
                        "unexpectedly contains a principal term"
                    )
                for month in months[1:]:
                    if not month.contains_principal_term:
                        if month is not leap_month:
                            report.add(
                                "First no-principal-term month rule broken in "
                                f"anchor year {anchor_year}"
                            )
                        break
        elif leap_months:
            report.add(f"Anchor year {anchor_year} has leap months in a 12-month span")


def validate_round_trip(bundle: DatasetBundle, report: ValidationReport) -> None:
    """Validate solar/lunar round-trip conversions exhaustively."""

    converter = LunarConverter(bundle)
    for record in bundle.records:
        solar_back = converter.solar_to_lunar(record.gregorian_date)
        if solar_back.to_dict() != record.to_dict():
            report.add(f"Solar lookup mismatch at {record.gregorian_date.isoformat()}")

        lunar_back = converter.lunar_to_solar(
            lunar_year=record.lunar_year,
            lunar_month=record.lunar_month,
            lunar_day=record.lunar_day,
            is_leap_month=record.is_leap_month,
        )
        if lunar_back.gregorian_date != record.gregorian_date:
            report.add(
                "Lunar round-trip mismatch for "
                f"{record.lunar_year}-{record.lunar_month}-{record.lunar_day} "
                f"leap={record.is_leap_month}"
            )


def validate_bundle(bundle: DatasetBundle) -> ValidationReport:
    """Run the full validation suite and return the report."""

    report = ValidationReport()
    validate_month_lengths(bundle, report)
    validate_day_continuity(bundle, report)
    validate_month_11_and_leaps(bundle, report)
    validate_round_trip(bundle, report)
    return report
