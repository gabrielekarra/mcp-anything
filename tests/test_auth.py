"""Tests for HTTP authentication support in design phase."""

import json
from pathlib import Path

import pytest

from mcp_anything.models.analysis import AnalysisResult, IPCMechanism, IPCType
from mcp_anything.models.design import AuthConfig
from mcp_anything.pipeline.design import _build_auth_config, _build_backend_config


def _make_analysis(
    app_name: str = "testapp",
    ipc_type: IPCType = IPCType.PROTOCOL,
    mechanism_details: dict | None = None,
) -> AnalysisResult:
    """Create a minimal AnalysisResult for testing."""
    mechs = []
    if mechanism_details is not None:
        mechs.append(IPCMechanism(
            ipc_type=ipc_type,
            confidence=0.9,
            evidence=["test"],
            details=mechanism_details,
        ))
    return AnalysisResult(
        app_name=app_name,
        app_description=f"MCP server for {app_name}",
        languages=[],
        files=[],
        ipc_mechanisms=mechs,
        capabilities=[],
        primary_ipc=ipc_type,
    )


class TestBuildAuthConfig:
    def test_no_auth_when_no_spec(self):
        analysis = _make_analysis(mechanism_details={"protocol": "http"})
        auth = _build_auth_config(analysis)
        assert auth.auth_type == ""

    def test_bearer_from_openapi_spec(self, tmp_path):
        spec = {
            "openapi": "3.0.0",
            "paths": {},
            "components": {
                "securitySchemes": {
                    "bearerAuth": {"type": "http", "scheme": "bearer"}
                }
            },
        }
        spec_file = tmp_path / "openapi.json"
        spec_file.write_text(json.dumps(spec))

        analysis = _make_analysis(
            mechanism_details={"spec_file": "openapi.json", "protocol": "http"}
        )
        auth = _build_auth_config(analysis, str(tmp_path))
        assert auth.auth_type == "bearer"
        assert auth.env_var_token == "TESTAPP_TOKEN"

    def test_api_key_header_from_openapi_spec(self, tmp_path):
        spec = {
            "openapi": "3.0.0",
            "paths": {},
            "components": {
                "securitySchemes": {
                    "apiKey": {
                        "type": "apiKey",
                        "name": "X-API-Key",
                        "in": "header",
                    }
                }
            },
        }
        spec_file = tmp_path / "openapi.json"
        spec_file.write_text(json.dumps(spec))

        analysis = _make_analysis(
            mechanism_details={"spec_file": "openapi.json", "protocol": "http"}
        )
        auth = _build_auth_config(analysis, str(tmp_path))
        assert auth.auth_type == "api_key"
        assert auth.api_key_header == "X-API-Key"
        assert auth.api_key_query == ""
        assert auth.env_var_token == "TESTAPP_API_KEY"

    def test_api_key_query_from_openapi_spec(self, tmp_path):
        spec = {
            "openapi": "3.0.0",
            "paths": {},
            "components": {
                "securitySchemes": {
                    "apiKey": {
                        "type": "apiKey",
                        "name": "api_key",
                        "in": "query",
                    }
                }
            },
        }
        spec_file = tmp_path / "openapi.json"
        spec_file.write_text(json.dumps(spec))

        analysis = _make_analysis(
            mechanism_details={"spec_file": "openapi.json", "protocol": "http"}
        )
        auth = _build_auth_config(analysis, str(tmp_path))
        assert auth.auth_type == "api_key"
        assert auth.api_key_header == ""
        assert auth.api_key_query == "api_key"

    def test_basic_auth_from_openapi_spec(self, tmp_path):
        spec = {
            "openapi": "3.0.0",
            "paths": {},
            "components": {
                "securitySchemes": {
                    "basicAuth": {"type": "http", "scheme": "basic"}
                }
            },
        }
        spec_file = tmp_path / "openapi.json"
        spec_file.write_text(json.dumps(spec))

        analysis = _make_analysis(
            mechanism_details={"spec_file": "openapi.json", "protocol": "http"}
        )
        auth = _build_auth_config(analysis, str(tmp_path))
        assert auth.auth_type == "basic"
        assert auth.env_var_username == "TESTAPP_USERNAME"
        assert auth.env_var_password == "TESTAPP_PASSWORD"

    def test_auth_from_ipc_details(self):
        analysis = _make_analysis(
            mechanism_details={"auth_type": "bearer", "protocol": "http"}
        )
        auth = _build_auth_config(analysis)
        assert auth.auth_type == "bearer"
        assert auth.env_var_token == "TESTAPP_TOKEN"

    def test_api_key_from_ipc_details(self):
        analysis = _make_analysis(
            mechanism_details={
                "auth_type": "api_key",
                "auth_header": "Authorization",
                "protocol": "http",
            }
        )
        auth = _build_auth_config(analysis)
        assert auth.auth_type == "api_key"
        assert auth.api_key_header == "Authorization"

    def test_env_var_names_use_app_name(self, tmp_path):
        spec = {
            "openapi": "3.0.0",
            "paths": {},
            "components": {
                "securitySchemes": {
                    "bearerAuth": {"type": "http", "scheme": "bearer"}
                }
            },
        }
        spec_file = tmp_path / "openapi.json"
        spec_file.write_text(json.dumps(spec))

        analysis = _make_analysis(
            app_name="my-cool-api",
            mechanism_details={"spec_file": "openapi.json", "protocol": "http"},
        )
        auth = _build_auth_config(analysis, str(tmp_path))
        assert auth.env_var_token == "MY_COOL_API_TOKEN"


class TestBackendConfigAuth:
    def test_backend_config_includes_auth(self, tmp_path):
        spec = {
            "openapi": "3.0.0",
            "paths": {},
            "components": {
                "securitySchemes": {
                    "bearerAuth": {"type": "http", "scheme": "bearer"}
                }
            },
        }
        spec_file = tmp_path / "openapi.json"
        spec_file.write_text(json.dumps(spec))

        analysis = _make_analysis(
            mechanism_details={
                "spec_file": "openapi.json",
                "protocol": "http",
                "port": "8080",
            }
        )
        config = _build_backend_config(analysis, str(tmp_path))
        assert config is not None
        assert config.auth.auth_type == "bearer"
        assert config.auth.env_var_token == "TESTAPP_TOKEN"

    def test_backend_config_no_auth_when_none(self):
        analysis = _make_analysis(
            mechanism_details={"protocol": "http", "port": "8080"}
        )
        config = _build_backend_config(analysis, "/nonexistent")
        assert config is not None
        assert config.auth.auth_type == ""
