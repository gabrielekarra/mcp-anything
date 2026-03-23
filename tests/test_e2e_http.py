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


# ---------------------------------------------------------------------------
# E2E: CLI backend actually spawns a subprocess
# ---------------------------------------------------------------------------

class TestE2ECLI:
    """End-to-end test: generated CLI backend spawns a real subprocess."""

    @pytest.mark.asyncio
    async def test_cli_backend_runs_subprocess(self, fake_cli_app, tmp_path):
        """Generate a CLI server from the argparse fixture, instantiate the real
        backend, call run_subcommand('status', []), and verify we get real output."""
        import importlib
        import sys as _sys
        import os as _os

        output_dir = tmp_path / "output"
        options = CLIOptions(
            codebase_path=fake_cli_app,
            output_dir=output_dir,
            name="cli-e2e",
            no_llm=True,
            no_install=True,
            transport="stdio",
        )
        console = Console(quiet=True)
        await PipelineEngine(options, console).run()

        pkg_name = "mcp_cli_e2e"
        src_path = str(output_dir / "src")
        _sys.path.insert(0, src_path)
        try:
            backend_mod = importlib.import_module(f"{pkg_name}.backend")
            backend = backend_mod.Backend()
            # run_subcommand("status", []) calls the real CLI script
            result = await backend.run_subcommand("status", [])
            parsed = json.loads(result)
            assert parsed.get("status") == "running", f"Unexpected output: {result}"
        finally:
            _sys.path.remove(src_path)
            to_remove = [k for k in _sys.modules if k.startswith(pkg_name)]
            for k in to_remove:
                del _sys.modules[k]


# ---------------------------------------------------------------------------
# E2E: WebSocket backend connects to a real WebSocket server
# ---------------------------------------------------------------------------

class TestE2EWebSocket:
    """End-to-end test: generated WebSocket backend connects to a real WS server."""

    @pytest.mark.asyncio
    async def test_websocket_backend_connects_and_calls(
        self, fake_websocket_app, tmp_path
    ):
        """Start a real JSON-RPC WebSocket server, generate the MCP server,
        instantiate the real backend, call execute(), and verify the round-trip."""
        import importlib
        import sys as _sys
        import asyncio as _asyncio

        try:
            import websockets  # noqa: F401
            try:
                from websockets.asyncio.server import serve as _ws_serve
            except ImportError:
                from websockets import serve as _ws_serve  # type: ignore[no-redef]
        except ImportError:
            pytest.skip("websockets library not installed")

        # 1. Start a real JSON-RPC WebSocket server on a random port
        messages_received: list[dict] = []

        async def ws_handler(websocket):
            async for raw in websocket:
                data = json.loads(raw)
                messages_received.append(data)
                response = {"jsonrpc": "2.0", "result": {"echo": data.get("params", {})}, "id": data.get("id")}
                await websocket.send(json.dumps(response))

        # Find free port
        import socket
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]

        server = await websockets.serve(ws_handler, "127.0.0.1", port)

        try:
            # 2. Generate MCP server from the WebSocket fixture
            output_dir = tmp_path / "output"
            options = CLIOptions(
                codebase_path=fake_websocket_app,
                output_dir=output_dir,
                name="ws-e2e",
                no_llm=True,
                no_install=True,
                transport="stdio",
            )
            await PipelineEngine(options, Console(quiet=True)).run()

            pkg_name = "mcp_ws_e2e"
            src_path = str(output_dir / "src")
            _sys.path.insert(0, src_path)
            try:
                backend_mod = importlib.import_module(f"{pkg_name}.backend")
                backend = backend_mod.Backend()
                # Override WS URL to point to our test server
                backend.url = f"ws://127.0.0.1:{port}"

                # 3. Call execute() — should send JSON-RPC to our server
                result = await backend.execute("chat_endpoint", websocket="hello")
                parsed = json.loads(result)
                assert "echo" in parsed, f"Unexpected response: {result}"

                # 4. Verify the server received a well-formed JSON-RPC message
                assert len(messages_received) == 1
                msg = messages_received[0]
                assert msg.get("jsonrpc") == "2.0"
                assert msg.get("method") == "chat_endpoint"
                assert msg.get("params", {}).get("websocket") == "hello"

                await backend.disconnect()

            finally:
                _sys.path.remove(src_path)
                to_remove = [k for k in _sys.modules if k.startswith(pkg_name)]
                for k in to_remove:
                    del _sys.modules[k]

        finally:
            server.close()
            await server.wait_closed()


# ---------------------------------------------------------------------------
# E2E: gRPC backend calls a real gRPC server
# ---------------------------------------------------------------------------

class TestE2EgRPC:
    """End-to-end test: generated gRPC backend calls a real gRPC server."""

    @pytest.mark.asyncio
    async def test_grpc_backend_calls_real_server(self, fake_grpc_app, tmp_path):
        """Compile the proto stubs, start a real gRPC server, generate the MCP
        server, call execute('user_service_list_users'), verify the response."""
        import importlib
        import sys as _sys

        try:
            import grpc
            import grpc.aio
            from grpc_tools import protoc
        except ImportError:
            pytest.skip("grpcio / grpcio-tools not installed")

        # 1. Compile the proto for the test server (separate tmp dir)
        proto_dir = tmp_path / "proto_compiled"
        proto_dir.mkdir()
        proto_file = fake_grpc_app / "user.proto"
        ret = protoc.main([
            "grpc_tools.protoc",
            f"--proto_path={fake_grpc_app}",
            f"--python_out={proto_dir}",
            f"--grpc_python_out={proto_dir}",
            str(proto_file),
        ])
        assert ret == 0, "Proto compilation failed"
        _sys.path.insert(0, str(proto_dir))

        try:
            import user_pb2
            import user_pb2_grpc

            # 2. Implement a minimal UserService server
            class UserServiceServicer(user_pb2_grpc.UserServiceServicer):
                async def ListUsers(self, request, context):
                    user = user_pb2.User(id="1", name="Alice", email="alice@example.com", age=30)
                    return user_pb2.ListUsersResponse(users=[user])

                async def GetUser(self, request, context):
                    return user_pb2.User(id=request.id, name="Bob", email="bob@example.com", age=25)

            # 3. Start the gRPC server on a random port
            import socket
            with socket.socket() as s:
                s.bind(("127.0.0.1", 0))
                grpc_port = s.getsockname()[1]

            grpc_server = grpc.aio.server()
            user_pb2_grpc.add_UserServiceServicer_to_server(UserServiceServicer(), grpc_server)
            grpc_server.add_insecure_port(f"127.0.0.1:{grpc_port}")
            await grpc_server.start()

            try:
                # 4. Generate the MCP server (with proto compilation)
                output_dir = tmp_path / "output"
                options = CLIOptions(
                    codebase_path=fake_grpc_app,
                    output_dir=output_dir,
                    name="grpc-e2e",
                    no_llm=True,
                    no_install=True,
                    transport="stdio",
                )
                await PipelineEngine(options, Console(quiet=True)).run()

                pkg_name = "mcp_grpc_e2e"
                src_path = str(output_dir / "src")
                _sys.path.insert(0, src_path)
                try:
                    import importlib as _il
                    backend_mod = _il.import_module(f"{pkg_name}.backend")
                    backend = backend_mod.Backend()
                    backend.host = "127.0.0.1"
                    backend.port = grpc_port

                    # 5. Call list_users
                    result = await backend.execute("user_service_list_users")
                    parsed = json.loads(result)
                    # Should have a "users" key with at least one entry
                    users = parsed.get("users", [])
                    assert len(users) >= 1, f"Expected users in response, got: {parsed}"
                    assert users[0].get("name") == "Alice"

                finally:
                    _sys.path.remove(src_path)
                    to_remove = [k for k in _sys.modules if k.startswith(pkg_name)]
                    for k in to_remove:
                        del _sys.modules[k]

            finally:
                await grpc_server.stop(grace=0)

        finally:
            _sys.path.remove(str(proto_dir))
            for mod_name in ["user_pb2", "user_pb2_grpc"]:
                _sys.modules.pop(mod_name, None)
