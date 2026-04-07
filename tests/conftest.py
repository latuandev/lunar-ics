"""Pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.routes import Router
from app.services.dataset_builder import DatasetBuilder
from app.services.query_service import QueryService


@pytest.fixture(scope="session")
def full_bundle():
    """Build the full canonical dataset once for the test session."""

    builder = DatasetBuilder(Path("/tmp/lunar-ics-test-full"))
    return builder.build_bundle(2000, 2100)


@pytest.fixture(scope="session")
def small_bundle():
    """Build a smaller bundle for fast unit-style tests."""

    builder = DatasetBuilder(Path("/tmp/lunar-ics-test-small"))
    return builder.build_bundle(2023, 2024)


@pytest.fixture(scope="session")
def exported_small_data_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Export a smaller dataset to a temporary directory."""

    data_dir = tmp_path_factory.mktemp("lunar-data")
    builder = DatasetBuilder(data_dir)
    builder.build_and_export(2023, 2024)
    return data_dir


@pytest.fixture(scope="session")
def router(exported_small_data_dir: Path) -> Router:
    """Return the HTTP router backed by the exported dataset."""

    service = QueryService.load(exported_small_data_dir)
    return Router(service)
