"""Tests for Flask/FastAPI detection and analysis."""

from pathlib import Path

import pytest

from mcp_anything.analysis.detectors.flask_fastapi_detector import FlaskFastAPIDetector
from mcp_anything.analysis.flask_fastapi_analyzer import (
    analyze_flask_fastapi_file,
    flask_fastapi_results_to_capabilities,
)
from mcp_anything.analysis.scanner import scan_codebase
from mcp_anything.models.analysis import FileInfo, IPCType, Language


# ── Detector Tests ──


class TestFlaskFastAPIDetector:
    def test_detects_fastapi(self, fake_fastapi_app):
        files = scan_codebase(fake_fastapi_app)
        detector = FlaskFastAPIDetector()
        mechs = detector.detect(fake_fastapi_app, files)
        assert len(mechs) == 1
        assert mechs[0].ipc_type == IPCType.PROTOCOL
        assert mechs[0].details["framework"] == "fastapi"
        assert mechs[0].details["protocol"] == "http"
        assert mechs[0].confidence >= 0.9

    def test_detects_flask(self, fake_flask_app):
        files = scan_codebase(fake_flask_app)
        detector = FlaskFastAPIDetector()
        mechs = detector.detect(fake_flask_app, files)
        assert len(mechs) == 1
        assert mechs[0].details["framework"] == "flask"
        assert mechs[0].details["port"] == "5000"

    def test_no_detection_on_plain_python(self, fake_cli_app):
        files = scan_codebase(fake_cli_app)
        detector = FlaskFastAPIDetector()
        mechs = detector.detect(fake_cli_app, files)
        assert mechs == []

    def test_extracts_port_from_uvicorn(self, tmp_path):
        (tmp_path / "main.py").write_text(
            'from fastapi import FastAPI\n'
            'app = FastAPI()\n'
            'import uvicorn\n'
            'uvicorn.run(app, port=9000)\n'
        )
        files = scan_codebase(tmp_path)
        detector = FlaskFastAPIDetector()
        mechs = detector.detect(tmp_path, files)
        assert len(mechs) == 1
        assert mechs[0].details["port"] == "9000"


# ── FastAPI Analyzer Tests ──


class TestFastAPIAnalyzer:
    def test_extracts_routes(self, fake_fastapi_app):
        fi = FileInfo(path="main.py", language=Language.PYTHON, size_bytes=0, line_count=0)
        result = analyze_flask_fastapi_file(fake_fastapi_app, fi)
        assert result is not None
        assert result.framework == "fastapi"
        assert len(result.routes) == 6  # list, get, create, update, delete, health

    def test_extracts_get_with_query_params(self, fake_fastapi_app):
        fi = FileInfo(path="main.py", language=Language.PYTHON, size_bytes=0, line_count=0)
        result = analyze_flask_fastapi_file(fake_fastapi_app, fi)
        list_route = next(r for r in result.routes if r.function_name == "list_users")
        assert list_route.http_method == "GET"
        assert list_route.path == "/users"
        # skip and limit params with Query() defaults
        param_names = {p.name for p in list_route.parameters}
        assert "skip" in param_names
        assert "limit" in param_names
        skip = next(p for p in list_route.parameters if p.name == "skip")
        assert skip.type == "integer"
        assert skip.description == "Number of users to skip"

    def test_extracts_path_params(self, fake_fastapi_app):
        fi = FileInfo(path="main.py", language=Language.PYTHON, size_bytes=0, line_count=0)
        result = analyze_flask_fastapi_file(fake_fastapi_app, fi)
        get_route = next(r for r in result.routes if r.function_name == "get_user")
        assert get_route.http_method == "GET"
        assert get_route.path == "/users/{user_id}"
        user_id_param = next(p for p in get_route.parameters if p.name == "user_id")
        assert user_id_param.required is True
        assert user_id_param.type == "integer"

    def test_extracts_post_with_body(self, fake_fastapi_app):
        fi = FileInfo(path="main.py", language=Language.PYTHON, size_bytes=0, line_count=0)
        result = analyze_flask_fastapi_file(fake_fastapi_app, fi)
        create_route = next(r for r in result.routes if r.function_name == "create_user")
        assert create_route.http_method == "POST"
        # Pydantic model param → object type
        user_param = next(p for p in create_route.parameters if p.name == "user")
        assert user_param.type == "object"

    def test_extracts_delete(self, fake_fastapi_app):
        fi = FileInfo(path="main.py", language=Language.PYTHON, size_bytes=0, line_count=0)
        result = analyze_flask_fastapi_file(fake_fastapi_app, fi)
        delete_route = next(r for r in result.routes if r.function_name == "delete_user")
        assert delete_route.http_method == "DELETE"

    def test_extracts_router_routes(self, fake_fastapi_app):
        fi = FileInfo(path="routers.py", language=Language.PYTHON, size_bytes=0, line_count=0)
        result = analyze_flask_fastapi_file(fake_fastapi_app, fi)
        assert result is not None
        assert result.has_routers is True
        assert len(result.routes) == 2  # list_items, create_item

    def test_router_prefix_included(self, tmp_path):
        (tmp_path / "routes.py").write_text(
            'from fastapi import APIRouter\n'
            'router = APIRouter(prefix="/items")\n'
            '@router.get("/")\n'
            'async def list_items():\n'
            '    """List items."""\n'
            '    return []\n'
            '@router.get("/{item_id}")\n'
            'async def get_item(item_id: int):\n'
            '    """Get item."""\n'
            '    return {}\n'
        )
        fi = FileInfo(path="routes.py", language=Language.PYTHON, size_bytes=0, line_count=0)
        result = analyze_flask_fastapi_file(tmp_path, fi)
        assert result is not None
        paths = {r.path for r in result.routes}
        assert "/items/" in paths
        assert "/items/{item_id}" in paths

    def test_description_from_docstring(self, fake_fastapi_app):
        fi = FileInfo(path="main.py", language=Language.PYTHON, size_bytes=0, line_count=0)
        result = analyze_flask_fastapi_file(fake_fastapi_app, fi)
        health_route = next(r for r in result.routes if r.function_name == "health_check")
        assert health_route.description == "Health check endpoint."


# ── Flask Analyzer Tests ──


class TestFlaskAnalyzer:
    def test_extracts_flask_routes(self, fake_flask_app):
        fi = FileInfo(path="app.py", language=Language.PYTHON, size_bytes=0, line_count=0)
        result = analyze_flask_fastapi_file(fake_flask_app, fi)
        assert result is not None
        assert result.framework == "flask"
        assert len(result.routes) == 5  # list, get, create, delete, health

    def test_flask_path_params(self, fake_flask_app):
        fi = FileInfo(path="app.py", language=Language.PYTHON, size_bytes=0, line_count=0)
        result = analyze_flask_fastapi_file(fake_flask_app, fi)
        get_route = next(r for r in result.routes if r.function_name == "get_user")
        assert get_route.http_method == "GET"
        # Flask <int:user_id> normalized to {user_id}
        assert get_route.path == "/users/{user_id}"
        assert len(get_route.parameters) == 1
        assert get_route.parameters[0].name == "user_id"
        assert get_route.parameters[0].required is True

    def test_flask_methods_kwarg(self, fake_flask_app):
        fi = FileInfo(path="app.py", language=Language.PYTHON, size_bytes=0, line_count=0)
        result = analyze_flask_fastapi_file(fake_flask_app, fi)
        create_route = next(r for r in result.routes if r.function_name == "create_user")
        assert create_route.http_method == "POST"

    def test_flask_default_get(self, fake_flask_app):
        fi = FileInfo(path="app.py", language=Language.PYTHON, size_bytes=0, line_count=0)
        result = analyze_flask_fastapi_file(fake_flask_app, fi)
        health_route = next(r for r in result.routes if r.function_name == "health")
        assert health_route.http_method == "GET"


# ── Capability Conversion Tests ──


class TestCapabilityConversion:
    def test_converts_to_capabilities(self, fake_fastapi_app):
        fi = FileInfo(path="main.py", language=Language.PYTHON, size_bytes=0, line_count=0)
        result = analyze_flask_fastapi_file(fake_fastapi_app, fi)
        caps = flask_fastapi_results_to_capabilities({"main.py": result})
        assert len(caps) >= 5
        # All should have category="api" and ipc_type=PROTOCOL
        for cap in caps:
            assert cap.category == "api"
            assert cap.ipc_type == IPCType.PROTOCOL

    def test_tool_names_are_correct(self, fake_fastapi_app):
        fi = FileInfo(path="main.py", language=Language.PYTHON, size_bytes=0, line_count=0)
        result = analyze_flask_fastapi_file(fake_fastapi_app, fi)
        caps = flask_fastapi_results_to_capabilities({"main.py": result})
        names = {c.name for c in caps}
        assert "get_users" in names
        assert "get_users_by_user_id" in names
        assert "post_users" in names
        assert "delete_users_by_user_id" in names

    def test_description_includes_http_method(self, fake_fastapi_app):
        fi = FileInfo(path="main.py", language=Language.PYTHON, size_bytes=0, line_count=0)
        result = analyze_flask_fastapi_file(fake_fastapi_app, fi)
        caps = flask_fastapi_results_to_capabilities({"main.py": result})
        get_users = next(c for c in caps if c.name == "get_users")
        assert get_users.description.startswith("GET /users")

    def test_skips_depends_params(self, tmp_path):
        (tmp_path / "app.py").write_text(
            'from fastapi import FastAPI, Depends\n'
            'app = FastAPI()\n'
            'def get_db(): pass\n'
            '@app.get("/users")\n'
            'async def list_users(db = Depends(get_db), skip: int = 0):\n'
            '    return []\n'
        )
        fi = FileInfo(path="app.py", language=Language.PYTHON, size_bytes=0, line_count=0)
        result = analyze_flask_fastapi_file(tmp_path, fi)
        route = result.routes[0]
        param_names = {p.name for p in route.parameters}
        assert "db" not in param_names
        assert "skip" in param_names

    def test_no_duplicate_tools(self, fake_fastapi_app):
        fi = FileInfo(path="main.py", language=Language.PYTHON, size_bytes=0, line_count=0)
        result = analyze_flask_fastapi_file(fake_fastapi_app, fi)
        caps = flask_fastapi_results_to_capabilities({"main.py": result})
        names = [c.name for c in caps]
        assert len(names) == len(set(names))
