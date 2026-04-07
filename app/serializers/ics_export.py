"""iCalendar export helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.lunar.models import DatasetMetadata, DayRecord

LUNAR_MONTH_NAMES = {
    1: "Giêng",
    2: "Hai",
    3: "Ba",
    4: "Tư",
    5: "Năm",
    6: "Sáu",
    7: "Bảy",
    8: "Tám",
    9: "Chín",
    10: "Mười",
    11: "Mười một",
    12: "Chạp",
}


def escape_ical_text(value: str) -> str:
    """Escape text for iCalendar content lines."""

    return (
        value.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def fold_ical_line(line: str) -> str:
    """Fold a single iCalendar content line at 75 octets."""

    encoded = line.encode("utf-8")
    if len(encoded) <= 75:
        return line

    parts: list[str] = []
    current = ""
    current_length = 0
    for character in line:
        char_bytes = len(character.encode("utf-8"))
        if current and current_length + char_bytes > 75:
            parts.append(current)
            current = " " + character
            current_length = 1 + char_bytes
        else:
            current += character
            current_length += char_bytes
    if current:
        parts.append(current)
    return "\r\n".join(parts)


def stable_uid(record: DayRecord) -> str:
    """Return a deterministic UID for an all-day event."""

    return f"vn-lunar-{record.gregorian_date.strftime('%Y%m%d')}@lunar-ics.local"


def format_summary(record: DayRecord) -> str:
    """Return a short ICS summary for a day record."""

    month_name = LUNAR_MONTH_NAMES[record.lunar_month]
    if record.lunar_day == 1:
        suffix = " nhuận" if record.is_leap_month else ""
        return f"Mùng 1 tháng {month_name}{suffix} ÂL"
    suffix = " nhuận" if record.is_leap_month else ""
    return f"{record.lunar_day:02d}/{record.lunar_month:02d}{suffix} ÂL"


def format_description(record: DayRecord) -> str:
    """Return a detailed ICS description for a day record."""

    parts = [
        f"Gregorian: {record.gregorian_date.isoformat()}",
        "Lunar: "
        f"{record.lunar_day:02d}/{record.lunar_month:02d}/{record.lunar_year}"
        f"{' leap' if record.is_leap_month else ''}",
        f"Leap month: {'true' if record.is_leap_month else 'false'}",
        f"Month length: {record.lunar_month_length}",
    ]
    if record.principal_term:
        parts.append(f"Principal term: {record.principal_term}")
    return " | ".join(parts)


def build_ics_calendar(
    *,
    records: list[DayRecord],
    metadata: DatasetMetadata,
    calendar_name: str,
    dtstamp: datetime | None = None,
) -> str:
    """Build an RFC 5545 compatible iCalendar document."""

    stamp = (dtstamp or metadata.generated_at_utc).astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//lunar-ics//Vietnamese Lunar Calendar//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:" + escape_ical_text(calendar_name),
        "X-WR-TIMEZONE:Asia/Ho_Chi_Minh",
    ]

    for record in records:
        start = record.gregorian_date.strftime("%Y%m%d")
        end = (record.gregorian_date + timedelta(days=1)).strftime("%Y%m%d")
        description = escape_ical_text(format_description(record))
        summary = escape_ical_text(format_summary(record))
        event_lines = [
            "BEGIN:VEVENT",
            f"UID:{stable_uid(record)}",
            f"DTSTAMP:{stamp}",
            f"DTSTART;VALUE=DATE:{start}",
            f"DTEND;VALUE=DATE:{end}",
            f"SUMMARY:{summary}",
            f"DESCRIPTION:{description}",
            "END:VEVENT",
        ]
        lines.extend(event_lines)

    lines.append("END:VCALENDAR")
    return "\r\n".join(fold_ical_line(line) for line in lines) + "\r\n"


def write_ics_file(
    path: Path,
    *,
    records: list[DayRecord],
    metadata: DatasetMetadata,
    calendar_name: str,
) -> None:
    """Write an iCalendar document to disk."""

    path.parent.mkdir(parents=True, exist_ok=True)
    content = build_ics_calendar(
        records=records,
        metadata=metadata,
        calendar_name=calendar_name,
    )
    path.write_text(content, encoding="utf-8", newline="")

