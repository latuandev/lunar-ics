"""ICS export tests."""

from __future__ import annotations

from app.serializers.ics_export import build_ics_calendar


def parse_events(content: str) -> list[dict[str, str]]:
    events: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for raw_line in content.split("\r\n"):
        if raw_line == "BEGIN:VEVENT":
            current = {}
        elif raw_line == "END:VEVENT":
            assert current is not None
            events.append(current)
            current = None
        elif current is not None and ":" in raw_line:
            key, value = raw_line.split(":", 1)
            current[key] = value
    return events


def test_ics_structure_and_event_count(small_bundle) -> None:
    content = build_ics_calendar(
        records=small_bundle.records,
        metadata=small_bundle.metadata,
        calendar_name="Test Calendar",
    )
    assert content.startswith("BEGIN:VCALENDAR\r\n")
    assert content.endswith("END:VCALENDAR\r\n")
    assert content.count("BEGIN:VEVENT") == len(small_bundle.records)

    events = parse_events(content)
    assert len(events) == len(small_bundle.records)

    uids = {event["UID"] for event in events}
    assert len(uids) == len(events)
    for event in events[:10]:
        assert event["DTSTART;VALUE=DATE"]
        assert event["DTEND;VALUE=DATE"]
        assert event["SUMMARY"]
        assert event["DESCRIPTION"]


def test_ics_dates_are_all_day_and_monotonic(small_bundle) -> None:
    content = build_ics_calendar(
        records=small_bundle.records,
        metadata=small_bundle.metadata,
        calendar_name="Test Calendar",
    )
    events = parse_events(content)
    for record, event in zip(small_bundle.records, events):
        assert event["DTSTART;VALUE=DATE"] == record.gregorian_date.strftime("%Y%m%d")
        assert event["DTEND;VALUE=DATE"] == (
            record.gregorian_date + __import__("datetime").timedelta(days=1)
        ).strftime("%Y%m%d")

