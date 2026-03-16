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
def fake_spring_mvc_app(fixtures_dir) -> Path:
    return fixtures_dir / "fake_spring_mvc_app"


@pytest.fixture
def fake_fastapi_app(fixtures_dir) -> Path:
    return fixtures_dir / "fake_fastapi_app"


@pytest.fixture
def fake_flask_app(fixtures_dir) -> Path:
    return fixtures_dir / "fake_flask_app"


@pytest.fixture
def fake_express_app(fixtures_dir) -> Path:
    return fixtures_dir / "fake_express_app"


@pytest.fixture
def fake_django_app(fixtures_dir) -> Path:
    return fixtures_dir / "fake_django_app"


@pytest.fixture
def fake_go_app(fixtures_dir) -> Path:
    return fixtures_dir / "fake_go_app"


@pytest.fixture
def fake_rails_app(fixtures_dir) -> Path:
    return fixtures_dir / "fake_rails_app"


@pytest.fixture
def fake_rust_app(fixtures_dir) -> Path:
    return fixtures_dir / "fake_rust_app"


@pytest.fixture
def fake_graphql_app(fixtures_dir) -> Path:
    return fixtures_dir / "fake_graphql_app"


@pytest.fixture
def fake_grpc_app(fixtures_dir) -> Path:
    return fixtures_dir / "fake_grpc_app"


@pytest.fixture
def fake_websocket_app(fixtures_dir) -> Path:
    return fixtures_dir / "fake_websocket_app"


@pytest.fixture
def tmp_output(tmp_path) -> Path:
    return tmp_path / "output"
