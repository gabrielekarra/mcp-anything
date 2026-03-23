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
def fake_jaxrs_app(fixtures_dir) -> Path:
    return fixtures_dir / "fake_jaxrs_app"


@pytest.fixture
def fake_kotlin_jaxrs_app(fixtures_dir) -> Path:
    return fixtures_dir / "fake_kotlin_jaxrs_app"


@pytest.fixture
def fake_kotlin_spring_app(fixtures_dir) -> Path:
    return fixtures_dir / "fake_kotlin_spring_app"


@pytest.fixture
def fake_micronaut_app(fixtures_dir) -> Path:
    return fixtures_dir / "fake_micronaut_app"


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
def fake_ts_express_app(fixtures_dir) -> Path:
    return fixtures_dir / "fake_ts_express_app"


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
def fake_ws_protocol_app(fixtures_dir) -> Path:
    return fixtures_dir / "fake_ws_protocol_app"


@pytest.fixture
def fake_axum_app(fixtures_dir) -> Path:
    return fixtures_dir / "fake_axum_app"


@pytest.fixture
def fake_rocket_app(fixtures_dir) -> Path:
    return fixtures_dir / "fake_rocket_app"


@pytest.fixture
def fake_go_echo_app(fixtures_dir) -> Path:
    return fixtures_dir / "fake_go_echo_app"


@pytest.fixture
def fake_go_chi_app(fixtures_dir) -> Path:
    return fixtures_dir / "fake_go_chi_app"


@pytest.fixture
def fake_go_mux_app(fixtures_dir) -> Path:
    return fixtures_dir / "fake_go_mux_app"


@pytest.fixture
def fake_go_nethttp_app(fixtures_dir) -> Path:
    return fixtures_dir / "fake_go_nethttp_app"


@pytest.fixture
def fake_socket_xmlrpc_app(fixtures_dir) -> Path:
    return fixtures_dir / "fake_socket_xmlrpc_app"


@pytest.fixture
def fake_rails_explicit_routes_app(fixtures_dir) -> Path:
    return fixtures_dir / "fake_rails_explicit_routes_app"


@pytest.fixture
def fake_click_app(fixtures_dir) -> Path:
    return fixtures_dir / "fake_click_app"


@pytest.fixture
def fake_warp_app(fixtures_dir) -> Path:
    return fixtures_dir / "fake_warp_app"


@pytest.fixture
def tmp_output(tmp_path) -> Path:
    return tmp_path / "output"
