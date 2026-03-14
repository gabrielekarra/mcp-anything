"""Shared test fixtures for mcp-anything."""

from pathlib import Path

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def fake_cli_app(fixtures_dir) -> Path:
    return fixtures_dir / "fake_cli_app"


@pytest.fixture
def fake_spring_app(fixtures_dir) -> Path:
    return fixtures_dir / "fake_spring_app"


@pytest.fixture
def fake_fastapi_app(fixtures_dir) -> Path:
    return fixtures_dir / "fake_fastapi_app"


@pytest.fixture
def fake_flask_app(fixtures_dir) -> Path:
    return fixtures_dir / "fake_flask_app"


@pytest.fixture
def tmp_output(tmp_path) -> Path:
    return tmp_path / "output"
