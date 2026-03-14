"""Tests for OpenAPI/Swagger spec detection and analysis."""

from pathlib import Path

import pytest

from mcp_anything.analysis.detectors.openapi_detector import OpenAPIDetector
from mcp_anything.analysis.openapi_analyzer import (
    extract_security_schemes,
    find_openapi_specs,
    openapi_to_capabilities,
    parse_openapi_spec,
    extract_server_info,
)
from mcp_anything.analysis.scanner import scan_codebase
from mcp_anything.models.analysis import IPCType


# ── Spec Discovery ──


class TestFindSpecs:
    def test_finds_json_spec(self, tmp_path):
        spec = tmp_path / "openapi.json"
        spec.write_text('{"openapi": "3.0.0", "paths": {}}')
        found = find_openapi_specs(tmp_path)
        assert len(found) >= 1
        assert spec in found

    def test_finds_yaml_spec(self, tmp_path):
        spec = tmp_path / "openapi.yaml"
        spec.write_text('openapi: "3.0.0"\npaths: {}')
        found = find_openapi_specs(tmp_path)
        assert spec in found

    def test_finds_swagger_json(self, tmp_path):
        spec = tmp_path / "swagger.json"
        spec.write_text('{"swagger": "2.0", "paths": {}}')
        found = find_openapi_specs(tmp_path)
        assert spec in found

    def test_finds_spec_in_docs_dir(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        spec = docs / "openapi.json"
        spec.write_text('{"openapi": "3.0.0", "paths": {}}')
        found = find_openapi_specs(tmp_path)
        assert spec in found

    def test_finds_custom_named_spec(self, tmp_path):
        spec = tmp_path / "my-api.json"
        spec.write_text('{"openapi": "3.0.0", "info": {}, "paths": {}}')
        found = find_openapi_specs(tmp_path)
        assert spec in found

    def test_no_specs_in_empty_dir(self, tmp_path):
        found = find_openapi_specs(tmp_path)
        assert found == []

    def test_ignores_non_spec_json(self, tmp_path):
        (tmp_path / "package.json").write_text('{"name": "test"}')
        found = find_openapi_specs(tmp_path)
        assert found == []


# ── Spec Parsing ──


class TestParseSpec:
    def test_parses_openapi3_json(self, fixtures_dir):
        spec = parse_openapi_spec(fixtures_dir / "petstore_openapi.json")
        assert spec is not None
        assert spec["openapi"] == "3.0.3"
        assert "paths" in spec

    def test_parses_swagger2_yaml(self, fixtures_dir):
        spec = parse_openapi_spec(fixtures_dir / "petstore_swagger.yaml")
        assert spec is not None
        assert spec["swagger"] == "2.0"
        assert "paths" in spec

    def test_returns_none_for_invalid(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("not json at all")
        assert parse_openapi_spec(bad) is None

    def test_returns_none_for_non_spec(self, tmp_path):
        non_spec = tmp_path / "data.json"
        non_spec.write_text('{"name": "test", "version": 1}')
        assert parse_openapi_spec(non_spec) is None


# ── Detector ──


class TestOpenAPIDetector:
    def test_detects_openapi_spec(self, tmp_path):
        spec = tmp_path / "openapi.json"
        spec.write_text('{"openapi": "3.0.0", "paths": {"/pets": {"get": {}}}}')
        files = scan_codebase(tmp_path)
        detector = OpenAPIDetector()
        mechs = detector.detect(tmp_path, files)
        assert len(mechs) == 1
        assert mechs[0].ipc_type == IPCType.PROTOCOL
        assert mechs[0].details["framework"] == "openapi"
        assert mechs[0].confidence >= 0.85

    def test_no_detection_without_spec(self, fake_cli_app):
        files = scan_codebase(fake_cli_app)
        detector = OpenAPIDetector()
        mechs = detector.detect(fake_cli_app, files)
        assert mechs == []


# ── OpenAPI 3.x Capability Extraction ──


class TestOpenAPI3Capabilities:
    @pytest.fixture
    def petstore_spec(self, fixtures_dir):
        return parse_openapi_spec(fixtures_dir / "petstore_openapi.json")

    def test_extracts_all_endpoints(self, petstore_spec):
        caps = openapi_to_capabilities(petstore_spec, "openapi.json")
        assert len(caps) == 7  # list, create, get, update, delete, vaccinations, inventory

    def test_uses_operation_id(self, petstore_spec):
        caps = openapi_to_capabilities(petstore_spec, "openapi.json")
        names = {c.name for c in caps}
        assert "list_pets" in names
        assert "create_pet" in names
        assert "get_pet" in names
        assert "update_pet" in names
        assert "delete_pet" in names

    def test_extracts_query_params(self, petstore_spec):
        caps = openapi_to_capabilities(petstore_spec, "openapi.json")
        list_pets = next(c for c in caps if c.name == "list_pets")
        param_names = {p.name for p in list_pets.parameters}
        assert "limit" in param_names
        assert "status" in param_names
        limit = next(p for p in list_pets.parameters if p.name == "limit")
        assert limit.type == "integer"
        assert limit.required is False

    def test_extracts_enum_values(self, petstore_spec):
        caps = openapi_to_capabilities(petstore_spec, "openapi.json")
        list_pets = next(c for c in caps if c.name == "list_pets")
        status = next(p for p in list_pets.parameters if p.name == "status")
        assert status.enum_values == ["available", "pending", "sold"]

    def test_extracts_path_params(self, petstore_spec):
        caps = openapi_to_capabilities(petstore_spec, "openapi.json")
        get_pet = next(c for c in caps if c.name == "get_pet")
        pet_id = next(p for p in get_pet.parameters if p.name == "petId")
        assert pet_id.required is True
        assert pet_id.type == "integer"

    def test_extracts_request_body_properties(self, petstore_spec):
        caps = openapi_to_capabilities(petstore_spec, "openapi.json")
        create_pet = next(c for c in caps if c.name == "create_pet")
        param_names = {p.name for p in create_pet.parameters}
        assert "name" in param_names
        assert "species" in param_names
        assert "age" in param_names
        name = next(p for p in create_pet.parameters if p.name == "name")
        assert name.required is True
        age = next(p for p in create_pet.parameters if p.name == "age")
        assert age.type == "integer"
        assert age.required is False

    def test_description_includes_http_method(self, petstore_spec):
        caps = openapi_to_capabilities(petstore_spec, "openapi.json")
        list_pets = next(c for c in caps if c.name == "list_pets")
        assert "GET" in list_pets.description
        assert "/pets" in list_pets.description

    def test_all_capabilities_are_api_protocol(self, petstore_spec):
        caps = openapi_to_capabilities(petstore_spec, "openapi.json")
        for cap in caps:
            assert cap.category == "api"
            assert cap.ipc_type == IPCType.PROTOCOL

    def test_server_info_extraction(self, petstore_spec):
        info = extract_server_info(petstore_spec)
        assert info["base_url"] == "http://localhost:8080/api/v1"
        assert info["port"] == "8080"


# ── Swagger 2.x Capability Extraction ──


class TestSwagger2Capabilities:
    @pytest.fixture
    def swagger_spec(self, fixtures_dir):
        return parse_openapi_spec(fixtures_dir / "petstore_swagger.yaml")

    def test_extracts_endpoints(self, swagger_spec):
        caps = openapi_to_capabilities(swagger_spec, "swagger.yaml")
        assert len(caps) == 4  # list, create, get, delete

    def test_uses_operation_id(self, swagger_spec):
        caps = openapi_to_capabilities(swagger_spec, "swagger.yaml")
        names = {c.name for c in caps}
        assert "listanimals" in names
        assert "createanimal" in names
        assert "getanimal" in names
        assert "deleteanimal" in names

    def test_swagger_base_path(self, swagger_spec):
        caps = openapi_to_capabilities(swagger_spec, "swagger.yaml")
        list_cap = next(c for c in caps if c.name == "listanimals")
        assert "/api/animals" in list_cap.description

    def test_swagger_body_params(self, swagger_spec):
        caps = openapi_to_capabilities(swagger_spec, "swagger.yaml")
        create = next(c for c in caps if c.name == "createanimal")
        param_names = {p.name for p in create.parameters}
        assert "name" in param_names
        assert "species" in param_names
        assert "weight" in param_names

    def test_swagger_server_info(self, swagger_spec):
        info = extract_server_info(swagger_spec)
        assert info["base_url"] == "http://localhost:9090/api"
        assert info["port"] == "9090"


# ── Security Scheme Extraction ──


class TestSecuritySchemes:
    def test_extracts_api_key_header(self):
        spec = {
            "openapi": "3.0.0",
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
        schemes = extract_security_schemes(spec)
        assert len(schemes) == 1
        assert schemes[0]["type"] == "api_key"
        assert schemes[0]["header"] == "X-API-Key"
        assert schemes[0]["location"] == "header"

    def test_extracts_api_key_query(self):
        spec = {
            "openapi": "3.0.0",
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
        schemes = extract_security_schemes(spec)
        assert len(schemes) == 1
        assert schemes[0]["type"] == "api_key"
        assert schemes[0]["location"] == "query"

    def test_extracts_bearer_token(self):
        spec = {
            "openapi": "3.0.0",
            "components": {
                "securitySchemes": {
                    "bearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                    }
                }
            },
        }
        schemes = extract_security_schemes(spec)
        assert len(schemes) == 1
        assert schemes[0]["type"] == "bearer"

    def test_extracts_basic_auth(self):
        spec = {
            "openapi": "3.0.0",
            "components": {
                "securitySchemes": {
                    "basicAuth": {
                        "type": "http",
                        "scheme": "basic",
                    }
                }
            },
        }
        schemes = extract_security_schemes(spec)
        assert len(schemes) == 1
        assert schemes[0]["type"] == "basic"

    def test_extracts_oauth2_as_bearer(self):
        spec = {
            "openapi": "3.0.0",
            "components": {
                "securitySchemes": {
                    "oauth2": {
                        "type": "oauth2",
                        "flows": {"clientCredentials": {"tokenUrl": "/token"}},
                    }
                }
            },
        }
        schemes = extract_security_schemes(spec)
        assert len(schemes) == 1
        assert schemes[0]["type"] == "bearer"

    def test_swagger2_security_definitions(self):
        spec = {
            "swagger": "2.0",
            "securityDefinitions": {
                "api_key": {
                    "type": "apiKey",
                    "name": "Authorization",
                    "in": "header",
                }
            },
        }
        schemes = extract_security_schemes(spec)
        assert len(schemes) == 1
        assert schemes[0]["type"] == "api_key"
        assert schemes[0]["header"] == "Authorization"

    def test_no_security_schemes(self):
        spec = {"openapi": "3.0.0", "paths": {}}
        schemes = extract_security_schemes(spec)
        assert schemes == []

    def test_multiple_schemes(self):
        spec = {
            "openapi": "3.0.0",
            "components": {
                "securitySchemes": {
                    "bearerAuth": {"type": "http", "scheme": "bearer"},
                    "apiKey": {"type": "apiKey", "name": "X-Key", "in": "header"},
                }
            },
        }
        schemes = extract_security_schemes(spec)
        assert len(schemes) == 2
        types = {s["type"] for s in schemes}
        assert "bearer" in types
        assert "api_key" in types
