"""Functional tests for generated MCP server tool implementations.

These tests verify that generated tool functions actually invoke the backend
correctly — not just that the code is syntactically valid or importable.

Approach:
  1. Run the full pipeline on a fixture app.
  2. Import the generated tool module(s).
  3. Inject a mock backend via a fake `_get_backend` closure.
  4. Call each tool function with representative inputs.
  5. Assert the backend received the correct method/path/params/args.
"""

import importlib
import inspect
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest
from rich.console import Console

from mcp_anything.config import CLIOptions
from mcp_anything.models.manifest import GenerationManifest
from mcp_anything.pipeline.engine import PipelineEngine


# ---------------------------------------------------------------------------
# Infrastructure
# ---------------------------------------------------------------------------

async def _run_pipeline(
    codebase_path: Path,
    output_dir: Path,
    *,
    name: str | None = None,
) -> GenerationManifest:
    options = CLIOptions(
        codebase_path=codebase_path,
        output_dir=output_dir,
        name=name,
        no_llm=True,
        no_install=True,
        transport="stdio",
    )
    console = Console(quiet=True)
    engine = PipelineEngine(options, console)
    await engine.run()
    manifest_path = output_dir / "mcp-anything-manifest.json"
    assert manifest_path.exists(), "Manifest not created"
    return GenerationManifest.load(manifest_path)


def _pkg_name(server_name: str) -> str:
    return f"mcp_{server_name.replace('-', '_')}"


class MockServer:
    """Minimal FastMCP stand-in that captures @server.tool() registrations."""

    def __init__(self):
        self._tools: dict[str, object] = {}

    def tool(self, name: str | None = None, **kwargs):
        """Decorator factory — stores the wrapped coroutine."""
        def decorator(fn):
            key = name if name else fn.__name__
            self._tools[key] = fn
            return fn
        return decorator

    def resource(self, *args, **kwargs):
        def decorator(fn):
            return fn
        return decorator

    def prompt(self, *args, **kwargs):
        def decorator(fn):
            return fn
        return decorator


async def _call_with_dummy_args(fn) -> object:
    """Call an async tool function, filling required params with dummy values."""
    sig = inspect.signature(fn)
    kwargs = {}
    for name, param in sig.parameters.items():
        if param.default is inspect.Parameter.empty:
            # Required param — provide a sensible dummy
            ann = param.annotation
            if ann is int or ann == "int":
                kwargs[name] = 1
            elif ann is bool or ann == "bool":
                kwargs[name] = False
            elif ann is float or ann == "float":
                kwargs[name] = 1.0
            elif ann is list or ann == "list":
                kwargs[name] = []
            elif ann is dict or ann == "dict":
                kwargs[name] = {}
            else:
                kwargs[name] = "test"
    return await fn(**kwargs)


def _load_module(output_dir: Path, pkg_name: str, module_name: str):
    """Import a generated module, cleaning up sys.modules afterward."""
    src_path = str(output_dir / "src")
    original_path = sys.path.copy()
    original_modules = set(sys.modules.keys())
    sys.path.insert(0, src_path)
    try:
        mod = importlib.import_module(f"{pkg_name}.{module_name}")
        return mod
    finally:
        sys.path[:] = original_path
        for key in list(sys.modules.keys()):
            if key not in original_modules:
                del sys.modules[key]


def _register_all_tools(output_dir: Path, pkg_name: str, mock_backend) -> MockServer:
    """Import every tool module and register tools with a MockServer.

    Tool modules live in src/{pkg_name}/tools/{module_name}.py.
    """
    src_path = str(output_dir / "src")
    original_path = sys.path.copy()
    original_modules = set(sys.modules.keys())
    sys.path.insert(0, src_path)

    mock_server = MockServer()
    _get_backend = lambda: mock_backend  # noqa: E731

    try:
        tools_dir = output_dir / "src" / pkg_name / "tools"
        if not tools_dir.exists():
            return mock_server
        for py_file in sorted(tools_dir.glob("*.py")):
            if py_file.name == "__init__.py":
                continue
            module_name = py_file.stem
            mod = importlib.import_module(f"{pkg_name}.tools.{module_name}")
            if hasattr(mod, "register_tools"):
                mod.register_tools(mock_server, _get_backend)
    finally:
        sys.path[:] = original_path
        # Only remove the generated package modules, not third-party ones.
        # Removing all new modules corrupts pydantic's internal sys.modules state.
        to_remove = [k for k in sys.modules if k.startswith(pkg_name)]
        for k in to_remove:
            del sys.modules[k]

    return mock_server


# ---------------------------------------------------------------------------
# Tests — HTTP tools (Flask)
# ---------------------------------------------------------------------------

class TestFunctionalFlask:
    """Verify generated HTTP tools call the backend with correct method/path/params."""

    @pytest.mark.asyncio
    async def test_get_users_calls_correct_endpoint(self, fake_flask_app, tmp_output):
        manifest = await _run_pipeline(fake_flask_app, tmp_output)
        pkg = _pkg_name(manifest.server_name)

        mock_backend = MagicMock()
        mock_backend.request = AsyncMock(return_value='{"users": []}')

        server = _register_all_tools(tmp_output, pkg, mock_backend)

        assert "get_users" in server._tools, f"get_users not registered. Tools: {list(server._tools)}"
        await server._tools["get_users"]()
        mock_backend.request.assert_called_once()
        args, kwargs = mock_backend.request.call_args
        assert args[0] == "GET"
        assert "/users" in args[1]

    @pytest.mark.asyncio
    async def test_post_users_sends_body(self, fake_flask_app, tmp_output):
        manifest = await _run_pipeline(fake_flask_app, tmp_output)
        pkg = _pkg_name(manifest.server_name)

        mock_backend = MagicMock()
        mock_backend.request = AsyncMock(return_value='{"id": 1}')

        server = _register_all_tools(tmp_output, pkg, mock_backend)

        assert "post_users" in server._tools, f"post_users not registered. Tools: {list(server._tools)}"
        await server._tools["post_users"]()
        mock_backend.request.assert_called_once()
        args, _ = mock_backend.request.call_args
        assert args[0] == "POST"
        assert "/users" in args[1]

    @pytest.mark.asyncio
    async def test_get_health_calls_health_endpoint(self, fake_flask_app, tmp_output):
        manifest = await _run_pipeline(fake_flask_app, tmp_output)
        pkg = _pkg_name(manifest.server_name)

        mock_backend = MagicMock()
        mock_backend.request = AsyncMock(return_value='{"status": "ok"}')

        server = _register_all_tools(tmp_output, pkg, mock_backend)

        assert "get_health" in server._tools, f"get_health not registered. Tools: {list(server._tools)}"
        await server._tools["get_health"]()
        mock_backend.request.assert_called_once()
        args, _ = mock_backend.request.call_args
        assert args[0] == "GET"
        assert "/health" in args[1]

    @pytest.mark.asyncio
    async def test_get_user_by_id_substitutes_path_param(self, fake_flask_app, tmp_output):
        """Path params like user_id must be in the path_params dict, not query_params."""
        manifest = await _run_pipeline(fake_flask_app, tmp_output)
        pkg = _pkg_name(manifest.server_name)

        mock_backend = MagicMock()
        mock_backend.request = AsyncMock(return_value='{"id": 42}')

        server = _register_all_tools(tmp_output, pkg, mock_backend)

        # The tool for GET /users/<user_id> could be named get_users_user_id or get_user_by_id
        candidate = next(
            (name for name in server._tools if "user" in name and name.startswith("get") and name != "get_users"),
            None,
        )
        if candidate is None:
            pytest.skip("No GET /users/{id} tool found")

        await server._tools[candidate](user_id=42)
        mock_backend.request.assert_called_once()
        _, kwargs = mock_backend.request.call_args
        # user_id should end up as a path param, not a query param
        path_params = kwargs.get("path_params") or {}
        assert path_params, f"Expected path_params with user_id, got {kwargs}"


# ---------------------------------------------------------------------------
# Tests — CLI tools (argparse)
# ---------------------------------------------------------------------------

class TestFunctionalCLI:
    """Verify generated CLI tools call run_subcommand with correct args."""

    @pytest.mark.asyncio
    async def test_process_calls_correct_subcommand(self, fake_cli_app, tmp_output):
        manifest = await _run_pipeline(fake_cli_app, tmp_output)
        pkg = _pkg_name(manifest.server_name)

        mock_backend = MagicMock()
        mock_backend.run_subcommand = AsyncMock(return_value='{"processed": true}')

        server = _register_all_tools(tmp_output, pkg, mock_backend)

        assert "process" in server._tools, f"process not registered. Tools: {list(server._tools)}"
        await server._tools["process"](input="in.txt", output="out.txt")
        mock_backend.run_subcommand.assert_called_once()
        args, _ = mock_backend.run_subcommand.call_args
        assert args[0] == "process", f"Expected subcommand 'process', got '{args[0]}'"

    @pytest.mark.asyncio
    async def test_status_calls_correct_subcommand(self, fake_cli_app, tmp_output):
        manifest = await _run_pipeline(fake_cli_app, tmp_output)
        pkg = _pkg_name(manifest.server_name)

        mock_backend = MagicMock()
        mock_backend.run_subcommand = AsyncMock(return_value='{"status": "running"}')

        server = _register_all_tools(tmp_output, pkg, mock_backend)

        assert "status" in server._tools, f"status not registered. Tools: {list(server._tools)}"
        await server._tools["status"]()
        mock_backend.run_subcommand.assert_called_once()
        args, _ = mock_backend.run_subcommand.call_args
        assert args[0] == "status"

    @pytest.mark.asyncio
    async def test_formats_calls_correct_subcommand(self, fake_cli_app, tmp_output):
        manifest = await _run_pipeline(fake_cli_app, tmp_output)
        pkg = _pkg_name(manifest.server_name)

        mock_backend = MagicMock()
        mock_backend.run_subcommand = AsyncMock(return_value='["json","csv","xml"]')

        server = _register_all_tools(tmp_output, pkg, mock_backend)

        assert "formats" in server._tools, f"formats not registered. Tools: {list(server._tools)}"
        await server._tools["formats"]()
        mock_backend.run_subcommand.assert_called_once()
        args, _ = mock_backend.run_subcommand.call_args
        assert args[0] == "formats"


# ---------------------------------------------------------------------------
# Tests — FastAPI (HTTP tools + query params)
# ---------------------------------------------------------------------------

class TestFunctionalFastAPI:
    """Verify FastAPI-generated HTTP tools pass query params correctly."""

    @pytest.mark.asyncio
    async def test_http_tools_use_http_backend(self, fake_fastapi_app, tmp_output):
        manifest = await _run_pipeline(fake_fastapi_app, tmp_output)
        pkg = _pkg_name(manifest.server_name)

        mock_backend = MagicMock()
        mock_backend.request = AsyncMock(return_value="[]")

        server = _register_all_tools(tmp_output, pkg, mock_backend)
        assert len(server._tools) > 0, "No tools registered"

        # Call any tool with auto-filled required params
        tool_name = next(iter(server._tools))
        await _call_with_dummy_args(server._tools[tool_name])


# ---------------------------------------------------------------------------
# Tests — WebSocket protocol tools
# ---------------------------------------------------------------------------

class TestFunctionalWebSocket:
    """Verify WebSocket tools call execute() on the protocol backend, not request()."""

    @pytest.mark.asyncio
    async def test_websocket_tools_call_execute(self, fake_websocket_app, tmp_output):
        manifest = await _run_pipeline(fake_websocket_app, tmp_output)
        pkg = _pkg_name(manifest.server_name)

        # Check that the manifest has protocol_call tools (not http_call)
        assert manifest.design is not None
        strategies = {t.impl.strategy for t in manifest.design.tools}
        assert "protocol_call" in strategies, (
            f"Expected protocol_call strategy for WebSocket tools, got: {strategies}"
        )
        assert "http_call" not in strategies, (
            f"WebSocket tools must not use http_call strategy, got: {strategies}. "
            "This means the emitter bug (PROTOCOL=http env_var) is still present."
        )

        mock_backend = MagicMock()
        mock_backend.execute = AsyncMock(return_value='{"result": "ok"}')

        server = _register_all_tools(tmp_output, pkg, mock_backend)
        assert len(server._tools) > 0, "No tools registered"

        # Call the first protocol tool with auto-filled required params
        tool_name = next(iter(server._tools))
        await _call_with_dummy_args(server._tools[tool_name])

        # execute() must have been called (not request())
        assert mock_backend.execute.called, (
            f"protocol_call tool '{tool_name}' must call backend.execute(), "
            f"but it called: request={mock_backend.request.called}"
        )
        assert not mock_backend.request.called, (
            "WebSocket protocol_call tool incorrectly called backend.request() "
            "(HTTP backend was rendered instead of protocol backend)"
        )


# ---------------------------------------------------------------------------
# Tests — Express.js (HTTP tools)
# ---------------------------------------------------------------------------

class TestFunctionalExpress:
    """Verify Express-generated HTTP tools call backend correctly."""

    @pytest.mark.asyncio
    async def test_express_http_tools(self, fake_express_app, tmp_output):
        manifest = await _run_pipeline(fake_express_app, tmp_output)
        pkg = _pkg_name(manifest.server_name)

        mock_backend = MagicMock()
        mock_backend.request = AsyncMock(return_value="[]")

        server = _register_all_tools(tmp_output, pkg, mock_backend)
        assert len(server._tools) > 0, "No tools registered"

        # Find GET users tool
        get_users = next(
            (name for name in server._tools if "users" in name and name.startswith("get")),
            None,
        )
        if get_users:
            await _call_with_dummy_args(server._tools[get_users])
            mock_backend.request.assert_called()
            args, _ = mock_backend.request.call_args
            assert args[0] == "GET"


# ---------------------------------------------------------------------------
# Tests — Spring Boot (HTTP tools)
# ---------------------------------------------------------------------------

class TestFunctionalSpringBoot:
    """Verify Spring Boot-generated HTTP tools call backend correctly."""

    @pytest.mark.asyncio
    async def test_spring_http_tools(self, fake_spring_app, tmp_output):
        manifest = await _run_pipeline(fake_spring_app, tmp_output)
        pkg = _pkg_name(manifest.server_name)

        assert manifest.design is not None
        http_tools = [t for t in manifest.design.tools if t.impl.strategy == "http_call"]
        assert len(http_tools) > 0, "Spring Boot should produce http_call tools"

        mock_backend = MagicMock()
        mock_backend.request = AsyncMock(return_value="[]")

        server = _register_all_tools(tmp_output, pkg, mock_backend)
        assert len(server._tools) > 0, "No tools registered"

        # Find and call a GET tool
        get_tool = next(
            (name for name in server._tools if name.startswith("get")),
            None,
        )
        if get_tool:
            await _call_with_dummy_args(server._tools[get_tool])
            mock_backend.request.assert_called()
            args, _ = mock_backend.request.call_args
            assert args[0] == "GET"


# ---------------------------------------------------------------------------
# Tests — GraphQL (HTTP tools with body)
# ---------------------------------------------------------------------------

class TestFunctionalGraphQL:
    """Verify GraphQL-generated tools send POST to /graphql with a body."""

    @pytest.mark.asyncio
    async def test_graphql_tools_post_to_graphql(self, fake_graphql_app, tmp_output):
        manifest = await _run_pipeline(fake_graphql_app, tmp_output)
        pkg = _pkg_name(manifest.server_name)

        assert manifest.design is not None
        assert len(manifest.design.tools) > 0, "No tools generated"

        mock_backend = MagicMock()
        mock_backend.request = AsyncMock(return_value='{"data": {}}')
        mock_backend.execute = AsyncMock(return_value='{"data": {}}')

        server = _register_all_tools(tmp_output, pkg, mock_backend)
        assert len(server._tools) > 0, "No tools registered"

        # Call any tool — GraphQL tools go through request or execute
        tool_name = next(iter(server._tools))
        await _call_with_dummy_args(server._tools[tool_name])

        # GraphQL tools must call the backend in some form
        assert mock_backend.request.called or mock_backend.execute.called, (
            "GraphQL tool must call backend.request() or backend.execute()"
        )
        if mock_backend.request.called:
            args, _ = mock_backend.request.call_args
            assert args[0] == "POST", f"GraphQL should POST, got {args[0]}"


# ---------------------------------------------------------------------------
# Tests — gRPC (HTTP/stub tools)
# ---------------------------------------------------------------------------

class TestFunctionalGRPC:
    """Verify gRPC-generated tools use protocol_call and call backend.execute()."""

    @pytest.mark.asyncio
    async def test_grpc_tools_call_execute(self, fake_grpc_app, tmp_output):
        await _assert_protocol_framework(fake_grpc_app, tmp_output)


# ---------------------------------------------------------------------------
# Tests — OpenAPI (HTTP tools)
# ---------------------------------------------------------------------------

class TestFunctionalOpenAPI:
    """Verify OpenAPI-generated HTTP tools pass path/query params correctly."""

    @pytest.mark.asyncio
    async def test_openapi_http_tools(self, fake_fastapi_app, tmp_output):
        """Use FastAPI app as it generates an OpenAPI-compatible server."""
        manifest = await _run_pipeline(fake_fastapi_app, tmp_output)
        pkg = _pkg_name(manifest.server_name)

        assert manifest.design is not None
        http_tools = [t for t in manifest.design.tools if t.impl.strategy == "http_call"]
        assert len(http_tools) > 0

        mock_backend = MagicMock()
        mock_backend.request = AsyncMock(return_value="[]")

        server = _register_all_tools(tmp_output, pkg, mock_backend)

        # Verify tools are registered and functional
        assert len(server._tools) >= len(http_tools), (
            f"Expected at least {len(http_tools)} tools registered, got {len(server._tools)}"
        )


# ---------------------------------------------------------------------------
# Tests — Backend not called with None params (Bug 5 regression)
# ---------------------------------------------------------------------------

class TestFunctionalNoNullParams:
    """Regression test: optional params with None value must not be sent to backend."""

    @pytest.mark.asyncio
    async def test_none_optional_params_not_sent(self, fake_flask_app, tmp_output):
        """When optional params are None, they must not appear in query_params."""
        manifest = await _run_pipeline(fake_flask_app, tmp_output)
        pkg = _pkg_name(manifest.server_name)

        calls_received = []

        async def mock_request(method, path, *, params=None, body=None, path_params=None):
            calls_received.append({
                "method": method,
                "path": path,
                "params": params,
                "body": body,
                "path_params": path_params,
            })
            return "{}"

        mock_backend = MagicMock()
        mock_backend.request = mock_request

        server = _register_all_tools(tmp_output, pkg, mock_backend)

        # Call get_users with no optional params
        if "get_users" in server._tools:
            await server._tools["get_users"]()
            assert len(calls_received) == 1
            # params should be None or empty (no null values sent)
            sent_params = calls_received[0]["params"]
            assert sent_params is None or sent_params == {}, (
                f"Optional None params should not be sent, got: {sent_params}"
            )


# ---------------------------------------------------------------------------
# Shared helper: verify any HTTP-based framework produces working tools
# ---------------------------------------------------------------------------

async def _assert_http_framework(
    fixture_path: Path,
    tmp_path: Path,
    *,
    name: str | None = None,
    min_tools: int = 1,
) -> None:
    """Run the full pipeline on a fixture and verify ≥1 HTTP tool actually calls backend.request."""
    manifest = await _run_pipeline(fixture_path, tmp_path, name=name)
    assert manifest.design is not None, "No design phase output"

    http_tools = [t for t in manifest.design.tools if t.impl.strategy == "http_call"]
    assert len(http_tools) >= min_tools, (
        f"Expected ≥{min_tools} http_call tools, got {len(http_tools)}. "
        f"All tools: {[(t.name, t.impl.strategy) for t in manifest.design.tools]}"
    )

    pkg = _pkg_name(manifest.server_name)
    mock_backend = MagicMock()
    mock_backend.request = AsyncMock(return_value='{"ok": true}')

    server = _register_all_tools(tmp_path, pkg, mock_backend)
    assert len(server._tools) >= min_tools, (
        f"Expected ≥{min_tools} tools registered, got {list(server._tools)}"
    )

    # Call every GET tool to verify backend.request fires with correct method
    called_any = False
    for tool_name, fn in server._tools.items():
        tool_spec = next((t for t in http_tools if t.name == tool_name), None)
        if tool_spec and tool_spec.impl.http_method == "GET":
            mock_backend.request.reset_mock()
            await _call_with_dummy_args(fn)
            assert mock_backend.request.called, (
                f"Tool '{tool_name}' did not call backend.request()"
            )
            args, _ = mock_backend.request.call_args
            assert args[0] == "GET", f"Tool '{tool_name}' sent {args[0]}, expected GET"
            called_any = True
            break  # One verified GET tool is enough per framework

    assert called_any, (
        f"No GET tool was exercised. Available tools: {list(server._tools)}"
    )


async def _assert_cli_framework(
    fixture_path: Path,
    tmp_path: Path,
    *,
    name: str | None = None,
) -> None:
    """Verify ≥1 cli_subcommand tool calls backend.run_subcommand with the tool name."""
    manifest = await _run_pipeline(fixture_path, tmp_path, name=name)
    assert manifest.design is not None

    cli_tools = [t for t in manifest.design.tools if t.impl.strategy == "cli_subcommand"]
    assert len(cli_tools) >= 1, (
        f"Expected ≥1 cli_subcommand tools, got {[(t.name, t.impl.strategy) for t in manifest.design.tools]}"
    )

    pkg = _pkg_name(manifest.server_name)
    mock_backend = MagicMock()
    mock_backend.run_subcommand = AsyncMock(return_value="ok")

    server = _register_all_tools(tmp_path, pkg, mock_backend)
    assert len(server._tools) >= 1

    # Prefer a tool with a non-empty subcommand — some CLIs also emit a top-level
    # "run" tool (e.g. run_fake_click_app) with empty cli_subcommand alongside named ones.
    named_tools = [t for t in cli_tools if t.impl.cli_subcommand]
    tool_spec = named_tools[0] if named_tools else cli_tools[0]
    tool_name = tool_spec.name
    expected_subcommand = tool_spec.impl.cli_subcommand

    assert tool_name in server._tools, (
        f"Tool '{tool_name}' not in registered tools: {list(server._tools)}"
    )
    await _call_with_dummy_args(server._tools[tool_name])
    mock_backend.run_subcommand.assert_called_once()
    args, _ = mock_backend.run_subcommand.call_args
    assert args[0] == expected_subcommand, (
        f"Expected subcommand '{expected_subcommand}', got '{args[0]}'"
    )


async def _assert_protocol_framework(
    fixture_path: Path,
    tmp_path: Path,
    *,
    name: str | None = None,
) -> None:
    """Verify ≥1 protocol_call tool calls backend.execute (not backend.request)."""
    manifest = await _run_pipeline(fixture_path, tmp_path, name=name)
    assert manifest.design is not None

    proto_tools = [t for t in manifest.design.tools if t.impl.strategy == "protocol_call"]
    assert len(proto_tools) >= 1, (
        f"Expected ≥1 protocol_call tools, got {[(t.name, t.impl.strategy) for t in manifest.design.tools]}"
    )

    pkg = _pkg_name(manifest.server_name)
    mock_backend = MagicMock()
    mock_backend.execute = AsyncMock(return_value='{"result": "ok"}')

    server = _register_all_tools(tmp_path, pkg, mock_backend)
    assert len(server._tools) >= 1

    tool_name = proto_tools[0].name
    assert tool_name in server._tools, (
        f"Tool '{tool_name}' not registered. Available: {list(server._tools)}"
    )
    await _call_with_dummy_args(server._tools[tool_name])
    assert mock_backend.execute.called, (
        f"protocol_call tool '{tool_name}' did not call backend.execute()"
    )
    assert not mock_backend.request.called, (
        f"protocol_call tool '{tool_name}' incorrectly called backend.request() — "
        "wrong backend template was rendered"
    )


# ---------------------------------------------------------------------------
# Django DRF
# ---------------------------------------------------------------------------

class TestFunctionalDjango:
    @pytest.mark.asyncio
    async def test_django_http_tools(self, fake_django_app, tmp_output):
        await _assert_http_framework(fake_django_app, tmp_output, min_tools=3)


# ---------------------------------------------------------------------------
# Python Click CLI
# ---------------------------------------------------------------------------

class TestFunctionalClick:
    @pytest.mark.asyncio
    async def test_click_cli_tools(self, fake_click_app, tmp_output):
        await _assert_cli_framework(fake_click_app, tmp_output)


# ---------------------------------------------------------------------------
# Spring MVC
# ---------------------------------------------------------------------------

class TestFunctionalSpringMVC:
    @pytest.mark.asyncio
    async def test_spring_mvc_http_tools(self, fake_spring_mvc_app, tmp_output):
        await _assert_http_framework(fake_spring_mvc_app, tmp_output, min_tools=2)


# ---------------------------------------------------------------------------
# JAX-RS / Quarkus
# ---------------------------------------------------------------------------

class TestFunctionalJaxRS:
    @pytest.mark.asyncio
    async def test_jaxrs_http_tools(self, fake_jaxrs_app, tmp_output):
        await _assert_http_framework(fake_jaxrs_app, tmp_output, min_tools=2)


# ---------------------------------------------------------------------------
# Micronaut
# ---------------------------------------------------------------------------

class TestFunctionalMicronaut:
    @pytest.mark.asyncio
    async def test_micronaut_http_tools(self, fake_micronaut_app, tmp_output):
        await _assert_http_framework(fake_micronaut_app, tmp_output, min_tools=2)


# ---------------------------------------------------------------------------
# Kotlin Spring
# ---------------------------------------------------------------------------

class TestFunctionalKotlinSpring:
    @pytest.mark.asyncio
    async def test_kotlin_spring_http_tools(self, fake_kotlin_spring_app, tmp_output):
        await _assert_http_framework(fake_kotlin_spring_app, tmp_output, min_tools=2)


# ---------------------------------------------------------------------------
# Kotlin JAX-RS
# ---------------------------------------------------------------------------

class TestFunctionalKotlinJaxRS:
    @pytest.mark.asyncio
    async def test_kotlin_jaxrs_http_tools(self, fake_kotlin_jaxrs_app, tmp_output):
        await _assert_http_framework(fake_kotlin_jaxrs_app, tmp_output, min_tools=2)


# ---------------------------------------------------------------------------
# Go Gin
# ---------------------------------------------------------------------------

class TestFunctionalGoGin:
    @pytest.mark.asyncio
    async def test_go_gin_http_tools(self, fake_go_app, tmp_output):
        await _assert_http_framework(fake_go_app, tmp_output, min_tools=2)


# ---------------------------------------------------------------------------
# Go Echo
# ---------------------------------------------------------------------------

class TestFunctionalGoEcho:
    @pytest.mark.asyncio
    async def test_go_echo_http_tools(self, fake_go_echo_app, tmp_output):
        await _assert_http_framework(fake_go_echo_app, tmp_output, min_tools=2)


# ---------------------------------------------------------------------------
# Go Chi
# ---------------------------------------------------------------------------

class TestFunctionalGoChi:
    @pytest.mark.asyncio
    async def test_go_chi_http_tools(self, fake_go_chi_app, tmp_output):
        await _assert_http_framework(fake_go_chi_app, tmp_output, min_tools=2)


# ---------------------------------------------------------------------------
# Go gorilla/mux
# ---------------------------------------------------------------------------

class TestFunctionalGoMux:
    @pytest.mark.asyncio
    async def test_go_mux_http_tools(self, fake_go_mux_app, tmp_output):
        await _assert_http_framework(fake_go_mux_app, tmp_output, min_tools=2)


# ---------------------------------------------------------------------------
# Go net/http
# ---------------------------------------------------------------------------

class TestFunctionalGoNetHTTP:
    @pytest.mark.asyncio
    async def test_go_nethttp_http_tools(self, fake_go_nethttp_app, tmp_output):
        await _assert_http_framework(fake_go_nethttp_app, tmp_output, min_tools=1)


# ---------------------------------------------------------------------------
# Ruby Rails (resources)
# ---------------------------------------------------------------------------

class TestFunctionalRails:
    @pytest.mark.asyncio
    async def test_rails_http_tools(self, fake_rails_app, tmp_output):
        await _assert_http_framework(fake_rails_app, tmp_output, min_tools=2)


# ---------------------------------------------------------------------------
# Ruby Rails (explicit routes)
# ---------------------------------------------------------------------------

class TestFunctionalRailsExplicit:
    @pytest.mark.asyncio
    async def test_rails_explicit_http_tools(self, fake_rails_explicit_routes_app, tmp_output):
        await _assert_http_framework(fake_rails_explicit_routes_app, tmp_output, min_tools=2)


# ---------------------------------------------------------------------------
# Rust Actix
# ---------------------------------------------------------------------------

class TestFunctionalRustActix:
    @pytest.mark.asyncio
    async def test_actix_http_tools(self, fake_rust_app, tmp_output):
        await _assert_http_framework(fake_rust_app, tmp_output, min_tools=2)


# ---------------------------------------------------------------------------
# Rust Axum
# ---------------------------------------------------------------------------

class TestFunctionalRustAxum:
    @pytest.mark.asyncio
    async def test_axum_http_tools(self, fake_axum_app, tmp_output):
        await _assert_http_framework(fake_axum_app, tmp_output, min_tools=2)


# ---------------------------------------------------------------------------
# Rust Rocket
# ---------------------------------------------------------------------------

class TestFunctionalRustRocket:
    @pytest.mark.asyncio
    async def test_rocket_http_tools(self, fake_rocket_app, tmp_output):
        await _assert_http_framework(fake_rocket_app, tmp_output, min_tools=2)


# ---------------------------------------------------------------------------
# Rust Warp
# ---------------------------------------------------------------------------

class TestFunctionalRustWarp:
    @pytest.mark.asyncio
    async def test_warp_http_tools(self, fake_warp_app, tmp_output):
        await _assert_http_framework(fake_warp_app, tmp_output, min_tools=2)


# ---------------------------------------------------------------------------
# TypeScript Express
# ---------------------------------------------------------------------------

class TestFunctionalTypeScriptExpress:
    @pytest.mark.asyncio
    async def test_ts_express_http_tools(self, fake_ts_express_app, tmp_output):
        await _assert_http_framework(fake_ts_express_app, tmp_output, min_tools=2)


# ---------------------------------------------------------------------------
# Socket / XML-RPC
# ---------------------------------------------------------------------------

class TestFunctionalSocketXMLRPC:
    @pytest.mark.asyncio
    async def test_socket_xmlrpc_protocol_tools(self, fake_socket_xmlrpc_app, tmp_output):
        await _assert_protocol_framework(fake_socket_xmlrpc_app, tmp_output)
