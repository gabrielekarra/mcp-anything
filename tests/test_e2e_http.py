"""End-to-end test: generated MCP server calls a real HTTP backend.

Verifies the full round-trip:
  1. Generate an MCP server from a Flask fixture
  2. Start a mock HTTP server
  3. Import the generated server module
  4. Call a tool programmatically
  5. Assert the mock received the correct HTTP request and the tool returned the response
"""

import asyncio
import importlib
import json
import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

import pytest
from rich.console import Console

from mcp_anything.config import CLIOptions
from mcp_anything.pipeline.engine import PipelineEngine


# ---------------------------------------------------------------------------
# Mock HTTP server
# ---------------------------------------------------------------------------

class _RequestLog:
    """Thread-safe log of received HTTP requests."""

    def __init__(self):
        self.requests: list[dict] = []
        self._lock = threading.Lock()

    def record(self, method: str, path: str, headers: dict, body: str):
        with self._lock:
            self.requests.append({
                "method": method,
                "path": path,
                "headers": headers,
                "body": body,
            })

    @property
    def last(self) -> dict:
        with self._lock:
            return self.requests[-1]


def _make_handler(log: _RequestLog, routes: dict):
    """Create an HTTP handler that logs requests and returns canned responses."""

    class Handler(BaseHTTPRequestHandler):
        def _handle(self):
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode() if content_length else ""
            log.record(self.command, self.path, dict(self.headers), body)

            # Strip query string for route lookup
            path_no_qs = self.path.split("?")[0]
            key = (self.command, path_no_qs)
            if key in routes:
                response = routes[key]
            else:
                response = {"error": "not found"}
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
                return

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())

        do_GET = _handle
        do_POST = _handle
        do_PUT = _handle
        do_DELETE = _handle
        do_PATCH = _handle

        def log_message(self, *_args):
            pass  # suppress stderr

    return Handler


@pytest.fixture
def mock_http_server():
    """Start a mock HTTP server on a random port and yield (port, log, routes)."""
    routes: dict[tuple[str, str], dict] = {}
    log = _RequestLog()
    handler_class = _make_handler(log, routes)
    server = HTTPServer(("127.0.0.1", 0), handler_class)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield port, log, routes
    server.shutdown()


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------

class TestE2EHTTP:
    """End-to-end test: generated server calls a mock HTTP backend."""

    @pytest.mark.asyncio
    async def test_generated_server_calls_backend(
        self, fake_flask_app, tmp_path, mock_http_server
    ):
        port, log, routes = mock_http_server

        # Register mock routes
        routes[("GET", "/users")] = {"users": [{"id": 1, "name": "Alice"}]}
        routes[("POST", "/users")] = {"id": 2, "name": "Bob"}
        routes[("GET", "/health")] = {"status": "ok"}

        # 1. Generate MCP server from the Flask fixture
        output_dir = tmp_path / "output"
        options = CLIOptions(
            codebase_path=fake_flask_app,
            output_dir=output_dir,
            name="e2e-test",
            no_llm=True,
            no_install=True,
            transport="stdio",
        )
        console = Console(quiet=True)
        engine = PipelineEngine(options, console)
        await engine.run()

        # 2. Verify generation succeeded
        pkg_name = "mcp_e2e_test"
        src_path = str(output_dir / "src")
        assert (output_dir / "src" / pkg_name / "server.py").exists()

        # Verify mcp.json has BASE_URL placeholder
        mcp_json = json.loads((output_dir / "mcp.json").read_text())
        server_config = mcp_json["mcpServers"]["e2e-test"]
        assert "env" in server_config
        assert "E2E_TEST_BASE_URL" in server_config["env"]

        # 3. Set BASE_URL and import the generated server
        os.environ["E2E_TEST_BASE_URL"] = f"http://127.0.0.1:{port}"
        original_path = sys.path.copy()
        try:
            sys.path.insert(0, src_path)
            server_mod = importlib.import_module(f"{pkg_name}.server")
            mcp_server = server_mod.server

            # 4. Call the get_users tool
            result = await mcp_server.call_tool("get_users", {})
            # FastMCP returns (content_list, metadata) tuple
            content_list = result[0] if isinstance(result, tuple) else result
            assert len(content_list) > 0
            response_text = content_list[0].text
            parsed = json.loads(response_text)
            assert parsed == {"users": [{"id": 1, "name": "Alice"}]}

            # 5. Verify the mock received the correct request
            assert log.last["method"] == "GET"
            assert log.last["path"] == "/users"

            # 6. Call health check tool
            result = await mcp_server.call_tool("get_health", {})
            content_list = result[0] if isinstance(result, tuple) else result
            response_text = content_list[0].text
            parsed = json.loads(response_text)
            assert parsed == {"status": "ok"}
            assert log.last["method"] == "GET"
            assert log.last["path"] == "/health"

        finally:
            os.environ.pop("E2E_TEST_BASE_URL", None)
            sys.path[:] = original_path
            to_remove = [k for k in sys.modules if k.startswith(pkg_name)]
            for k in to_remove:
                del sys.modules[k]
