"""Stdlib HTTP server entrypoint."""

from __future__ import annotations

import logging
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import ClassVar

from app.routes import HttpError, Router, error_payload
from app.services.query_service import QueryService

LOGGER = logging.getLogger(__name__)


class RequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler backed by the query service."""

    router: ClassVar[Router]
    server_version = "LunarICS/1.0"

    def do_GET(self) -> None:  # noqa: N802
        """Handle GET requests."""

        try:
            status, content_type, body, extra_headers = self.router.dispatch(self.path)
        except HttpError as exc:
            status = exc.status_code
            content_type = "application/json; charset=utf-8"
            import json

            body = json.dumps(
                error_payload(exc.code, exc.message),
                ensure_ascii=False,
                indent=2,
            ).encode("utf-8")
            extra_headers = {"Cache-Control": "no-store"}
        except Exception:
            LOGGER.exception("Unhandled request error")
            status = HTTPStatus.INTERNAL_SERVER_ERROR
            content_type = "application/json; charset=utf-8"
            import json

            body = json.dumps(
                error_payload("internal_error", "internal server error"),
                ensure_ascii=False,
                indent=2,
            ).encode("utf-8")
            extra_headers = {"Cache-Control": "no-store"}

        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for key, value in extra_headers.items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        """Route access logs through the standard logger."""

        LOGGER.info(
            "%s - - [%s] %s",
            self.client_address[0],
            self.log_date_time_string(),
            format % args,
        )


def create_http_server(host: str, port: int, query_service: QueryService) -> ThreadingHTTPServer:
    """Create the threaded HTTP server instance."""

    RequestHandler.router = Router(query_service)
    return ThreadingHTTPServer((host, port), RequestHandler)


def serve(host: str, port: int, query_service: QueryService) -> None:
    """Run the HTTP server until interrupted."""

    server = create_http_server(host, port, query_service)
    LOGGER.info("Serving on http://%s:%s", host, port)
    try:
        server.serve_forever()
    finally:
        server.server_close()

