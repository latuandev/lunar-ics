"""CLI entrypoint for building, verifying, and serving the project."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from urllib.request import urlopen

from app.config import Settings
from app.logging_config import configure_logging
from app.lunar.validators import validate_bundle
from app.server import serve
from app.services.calendar_feed_service import validate_rolling_years
from app.services.dataset_builder import DatasetBuilder
from app.services.query_service import QueryService

LOGGER = logging.getLogger(__name__)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""

    settings = Settings.from_env()
    parser = argparse.ArgumentParser(prog="python -m app.main")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build-dataset", help="Build and export dataset files")
    build.add_argument("--from-year", type=int, default=2000)
    build.add_argument("--to-year", type=int, default=2100)
    build.add_argument("--data-dir", type=Path, default=settings.data_dir)

    verify = subparsers.add_parser("verify", help="Verify dataset integrity")
    verify.add_argument("--from-year", type=int, default=2000)
    verify.add_argument("--to-year", type=int, default=2100)
    verify.add_argument("--data-dir", type=Path, default=settings.data_dir)
    verify.add_argument(
        "--load-existing",
        action="store_true",
        help="Validate the exported JSON bundle instead of rebuilding in memory",
    )

    rolling = subparsers.add_parser(
        "build-rolling-ics",
        help="Build the rolling ICS feed for the current Vietnam-year window",
    )
    rolling.add_argument("--years", type=int, default=5)
    rolling.add_argument("--data-dir", type=Path, default=settings.data_dir)

    run = subparsers.add_parser("serve", help="Run the stdlib HTTP server")
    run.add_argument("--host", default=settings.app_host)
    run.add_argument("--port", type=int, default=settings.app_port)
    run.add_argument("--data-dir", type=Path, default=settings.data_dir)

    smoke = subparsers.add_parser("smoke-test", help="Run a quick HTTP smoke test")
    smoke.add_argument("--base-url", default=f"http://127.0.0.1:{settings.app_port}")

    parser.add_argument("--log-level", default=settings.log_level)
    parser.add_argument("--json-logs", action="store_true")
    return parser.parse_args(argv)


def ensure_dataset(data_dir: Path) -> QueryService:
    """Load the full dataset, building it first when missing."""

    builder = DatasetBuilder(data_dir)
    if not builder.full_json_path.exists():
        LOGGER.info("Dataset not found at %s, building canonical export", builder.full_json_path)
        builder.build_and_export(2000, 2100)
    return QueryService.load(data_dir)


def run_build_dataset(args: argparse.Namespace) -> int:
    """Build and export the requested dataset."""

    builder = DatasetBuilder(args.data_dir)
    bundle = builder.build_and_export(args.from_year, args.to_year)
    LOGGER.info(
        "Built dataset for %s..%s with %s records",
        args.from_year,
        args.to_year,
        len(bundle.records),
    )
    return 0


def run_verify(args: argparse.Namespace) -> int:
    """Validate a dataset and return an exit code."""

    builder = DatasetBuilder(args.data_dir)
    bundle = (
        builder.load_bundle()
        if args.load_existing and builder.full_json_path.exists()
        else builder.build_bundle(args.from_year, args.to_year)
    )
    report = validate_bundle(bundle)
    report.assert_valid()
    LOGGER.info(
        "Verification passed for %s..%s with %s records",
        bundle.metadata.from_year,
        bundle.metadata.to_year,
        len(bundle.records),
    )
    return 0


def run_serve(args: argparse.Namespace) -> int:
    """Load the dataset and start the HTTP server."""

    query_service = ensure_dataset(args.data_dir)
    serve(args.host, args.port, query_service)
    return 0


def run_smoke_test(args: argparse.Namespace) -> int:
    """Run a small smoke test against a running HTTP endpoint."""

    endpoints = [
        "/healthz",
        "/api/v1/calendar/rolling-window",
        "/api/v1/date/2024-02-10",
        "/api/v1/lunar-to-solar?year=2024&month=1&day=1&leap=0",
        "/calendar/vn_lunar_5y.ics",
    ]
    for endpoint in endpoints:
        with urlopen(args.base_url.rstrip("/") + endpoint) as response:
            if response.status != 200:
                raise RuntimeError(f"Smoke test failed for {endpoint}: {response.status}")
    LOGGER.info("Smoke test passed against %s", args.base_url)
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI main function."""

    args = parse_args(argv)
    configure_logging(level=args.log_level, json_logs=args.json_logs)

    if args.command == "build-dataset":
        return run_build_dataset(args)
    if args.command == "verify":
        return run_verify(args)
    if args.command == "build-rolling-ics":
        return run_build_rolling_ics(args)
    if args.command == "serve":
        return run_serve(args)
    if args.command == "smoke-test":
        return run_smoke_test(args)
    raise ValueError(f"Unsupported command: {args.command}")


def run_build_rolling_ics(args: argparse.Namespace) -> int:
    """Build the rolling ICS feed for the configured data directory."""

    validated_years = validate_rolling_years(args.years)
    query_service = ensure_dataset(args.data_dir)
    output_path = query_service.calendar_feed_service.ensure_rolling_ics(validated_years)
    window = query_service.calendar_feed_service.get_rolling_window(validated_years)
    LOGGER.info(
        "Built rolling ICS feed %s covering %s..%s",
        output_path,
        window.start_year,
        window.end_year,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
