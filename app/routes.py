"""HTTP routing helpers."""

from __future__ import annotations

import csv
from datetime import date
from io import StringIO
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from app.serializers.csv_export import CSV_COLUMNS
from app.serializers.ics_export import build_ics_calendar
from app.services.query_service import QueryService
from app.types import JSONDict
from app.utils.date_utils import parse_iso_date


class HttpError(Exception):
    """Application-level HTTP error."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def error_payload(code: str, message: str) -> JSONDict:
    """Build the standard JSON error payload."""

    return {
        "error": {
            "code": code,
            "message": message,
        }
    }


class Router:
    """Dispatch GET routes for the calendar API."""

    def __init__(self, query_service: QueryService) -> None:
        self.query_service = query_service

    def dispatch(self, raw_path: str) -> tuple[int, str, bytes, dict[str, str]]:
        """Dispatch a GET request and return a response tuple."""

        parsed = urlparse(raw_path)
        query = parse_qs(parsed.query)
        path = parsed.path

        if path == "/healthz":
            return self._json(200, {"status": "ok"})
        if path.startswith("/api/v1/date/"):
            value = path.removeprefix("/api/v1/date/")
            return self._solar_to_lunar(self._parse_iso_date(value))
        if path == "/api/v1/solar-to-lunar":
            value = self._single_query_value(query, "date")
            return self._solar_to_lunar(self._parse_iso_date(value))
        if path == "/api/v1/lunar-to-solar":
            return self._lunar_to_solar(query)
        if path.startswith("/api/v1/year/"):
            year_text = path.removeprefix("/api/v1/year/")
            return self._year(self._parse_int(year_text, "year"), query.get("format", ["json"])[0])
        if path.startswith("/api/v1/month/"):
            year_text, month_text = self._tail_segments(path, "/api/v1/month/", 2)
            return self._month(
                self._parse_int(year_text, "year"),
                self._parse_int(month_text, "month"),
            )
        if path == "/api/v1/range":
            start = self._parse_iso_date(self._single_query_value(query, "start"))
            end = self._parse_iso_date(self._single_query_value(query, "end"))
            return self._range(start, end)
        if path == "/calendar/vn_lunar_2000_2100.ics":
            return self._file_response("ics/vn_lunar_2000_2100.ics", "text/calendar; charset=utf-8")
        if path.startswith("/calendar/year/") and path.endswith(".ics"):
            year = self._parse_int(
                path.removeprefix("/calendar/year/").removesuffix(".ics"),
                "year",
            )
            return self._file_response(f"ics/year/{year}.ics", "text/calendar; charset=utf-8")
        if path.startswith("/downloads/"):
            relative = path.removeprefix("/downloads/")
            resolved = self.query_service.resolve_download_path(relative)
            return self._path_response(resolved)

        raise HttpError(404, "not_found", f"Route not found: {path}")

    def _single_query_value(self, query: dict[str, list[str]], key: str) -> str:
        values = query.get(key)
        if not values or not values[0]:
            raise HttpError(400, "invalid_input", f"Missing query parameter: {key}")
        return values[0]

    def _parse_iso_date(self, value: str) -> date:
        try:
            return parse_iso_date(value)
        except ValueError as exc:
            raise HttpError(400, "invalid_input", f"Invalid ISO date: {value}") from exc

    def _parse_int(self, value: str, field_name: str) -> int:
        try:
            return int(value)
        except ValueError as exc:
            raise HttpError(
                400,
                "invalid_input",
                f"Invalid integer for {field_name}: {value}",
            ) from exc

    def _tail_segments(self, path: str, prefix: str, count: int) -> tuple[str, ...]:
        tail = path.removeprefix(prefix).strip("/")
        parts = tuple(part for part in tail.split("/") if part)
        if len(parts) != count:
            raise HttpError(404, "not_found", f"Route not found: {path}")
        return parts

    def _solar_to_lunar(self, value: date) -> tuple[int, str, bytes, dict[str, str]]:
        try:
            record = self.query_service.solar_to_lunar(value)
        except ValueError as exc:
            raise HttpError(400, "invalid_input", str(exc)) from exc
        return self._json(200, record.to_dict())

    def _lunar_to_solar(
        self, query: dict[str, list[str]]
    ) -> tuple[int, str, bytes, dict[str, str]]:
        try:
            lunar_year = int(self._single_query_value(query, "year"))
            lunar_month = int(self._single_query_value(query, "month"))
            lunar_day = int(self._single_query_value(query, "day"))
            leap = self._single_query_value(query, "leap")
            if leap not in {"0", "1"}:
                raise ValueError("leap must be 0 or 1")
            record = self.query_service.lunar_to_solar(
                lunar_year=lunar_year,
                lunar_month=lunar_month,
                lunar_day=lunar_day,
                is_leap_month=leap == "1",
            )
        except ValueError as exc:
            raise HttpError(400, "invalid_input", str(exc)) from exc
        return self._json(200, record.to_dict())

    def _year(
        self,
        year: int,
        output_format: str,
    ) -> tuple[int, str, bytes, dict[str, str]]:
        try:
            records = self.query_service.year_records(year)
        except ValueError as exc:
            raise HttpError(400, "invalid_input", str(exc)) from exc

        if output_format == "json":
            return self._json(
                200,
                {
                    "year": year,
                    "count": len(records),
                    "records": [record.to_dict() for record in records],
                },
            )
        if output_format == "csv":
            return self._csv_response(records)
        if output_format == "ics":
            calendar_name = f"Lịch âm Việt Nam {year}"
            content = build_ics_calendar(
                records=records,
                metadata=self.query_service.bundle.metadata,
                calendar_name=calendar_name,
            )
            headers = {
                "Cache-Control": "public, max-age=3600",
                "Content-Disposition": f'inline; filename="{year}.ics"',
            }
            return 200, "text/calendar; charset=utf-8", content.encode("utf-8"), headers
        raise HttpError(400, "invalid_input", "format must be one of json, csv, ics")

    def _month(self, year: int, month: int) -> tuple[int, str, bytes, dict[str, str]]:
        try:
            records = self.query_service.month_records(year, month)
        except ValueError as exc:
            raise HttpError(400, "invalid_input", str(exc)) from exc
        return self._json(
            200,
            {
                "year": year,
                "month": month,
                "count": len(records),
                "records": [record.to_dict() for record in records],
            },
        )

    def _range(self, start: date, end: date) -> tuple[int, str, bytes, dict[str, str]]:
        try:
            records = self.query_service.range_records(start, end)
        except ValueError as exc:
            raise HttpError(400, "invalid_input", str(exc)) from exc
        return self._json(
            200,
            {
                "start": start.isoformat(),
                "end": end.isoformat(),
                "count": len(records),
                "records": [record.to_dict() for record in records],
            },
        )

    def _csv_response(self, records) -> tuple[int, str, bytes, dict[str, str]]:
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for record in records:
            writer.writerow(record.to_dict())
        return (
            200,
            "text/csv; charset=utf-8",
            output.getvalue().encode("utf-8"),
            {"Cache-Control": "no-store"},
        )

    def _file_response(
        self, relative_path: str, content_type: str
    ) -> tuple[int, str, bytes, dict[str, str]]:
        try:
            resolved = self.query_service.resolve_download_path(relative_path)
        except ValueError as exc:
            raise HttpError(404, "not_found", str(exc)) from exc
        return self._path_response(resolved, content_type=content_type)

    def _path_response(
        self,
        path: Path,
        *,
        content_type: str | None = None,
    ) -> tuple[int, str, bytes, dict[str, str]]:
        if content_type is None:
            suffix = path.suffix.lower()
            if suffix == ".json":
                content_type = "application/json; charset=utf-8"
            elif suffix == ".csv":
                content_type = "text/csv; charset=utf-8"
            elif suffix == ".ics":
                content_type = "text/calendar; charset=utf-8"
            else:
                content_type = "application/octet-stream"
        headers = {
            "Cache-Control": "public, max-age=86400",
            "Content-Disposition": f'inline; filename="{path.name}"',
        }
        return 200, content_type, path.read_bytes(), headers

    def _json(self, status: int, payload: JSONDict) -> tuple[int, str, bytes, dict[str, str]]:
        import json

        return (
            status,
            "application/json; charset=utf-8",
            json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"),
            {"Cache-Control": "no-store"},
        )
