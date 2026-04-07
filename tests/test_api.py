"""HTTP API integration tests."""

from __future__ import annotations

import json

from app.routes import HttpError


def dispatch_json(router, path: str) -> dict:
    status, content_type, body, _ = router.dispatch(path)
    assert status == 200
    assert content_type.startswith("application/json")
    return json.loads(body.decode("utf-8"))


def test_healthz(router) -> None:
    payload = dispatch_json(router, "/healthz")
    assert payload == {"status": "ok"}


def test_date_lookup(router) -> None:
    payload = dispatch_json(router, "/api/v1/date/2024-02-10")
    assert payload["lunar_day"] == 1
    assert payload["lunar_month"] == 1
    assert payload["lunar_year"] == 2024


def test_lunar_to_solar_invalid_input(router) -> None:
    try:
        router.dispatch("/api/v1/lunar-to-solar?year=2024&month=13&day=1&leap=0")
    except HttpError as exc:
        assert exc.status_code == 400
        assert exc.code == "invalid_input"
    else:
        raise AssertionError("Expected HTTP 400 for invalid lunar input")


def test_year_endpoint_and_formats(router) -> None:
    payload = dispatch_json(router, "/api/v1/year/2024")
    assert payload["year"] == 2024
    assert payload["count"] == 366

    status, content_type, body, _ = router.dispatch("/api/v1/year/2024?format=csv")
    assert status == 200
    assert content_type.startswith("text/csv")
    assert body.decode("utf-8").startswith("gregorian_date,")


def test_ics_and_download_endpoints(router) -> None:
    status, content_type, body, _ = router.dispatch("/calendar/vn_lunar_2000_2100.ics")
    assert status == 200
    assert content_type.startswith("text/calendar")
    assert body.startswith(b"BEGIN:VCALENDAR")

    status, content_type, body, _ = router.dispatch("/downloads/json/year/2024.json")
    assert status == 200
    assert content_type.startswith("application/json")
    payload = json.loads(body.decode("utf-8"))
    assert payload["year"] == 2024
