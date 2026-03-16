"""Tests for URL-based spec fetching."""

import json
import textwrap
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from threading import Thread

import pytest
import yaml
from rich.console import Console

from mcp_anything.url_fetcher import (
    is_url,
    fetch_url,
    _derive_name_from_url,
    _detect_and_save,
    _resolve_spec_url,
)


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------


class TestIsUrl:
    def test_http(self):
        assert is_url("http://example.com/api") is True

    def test_https(self):
        assert is_url("https://api.example.com/openapi.json") is True

    def test_local_path(self):
        assert is_url("/home/user/project") is False
        assert is_url("./my-app") is False
        assert is_url("my-app") is False

    def test_ftp_not_supported(self):
        assert is_url("ftp://example.com/spec.json") is False


class TestDeriveNameFromUrl:
    def test_from_spec_title(self):
        spec = {"info": {"title": "Petstore API"}}
        assert _derive_name_from_url("https://example.com", spec) == "petstore_api"

    def test_from_hostname(self):
        assert _derive_name_from_url("https://api.stripe.com/v1/openapi.json") == "api"

    def test_from_hostname_no_subdomain(self):
        assert _derive_name_from_url("https://stripe.com/docs") == "stripe"

    def test_long_title_truncated(self):
        spec = {"info": {"title": "A" * 60 + " Very Long API Name"}}
        name = _derive_name_from_url("https://x.com", spec)
        assert len(name) <= 40

    def test_fallback_to_api(self):
        name = _derive_name_from_url("https:///weird-url", None)
        assert name == "api"


class TestDetectAndSave:
    def test_openapi_json(self, tmp_path):
        content = json.dumps({"openapi": "3.0.0", "info": {"title": "Test"}, "paths": {}})
        filename = _detect_and_save(content, "https://x.com/spec.json", tmp_path)
        assert filename == "openapi.json"
        assert (tmp_path / "openapi.json").exists()

    def test_swagger_json(self, tmp_path):
        content = json.dumps({"swagger": "2.0", "info": {"title": "Test"}, "paths": {}})
        filename = _detect_and_save(content, "https://x.com/api", tmp_path)
        assert filename == "swagger.json"

    def test_openapi_yaml(self, tmp_path):
        content = "openapi: '3.0.0'\ninfo:\n  title: Test\npaths: {}\n"
        filename = _detect_and_save(content, "https://x.com/spec.yaml", tmp_path)
        assert filename == "openapi.yaml"
        assert (tmp_path / "openapi.yaml").exists()

    def test_graphql_sdl(self, tmp_path):
        content = "type Query {\n  user(id: ID!): User\n}\n"
        filename = _detect_and_save(content, "https://x.com/schema", tmp_path)
        assert filename == "schema.graphql"

    def test_protobuf(self, tmp_path):
        content = 'syntax = "proto3";\nservice MyService {}\n'
        filename = _detect_and_save(content, "https://x.com/service", tmp_path)
        assert filename == "service.proto"

    def test_unknown_content(self, tmp_path):
        content = "<html><body>Not a spec</body></html>"
        filename = _detect_and_save(content, "https://x.com/page", tmp_path)
        assert filename is None

    def test_json_url_hint(self, tmp_path):
        content = json.dumps({"some": "data"})
        filename = _detect_and_save(content, "https://x.com/api/spec.json", tmp_path)
        assert filename == "spec.json"


class TestResolveSpecUrl:
    def test_swagger_ui(self):
        assert _resolve_spec_url("https://api.com/swagger-ui") == "https://api.com/v3/api-docs"

    def test_docs_page(self):
        assert _resolve_spec_url("https://api.com/docs") == "https://api.com/openapi.json"

    def test_redoc(self):
        assert _resolve_spec_url("https://api.com/redoc") == "https://api.com/openapi.json"

    def test_already_spec(self):
        url = "https://api.com/openapi.json"
        assert _resolve_spec_url(url) == url

    def test_passthrough(self):
        url = "https://api.com/v1/some-endpoint"
        assert _resolve_spec_url(url) == url


# ---------------------------------------------------------------------------
# Integration test with local HTTP server
# ---------------------------------------------------------------------------


PETSTORE_SPEC = {
    "openapi": "3.0.3",
    "info": {"title": "Petstore", "version": "1.0.0"},
    "paths": {
        "/pets": {
            "get": {
                "operationId": "listPets",
                "summary": "List all pets",
                "responses": {"200": {"description": "OK"}},
            },
            "post": {
                "operationId": "createPet",
                "summary": "Create a pet",
                "responses": {"201": {"description": "Created"}},
            },
        }
    },
}


class _SpecHandler(BaseHTTPRequestHandler):
    """Serves a petstore spec on any path."""

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(PETSTORE_SPEC).encode())

    def log_message(self, format, *args):
        pass  # suppress output


@pytest.fixture
def local_spec_server():
    """Start a local HTTP server serving a petstore spec."""
    server = HTTPServer(("127.0.0.1", 0), _SpecHandler)
    port = server.server_address[1]
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


class TestFetchUrl:
    def test_fetch_openapi_from_url(self, local_spec_server):
        console = Console(quiet=True)
        temp_dir, name = fetch_url(f"{local_spec_server}/openapi.json", console)

        try:
            assert temp_dir.is_dir()
            assert (temp_dir / "openapi.json").exists()

            spec = json.loads((temp_dir / "openapi.json").read_text())
            assert spec["openapi"] == "3.0.3"
            assert spec["info"]["title"] == "Petstore"
            assert name == "petstore"
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_fetch_bad_url(self):
        console = Console(quiet=True)
        with pytest.raises(RuntimeError, match="Failed to fetch"):
            fetch_url("http://127.0.0.1:1/nonexistent", console)


class TestFetchUrlPipeline:
    """End-to-end: fetch from URL → run pipeline → verify output."""

    @pytest.mark.asyncio
    async def test_url_to_mcp_server(self, local_spec_server, tmp_output):
        from mcp_anything.config import CLIOptions
        from mcp_anything.models.manifest import GenerationManifest
        from mcp_anything.pipeline.engine import PipelineEngine

        console = Console(quiet=True)
        temp_dir, name = fetch_url(f"{local_spec_server}/openapi.json", console)

        try:
            options = CLIOptions(
                codebase_path=temp_dir,
                output_dir=tmp_output,
                name=name,
                source_url=f"{local_spec_server}/openapi.json",
                no_llm=True,
                no_install=True,
            )
            engine = PipelineEngine(options, console)
            await engine.run()

            manifest = GenerationManifest.load(tmp_output / "mcp-anything-manifest.json")
            assert manifest.completed_phases == [
                "analyze", "design", "implement", "test", "document", "package"
            ]
            assert manifest.errors == []

            # Verify tools were generated from the fetched spec
            tool_names = {t.name for t in manifest.design.tools}
            assert len(tool_names) >= 2
            assert any("pet" in n for n in tool_names), f"Expected pet tools, got: {tool_names}"

            # Verify generated files
            pkg_name = f"mcp_{name.replace('-', '_')}"
            assert (tmp_output / "src" / pkg_name / "server.py").exists()
            assert (tmp_output / "pyproject.toml").exists()
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
