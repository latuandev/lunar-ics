"""Dataset build and export orchestration."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from app.lunar.models import DatasetBundle, DatasetMetadata, DayRecord, LunarMonth, PrincipalTerm
from app.lunar.validators import validate_bundle
from app.lunar.vietnamese_rules import build_dataset_bundle
from app.serializers.csv_export import write_csv_file
from app.serializers.ics_export import write_ics_file
from app.serializers.json_export import read_json_file, write_json_file


class DatasetBuilder:
    """Build, load, validate, and export calendar datasets."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir

    @property
    def full_json_path(self) -> Path:
        """Return the canonical full JSON export path."""

        return self.data_dir / "json" / "vn_lunar_2000_2100.json"

    @property
    def full_csv_path(self) -> Path:
        """Return the canonical full CSV export path."""

        return self.data_dir / "csv" / "vn_lunar_2000_2100.csv"

    @property
    def full_ics_path(self) -> Path:
        """Return the canonical full ICS export path."""

        return self.data_dir / "ics" / "vn_lunar_2000_2100.ics"

    def build_bundle(self, from_year: int, to_year: int) -> DatasetBundle:
        """Build an in-memory dataset bundle."""

        return build_dataset_bundle(from_year, to_year)

    def export_bundle(self, bundle: DatasetBundle) -> None:
        """Export JSON, CSV, and ICS files for the bundle."""

        write_json_file(self.full_json_path, bundle.to_dict())
        write_csv_file(self.full_csv_path, bundle.records)
        write_ics_file(
            self.full_ics_path,
            records=bundle.records,
            metadata=bundle.metadata,
            calendar_name="Lịch âm Việt Nam 2000-2100",
        )

        for year in range(bundle.metadata.from_year, bundle.metadata.to_year + 1):
            year_records = [
                record for record in bundle.records if record.gregorian_date.year == year
            ]
            year_payload = {
                "metadata": bundle.metadata.to_dict(),
                "year": year,
                "count": len(year_records),
                "records": [record.to_dict() for record in year_records],
            }
            write_json_file(self.data_dir / "json" / "year" / f"{year}.json", year_payload)
            write_ics_file(
                self.data_dir / "ics" / "year" / f"{year}.ics",
                records=year_records,
                metadata=bundle.metadata,
                calendar_name=f"Lịch âm Việt Nam {year}",
            )

    def build_and_export(self, from_year: int, to_year: int) -> DatasetBundle:
        """Build, validate, and export a dataset bundle."""

        bundle = self.build_bundle(from_year, to_year)
        report = validate_bundle(bundle)
        report.assert_valid()
        self.export_bundle(bundle)
        return bundle

    def load_bundle(self, path: Path | None = None) -> DatasetBundle:
        """Load a previously exported bundle from disk."""

        payload = read_json_file(path or self.full_json_path)
        metadata = self._metadata_from_dict(payload["metadata"])
        months = [self._month_from_dict(item) for item in payload["months"]]
        records = [self._record_from_dict(item) for item in payload["records"]]
        bundle = DatasetBundle(metadata=metadata, months=months, records=records)
        bundle.build_indexes()
        return bundle

    def _metadata_from_dict(self, data: dict) -> DatasetMetadata:
        return DatasetMetadata(
            from_year=int(data["from_year"]),
            to_year=int(data["to_year"]),
            start_date=date.fromisoformat(data["start_date"]),
            end_date=date.fromisoformat(data["end_date"]),
            generated_at_utc=datetime.fromisoformat(data["generated_at_utc"]),
            timezone_name=str(data["timezone_name"]),
            reference_longitude_deg=float(data["reference_longitude_deg"]),
            algorithm_version=str(data["algorithm_version"]),
        )

    def _principal_term_from_dict(self, data: dict | None) -> PrincipalTerm | None:
        if data is None:
            return None
        return PrincipalTerm(
            index=int(data["index"]),
            longitude_deg=int(data["longitude_deg"]),
            name=str(data["name"]),
            jd_ut=float(data["jd_ut"]),
            local_datetime=datetime.fromisoformat(data["local_datetime"]),
        )

    def _month_from_dict(self, data: dict) -> LunarMonth:
        return LunarMonth(
            start_jd_ut=float(data.get("start_jd_ut", 0.0)),
            end_jd_ut=float(data.get("end_jd_ut", 0.0)),
            start_gregorian_date=date.fromisoformat(data["start_gregorian_date"]),
            end_gregorian_date=date.fromisoformat(data["end_gregorian_date"]),
            month_length=int(data["month_length"]),
            lunar_month=int(data["lunar_month"]),
            lunar_year=int(data["lunar_year"]),
            is_leap_month=bool(data["is_leap_month"]),
            contains_principal_term=bool(data["contains_principal_term"]),
            principal_term=self._principal_term_from_dict(data.get("principal_term")),
            is_month_11=bool(data["is_month_11"]),
            anchor_year=int(data["anchor_year"]),
        )

    def _record_from_dict(self, data: dict) -> DayRecord:
        return DayRecord(
            gregorian_date=date.fromisoformat(data["gregorian_date"]),
            lunar_day=int(data["lunar_day"]),
            lunar_month=int(data["lunar_month"]),
            lunar_year=int(data["lunar_year"]),
            is_leap_month=bool(data["is_leap_month"]),
            lunar_month_length=int(data["lunar_month_length"]),
            month_start_gregorian_date=date.fromisoformat(data["month_start_gregorian_date"]),
            month_end_gregorian_date=date.fromisoformat(data["month_end_gregorian_date"]),
            principal_term=data.get("principal_term"),
            principal_term_longitude_deg=(
                int(data["principal_term_longitude_deg"])
                if data.get("principal_term_longitude_deg") is not None
                else None
            ),
            principal_term_moment_local=data.get("principal_term_moment_local"),
        )
