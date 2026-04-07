"""HEAD request tests for the stdlib HTTP handler."""

from __future__ import annotations

from io import BytesIO

from app.server import RequestHandler


def build_fake_handler(router, path: str):
    handler = RequestHandler.__new__(RequestHandler)
    handler.router = router
    handler.path = path
    handler.wfile = BytesIO()
    handler.client_address = ("127.0.0.1", 12345)
    handler.request_version = "HTTP/1.1"
    handler.command = "HEAD"
    handler.requestline = f"HEAD {path} HTTP/1.1"
    handler.headers_sent = []
    handler.status_code = None

    def send_response(code: int, message: str | None = None) -> None:
        handler.status_code = code

    def send_header(key: str, value: str) -> None:
        handler.headers_sent.append((key, value))

    def end_headers() -> None:
        return None

    handler.send_response = send_response
    handler.send_header = send_header
    handler.end_headers = end_headers
    return handler


def assert_head_response(handler, expected_content_type_prefix: str) -> None:
    assert handler.status_code == 200
    assert any(
        key == "Content-Type" and value.startswith(expected_content_type_prefix)
        for key, value in handler.headers_sent
    )
    assert handler.wfile.getvalue() == b""


def test_head_request_for_rolling_ics(router) -> None:
    handler = build_fake_handler(router, "/calendar/vn_lunar_5y.ics")
    RequestHandler.do_HEAD(handler)
    assert_head_response(handler, "text/calendar")


def test_head_request_for_healthz(router) -> None:
    handler = build_fake_handler(router, "/healthz")
    RequestHandler.do_HEAD(handler)
    assert_head_response(handler, "application/json")


def test_head_request_for_json_api(router) -> None:
    handler = build_fake_handler(router, "/api/v1/calendar/rolling-window")
    RequestHandler.do_HEAD(handler)
    assert_head_response(handler, "application/json")
