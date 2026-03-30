"""End-to-end integration tests for the mcp-anything pipeline.

Each test runs the full 5-phase pipeline on a fixture app and verifies:
  1. All phases complete without errors
  2. Expected output files exist with correct structure
  3. Generated Python files are syntactically valid (AST-parseable)
  4. The generated server module can be imported and has the expected tools
  5. The design phase produces correct tool names and strategies
"""

import ast
import asyncio
import sys
from pathlib import Path

import pytest
from rich.console import Console

from mcp_anything.config import CLIOptions
from mcp_anything.models.manifest import GenerationManifest
from mcp_anything.pipeline.engine import PipelineEngine


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _run_pipeline(
    codebase_path: Path,
    output_dir: Path,
    *,
    transport: str = "stdio",
    name: str | None = None,
) -> GenerationManifest:
    """Run the full pipeline and return the saved manifest."""
    options = CLIOptions(
        codebase_path=codebase_path,
        output_dir=output_dir,
        name=name,
        no_llm=True,
        no_install=True,
        transport=transport,
    )
    console = Console(quiet=True)
    engine = PipelineEngine(options, console)
    await engine.run()

    manifest_path = output_dir / "mcp-anything-manifest.json"
    assert manifest_path.exists(), "Manifest file not created"
    return GenerationManifest.load(manifest_path)


def _package_name(server_name: str) -> str:
    """Derive the generated Python package name."""
    return f"mcp_{server_name.replace('-', '_')}"


def _validate_python_syntax(output_dir: Path) -> list[str]:
    """Parse every .py file under output_dir; return list of errors."""
    errors: list[str] = []
    for py_file in output_dir.rglob("*.py"):
        try:
            ast.parse(py_file.read_text(), filename=str(py_file))
        except SyntaxError as exc:
            errors.append(f"{py_file.relative_to(output_dir)}: {exc}")
    return errors


def _assert_standard_structure(output_dir: Path, pkg_name: str) -> None:
    """Assert the expected directory layout exists."""
    src = output_dir / "src" / pkg_name
    assert src.is_dir(), f"Package directory {src} missing"
    assert (src / "__init__.py").exists(), "__init__.py missing"
    assert (src / "server.py").exists(), "server.py missing"
    assert (output_dir / "pyproject.toml").exists(), "pyproject.toml missing"
    assert (output_dir / "mcp.json").exists(), "mcp.json missing"
    assert (output_dir / "README.md").exists(), "README.md missing"


def _import_server(output_dir: Path, pkg_name: str):
    """Import the generated server module and return it."""
    src_path = str(output_dir / "src")
    original_path = sys.path.copy()
    try:
        sys.path.insert(0, src_path)
        import importlib
        mod = importlib.import_module(f"{pkg_name}.server")
        return mod
    finally:
        sys.path[:] = original_path
        # Clean up imported modules to avoid cross-test pollution
        to_remove = [k for k in sys.modules if k.startswith(pkg_name)]
        for k in to_remove:
            del sys.modules[k]


def _get_tool_names(manifest: GenerationManifest) -> set[str]:
    """Extract tool names from the design."""
    assert manifest.design is not None
    return {t.name for t in manifest.design.tools}




# ---------------------------------------------------------------------------
# Shared assertions used across many tests
# ---------------------------------------------------------------------------

def _full_assertions(
    manifest: GenerationManifest,
    output_dir: Path,
    *,
    expected_tools: set[str],
    expected_strategy: str,
    min_tools: int = 1,
) -> None:
    """Run all standard assertions on a completed pipeline."""
    # All 5 phases completed
    assert manifest.completed_phases == [
        "analyze", "design", "implement", "document", "package"
    ], f"Phases: {manifest.completed_phases}"
    assert manifest.errors == [], f"Pipeline errors: {manifest.errors}"

    # Design is populated
    design = manifest.design
    assert design is not None
    assert len(design.tools) >= min_tools, (
        f"Expected >= {min_tools} tools, got {len(design.tools)}"
    )

    # Correct tool names
    actual_tools = _get_tool_names(manifest)
    missing = expected_tools - actual_tools
    assert not missing, f"Missing expected tools: {missing}. Got: {actual_tools}"

    # Strategy check
    for tool in design.tools:
        if tool.name in expected_tools:
            assert tool.impl.strategy == expected_strategy, (
                f"Tool {tool.name}: expected strategy '{expected_strategy}', "
                f"got '{tool.impl.strategy}'"
            )

    # File structure
    pkg_name = _package_name(design.server_name)
    _assert_standard_structure(output_dir, pkg_name)

    # All generated Python is valid syntax
    syntax_errors = _validate_python_syntax(output_dir)
    assert syntax_errors == [], f"Syntax errors:\n" + "\n".join(syntax_errors)

    # Server module can be imported
    server_mod = _import_server(output_dir, pkg_name)
    assert hasattr(server_mod, "server"), "server object not found in server module"


# ---------------------------------------------------------------------------
# Tests — Python backends
# ---------------------------------------------------------------------------

class TestPythonCLI:
    """Integration test: Python argparse CLI app."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, fake_cli_app, tmp_output):
        manifest = await _run_pipeline(fake_cli_app, tmp_output)

        _full_assertions(
            manifest, tmp_output,
            expected_tools={"process", "status", "formats"},
            expected_strategy="cli_subcommand",
            min_tools=3,
        )

        # CLI-specific: verify analysis detected CLI mechanism
        assert manifest.analysis is not None
        ipc_types = {m.ipc_type for m in manifest.analysis.ipc_mechanisms}
        assert "cli" in ipc_types or any(
            "cli" in str(t).lower() for t in ipc_types
        ), f"Expected CLI detection, got: {ipc_types}"


class TestFlask:
    """Integration test: Flask REST API."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, fake_flask_app, tmp_output):
        manifest = await _run_pipeline(fake_flask_app, tmp_output)

        _full_assertions(
            manifest, tmp_output,
            expected_tools={"get_users", "post_users", "get_health"},
            expected_strategy="http_call",
            min_tools=4,
        )

        # HTTP-specific: verify backend config
        design = manifest.design
        assert design.backend is not None
        assert design.backend.host == "localhost"

        # Verify HTTP paths on tools
        http_tools = {t.name: t for t in design.tools if t.impl.strategy == "http_call"}
        assert "get_users" in http_tools
        assert http_tools["get_users"].impl.http_method == "GET"
        assert "/users" in http_tools["get_users"].impl.http_path


class TestFastAPI:
    """Integration test: FastAPI REST API."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, fake_fastapi_app, tmp_output):
        manifest = await _run_pipeline(fake_fastapi_app, tmp_output)

        _full_assertions(
            manifest, tmp_output,
            expected_tools={"get_users", "post_users", "get_health"},
            expected_strategy="http_call",
            min_tools=5,
        )

        # Verify path params are extracted for parameterized routes
        design = manifest.design
        user_by_id_tools = [
            t for t in design.tools
            if "user" in t.name and "by" in t.name
        ]
        assert len(user_by_id_tools) >= 1, "No user-by-id tools found"
        param_names = {p.name for p in user_by_id_tools[0].parameters}
        assert "user_id" in param_names or "id" in param_names, (
            f"Expected path param user_id or id, got: {param_names}"
        )


class TestDjango:
    """Integration test: Django REST Framework ViewSet."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, fake_django_app, tmp_output):
        manifest = await _run_pipeline(fake_django_app, tmp_output)

        _full_assertions(
            manifest, tmp_output,
            expected_tools={"get_users", "post_users"},
            expected_strategy="http_call",
            min_tools=5,
        )


# ---------------------------------------------------------------------------
# Tests — JavaScript/TypeScript backends
# ---------------------------------------------------------------------------

class TestExpress:
    """Integration test: Express.js REST API."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, fake_express_app, tmp_output):
        manifest = await _run_pipeline(fake_express_app, tmp_output)

        _full_assertions(
            manifest, tmp_output,
            expected_tools={"get_health", "get_products", "post_products"},
            expected_strategy="http_call",
            min_tools=4,
        )

    @pytest.mark.asyncio
    async def test_router_mount_prefix_applied(self, fake_express_app, tmp_output):
        """Bug #3 regression: router-mounted routes must include the mount prefix."""
        manifest = await _run_pipeline(fake_express_app, tmp_output)
        tool_names = _get_tool_names(manifest)

        # Routes mounted via app.use('/api/users', usersRouter) should have
        # the prefix in the tool name, not bare 'get' or 'post'
        bare_names = {"get", "post", "put", "delete", "patch"}
        collision = bare_names & tool_names
        assert not collision, (
            f"Router routes lost mount prefix — bare tool names found: {collision}"
        )


# ---------------------------------------------------------------------------
# Tests — Java backends
# ---------------------------------------------------------------------------

class TestSpringBoot:
    """Integration test: Spring Boot REST controller."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, fake_spring_app, tmp_output):
        manifest = await _run_pipeline(fake_spring_app, tmp_output)

        _full_assertions(
            manifest, tmp_output,
            expected_tools={"get_users", "post_users"},
            expected_strategy="http_call",
            min_tools=4,
        )

        # Verify annotation-extracted params
        design = manifest.design
        get_by_id = next(
            (t for t in design.tools if "by_id" in t.name and t.impl.http_method == "GET"),
            None,
        )
        assert get_by_id is not None, "No GET-by-id tool found"
        assert any(p.name == "id" for p in get_by_id.parameters), (
            f"Expected 'id' path param, got: {[p.name for p in get_by_id.parameters]}"
        )


class TestJaxRS:
    """Integration test: JAX-RS/Quarkus REST resource."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, fake_jaxrs_app, tmp_output):
        manifest = await _run_pipeline(fake_jaxrs_app, tmp_output)

        _full_assertions(
            manifest, tmp_output,
            expected_tools={"get_items", "post_items"},
            expected_strategy="http_call",
            min_tools=4,
        )


class TestMicronaut:
    """Integration test: Micronaut REST controller."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, fake_micronaut_app, tmp_output):
        manifest = await _run_pipeline(fake_micronaut_app, tmp_output)

        _full_assertions(
            manifest, tmp_output,
            expected_tools={"get_orders", "post_orders"},
            expected_strategy="http_call",
            min_tools=4,
        )


# ---------------------------------------------------------------------------
# Tests — Go backends
# ---------------------------------------------------------------------------

class TestGoGin:
    """Integration test: Go Gin web framework."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, fake_go_app, tmp_output):
        manifest = await _run_pipeline(fake_go_app, tmp_output)

        # Go Gin uses /api/v1/users — route_utils strips /api/ then /v1/ prefix
        tool_names = _get_tool_names(manifest)
        # Should have user CRUD tools (exact prefix depends on stripping logic)
        assert any("users" in n for n in tool_names), (
            f"Expected user-related tools, got: {tool_names}"
        )
        assert len(tool_names) >= 4

        design = manifest.design
        pkg_name = _package_name(design.server_name)
        _assert_standard_structure(tmp_output, pkg_name)
        syntax_errors = _validate_python_syntax(tmp_output)
        assert syntax_errors == [], f"Syntax errors:\n" + "\n".join(syntax_errors)

        server_mod = _import_server(tmp_output, pkg_name)
        assert hasattr(server_mod, "server")


# ---------------------------------------------------------------------------
# Tests — Ruby backends
# ---------------------------------------------------------------------------

class TestRails:
    """Integration test: Ruby on Rails controllers."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, fake_rails_app, tmp_output):
        manifest = await _run_pipeline(fake_rails_app, tmp_output)

        _full_assertions(
            manifest, tmp_output,
            expected_tools={"get_users", "post_users"},
            expected_strategy="http_call",
            min_tools=4,
        )


# ---------------------------------------------------------------------------
# Tests — Rust backends
# ---------------------------------------------------------------------------

class TestRustActix:
    """Integration test: Rust Actix-web framework."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, fake_rust_app, tmp_output):
        manifest = await _run_pipeline(fake_rust_app, tmp_output)

        _full_assertions(
            manifest, tmp_output,
            expected_tools={"get_users", "post_users", "get_health"},
            expected_strategy="http_call",
            min_tools=4,
        )


# ---------------------------------------------------------------------------
# Tests — Spec-based backends
# ---------------------------------------------------------------------------

class TestOpenAPI:
    """Integration test: OpenAPI 3.0 specification."""

    @pytest.fixture
    def openapi_dir(self, fixtures_dir, tmp_path):
        """Create a directory containing just the OpenAPI spec."""
        spec_dir = tmp_path / "petstore"
        spec_dir.mkdir()
        import shutil
        shutil.copy(fixtures_dir / "petstore_openapi.json", spec_dir / "openapi.json")
        return spec_dir

    @pytest.mark.asyncio
    async def test_full_pipeline(self, openapi_dir, tmp_output):
        manifest = await _run_pipeline(openapi_dir, tmp_output, name="petstore")

        # OpenAPI uses operationId for tool names
        _full_assertions(
            manifest, tmp_output,
            expected_tools={"list_pets", "create_pet", "get_pet", "delete_pet"},
            expected_strategy="http_call",
            min_tools=5,
        )

        # Should have tools for all pet operations
        tool_names = _get_tool_names(manifest)
        assert "get_inventory" in tool_names or "list_vaccinations" in tool_names, (
            f"Expected nested operations, got: {tool_names}"
        )


class TestGraphQL:
    """Integration test: GraphQL SDL schema."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, fake_graphql_app, tmp_output):
        manifest = await _run_pipeline(fake_graphql_app, tmp_output)

        # GraphQL tools are named after queries/mutations, not HTTP methods
        tool_names = _get_tool_names(manifest)
        assert len(tool_names) >= 4, f"Expected >= 4 tools, got: {tool_names}"

        # Should have both query and mutation tools
        assert any("user" in n for n in tool_names), (
            f"Expected user-related tools, got: {tool_names}"
        )
        assert any("create" in n for n in tool_names), (
            f"Expected mutation tools (create_*), got: {tool_names}"
        )

        # Structure and syntax still valid
        design = manifest.design
        pkg_name = _package_name(design.server_name)
        _assert_standard_structure(tmp_output, pkg_name)
        syntax_errors = _validate_python_syntax(tmp_output)
        assert syntax_errors == [], f"Syntax errors:\n" + "\n".join(syntax_errors)


class TestGRPC:
    """Integration test: gRPC/Protobuf service definition."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, fake_grpc_app, tmp_output):
        manifest = await _run_pipeline(fake_grpc_app, tmp_output)

        tool_names = _get_tool_names(manifest)
        assert len(tool_names) >= 3, f"Expected >= 3 tools, got: {tool_names}"

        # Should have CRUD-ish method names from the proto service
        assert any("user" in n for n in tool_names), (
            f"Expected user-related tools from proto, got: {tool_names}"
        )

        design = manifest.design
        pkg_name = _package_name(design.server_name)
        _assert_standard_structure(tmp_output, pkg_name)
        syntax_errors = _validate_python_syntax(tmp_output)
        assert syntax_errors == [], f"Syntax errors:\n" + "\n".join(syntax_errors)


# ---------------------------------------------------------------------------
# Tests — Protocol backends
# ---------------------------------------------------------------------------

class TestWebSocketProtocol:
    """Integration test: WebSocket protocol backend (raw websockets library)."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, fake_ws_protocol_app, tmp_output):
        manifest = await _run_pipeline(fake_ws_protocol_app, tmp_output)

        # Should detect as protocol with WebSocket
        assert manifest.analysis is not None
        assert manifest.analysis.primary_ipc is not None
        mechanisms = [m.ipc_type.value for m in manifest.analysis.ipc_mechanisms]
        assert "protocol" in mechanisms, f"Expected protocol IPC, got: {mechanisms}"

        # Should produce protocol_call tools
        tool_names = _get_tool_names(manifest)
        assert "register_device" in tool_names, f"Expected register_device, got: {tool_names}"
        assert "get_device" in tool_names, f"Expected get_device, got: {tool_names}"
        assert "list_devices" in tool_names, f"Expected list_devices, got: {tool_names}"

        design = manifest.design
        assert design is not None

        # All tools should use protocol_call strategy
        for tool in design.tools:
            if tool.name in {"register_device", "get_device", "list_devices"}:
                assert tool.impl.strategy == "protocol_call", (
                    f"Tool {tool.name}: expected 'protocol_call', got '{tool.impl.strategy}'"
                )

        # Backend should be protocol type
        assert design.backend is not None
        assert design.backend.backend_type.value == "protocol"

        # Should have websockets dependency
        assert any("websockets" in d for d in design.dependencies), (
            f"Expected websockets dependency, got: {design.dependencies}"
        )

        # Structure, syntax, imports
        pkg_name = _package_name(design.server_name)
        _assert_standard_structure(tmp_output, pkg_name)
        syntax_errors = _validate_python_syntax(tmp_output)
        assert syntax_errors == [], f"Syntax errors:\n" + "\n".join(syntax_errors)

        server_mod = _import_server(tmp_output, pkg_name)
        assert hasattr(server_mod, "server"), "server object not found"


# ---------------------------------------------------------------------------
# Tests — Transport modes
# ---------------------------------------------------------------------------

class TestHTTPTransport:
    """Integration test: --transport http generates Streamable HTTP config."""

    @pytest.mark.asyncio
    async def test_http_transport(self, fake_flask_app, tmp_output):
        manifest = await _run_pipeline(
            fake_flask_app, tmp_output, transport="http"
        )

        assert manifest.design is not None
        assert manifest.design.transport == "http"

        # mcp.json should have URL instead of command
        import json
        mcp_config = json.loads((tmp_output / "mcp.json").read_text())
        servers = mcp_config["mcpServers"]
        assert len(servers) == 1
        server_cfg = next(iter(servers.values()))
        assert "url" in server_cfg, (
            f"HTTP transport should use 'url' in mcp.json, got: {server_cfg}"
        )
        assert server_cfg["url"].endswith("/mcp")


class TestStdioTransport:
    """Integration test: default stdio transport uses command-based mcp.json."""

    @pytest.mark.asyncio
    async def test_stdio_mcp_config(self, fake_flask_app, tmp_output):
        manifest = await _run_pipeline(fake_flask_app, tmp_output)

        import json
        mcp_config = json.loads((tmp_output / "mcp.json").read_text())
        servers = mcp_config["mcpServers"]
        server_cfg = next(iter(servers.values()))
        assert "command" in server_cfg, (
            f"stdio transport should use 'command' in mcp.json, got: {server_cfg}"
        )
        assert "env" in server_cfg, "stdio HTTP proxy config should include env placeholders"
        env = server_cfg["env"]
        assert any(key.endswith("_BASE_URL") for key in env), (
            f"Expected *_BASE_URL in env config, got: {env}"
        )


# ---------------------------------------------------------------------------
# Tests — Resume support
# ---------------------------------------------------------------------------

class TestResume:
    """Integration test: pipeline resume skips completed phases."""

    @pytest.mark.asyncio
    async def test_resume_skips_completed(self, fake_flask_app, tmp_output):
        # Run only analyze + design first
        options = CLIOptions(
            codebase_path=fake_flask_app,
            output_dir=tmp_output,
            phases=["analyze", "design"],
            no_llm=True,
            no_install=True,
        )
        console = Console(quiet=True)
        engine = PipelineEngine(options, console)
        await engine.run()

        manifest = GenerationManifest.load(tmp_output / "mcp-anything-manifest.json")
        assert manifest.completed_phases == ["analyze", "design"]

        # Now resume — should skip analyze+design and run the rest
        resume_options = CLIOptions(
            codebase_path=fake_flask_app,
            output_dir=tmp_output,
            resume=True,
            no_llm=True,
            no_install=True,
        )
        engine2 = PipelineEngine(resume_options, console)
        await engine2.run()

        manifest2 = GenerationManifest.load(tmp_output / "mcp-anything-manifest.json")
        assert manifest2.completed_phases == [
            "analyze", "design", "implement", "document", "package"
        ]
        # Design data should be preserved from the first run
        assert manifest2.design is not None
        assert len(manifest2.design.tools) >= 4


# ---------------------------------------------------------------------------
# Tests — Cross-cutting concerns
# ---------------------------------------------------------------------------

class TestManifestIntegrity:
    """Verify the manifest captures complete pipeline state."""

    @pytest.mark.asyncio
    async def test_manifest_has_analysis_and_design(self, fake_fastapi_app, tmp_output):
        manifest = await _run_pipeline(fake_fastapi_app, tmp_output)

        # Analysis populated
        analysis = manifest.analysis
        assert analysis is not None
        assert len(analysis.capabilities) >= 5
        assert len(analysis.files) >= 1
        assert len(analysis.ipc_mechanisms) >= 1

        # Design populated
        design = manifest.design
        assert design is not None
        assert len(design.tools) >= 5
        assert len(design.tool_modules) >= 1
        assert design.backend is not None
        assert len(design.resources) >= 1
        assert len(design.prompts) >= 1

        # Generated files tracked
        assert len(manifest.generated_files) >= 5
        assert "pyproject.toml" in manifest.generated_files
        assert "mcp.json" in manifest.generated_files


class TestAGENTSmd:
    """Verify AGENTS.md generation contains tool documentation."""

    @pytest.mark.asyncio
    async def test_agents_md_content(self, fake_flask_app, tmp_output):
        manifest = await _run_pipeline(fake_flask_app, tmp_output)

        agents_md = tmp_output / "AGENTS.md"
        assert agents_md.exists(), "AGENTS.md not generated"

        content = agents_md.read_text()
        # Should document the tools
        tool_names = _get_tool_names(manifest)
        for name in list(tool_names)[:3]:  # Check at least a few
            assert name in content, f"Tool '{name}' not documented in AGENTS.md"


# ---------------------------------------------------------------------------
# Tests — Scope filtering
# ---------------------------------------------------------------------------

class TestScopeFiltering:
    """Integration tests for --include/--exclude/--scope-file/--review."""

    @pytest.fixture
    def openapi_dir(self, fixtures_dir, tmp_path):
        """Petstore OpenAPI spec in a temp dir."""
        spec_dir = tmp_path / "petstore"
        spec_dir.mkdir()
        import shutil
        shutil.copy(fixtures_dir / "petstore_openapi.json", spec_dir / "openapi.json")
        return spec_dir

    @pytest.mark.asyncio
    async def test_include_filters_tools(self, openapi_dir, tmp_output):
        """--include restricts which capabilities become tools."""
        options = CLIOptions(
            codebase_path=openapi_dir,
            output_dir=tmp_output,
            name="petstore",
            no_llm=True,
            no_install=True,
            include=["list_*", "get_*"],
        )
        console = Console(quiet=True)
        engine = PipelineEngine(options, console)
        await engine.run()

        manifest = GenerationManifest.load(tmp_output / "mcp-anything-manifest.json")
        tool_names = _get_tool_names(manifest)

        # Only list_* and get_* should survive
        assert "list_pets" in tool_names
        assert "get_pet" in tool_names
        # create_pet, delete_pet should be excluded
        assert "create_pet" not in tool_names
        assert "delete_pet" not in tool_names

        # Still produces valid output
        syntax_errors = _validate_python_syntax(tmp_output)
        assert syntax_errors == [], f"Syntax errors: {syntax_errors}"

    @pytest.mark.asyncio
    async def test_exclude_filters_tools(self, openapi_dir, tmp_output):
        """--exclude removes matching capabilities."""
        options = CLIOptions(
            codebase_path=openapi_dir,
            output_dir=tmp_output,
            name="petstore",
            no_llm=True,
            no_install=True,
            exclude=["delete_*"],
        )
        console = Console(quiet=True)
        engine = PipelineEngine(options, console)
        await engine.run()

        manifest = GenerationManifest.load(tmp_output / "mcp-anything-manifest.json")
        tool_names = _get_tool_names(manifest)

        assert "list_pets" in tool_names
        assert "create_pet" in tool_names
        assert "delete_pet" not in tool_names

    @pytest.mark.asyncio
    async def test_scope_file_filters_tools(self, openapi_dir, tmp_output, tmp_path):
        """--scope-file with per-capability enabled/disabled."""
        import yaml

        scope_path = tmp_path / "scope.yaml"
        scope_doc = {
            "include_patterns": [],
            "exclude_patterns": [],
            "capabilities": [
                {"name": "list_pets", "enabled": True},
                {"name": "get_pet", "enabled": True},
                {"name": "create_pet", "enabled": False},
                {"name": "delete_pet", "enabled": False},
            ],
        }
        with open(scope_path, "w") as f:
            yaml.dump(scope_doc, f)

        options = CLIOptions(
            codebase_path=openapi_dir,
            output_dir=tmp_output,
            name="petstore",
            no_llm=True,
            no_install=True,
            scope_file=scope_path,
        )
        console = Console(quiet=True)
        engine = PipelineEngine(options, console)
        await engine.run()

        manifest = GenerationManifest.load(tmp_output / "mcp-anything-manifest.json")
        tool_names = _get_tool_names(manifest)

        assert "list_pets" in tool_names
        assert "get_pet" in tool_names
        assert "create_pet" not in tool_names
        assert "delete_pet" not in tool_names

        # Valid output with correct tool count
        syntax_errors = _validate_python_syntax(tmp_output)
        assert syntax_errors == [], f"Syntax errors: {syntax_errors}"

    @pytest.mark.asyncio
    async def test_review_then_resume(self, openapi_dir, tmp_output):
        """--review pauses after analyze; --resume loads scope.yaml."""
        import yaml

        # Step 1: Run with --review — should stop after analyze
        review_options = CLIOptions(
            codebase_path=openapi_dir,
            output_dir=tmp_output,
            name="petstore",
            no_llm=True,
            no_install=True,
            review=True,
        )
        console = Console(quiet=True)
        engine = PipelineEngine(review_options, console)
        await engine.run()

        # Should have created scope.yaml and stopped after analyze
        manifest = GenerationManifest.load(tmp_output / "mcp-anything-manifest.json")
        assert manifest.completed_phases == ["analyze"]

        scope_path = tmp_output / "scope.yaml"
        assert scope_path.exists(), "scope.yaml not created by --review"

        # Step 2: User edits scope — disable some capabilities
        doc = yaml.safe_load(scope_path.read_text())
        for entry in doc["capabilities"]:
            if entry["name"] in ("create_pet", "delete_pet"):
                entry["enabled"] = False
        with open(scope_path, "w") as f:
            yaml.dump(doc, f)

        # Step 3: Resume — should apply scope and complete
        resume_options = CLIOptions(
            codebase_path=openapi_dir,
            output_dir=tmp_output,
            name="petstore",
            no_llm=True,
            no_install=True,
            resume=True,
        )
        engine2 = PipelineEngine(resume_options, console)
        await engine2.run()

        manifest2 = GenerationManifest.load(tmp_output / "mcp-anything-manifest.json")
        assert manifest2.completed_phases == [
            "analyze", "design", "implement", "document", "package"
        ]

        tool_names = _get_tool_names(manifest2)
        assert "list_pets" in tool_names
        assert "get_pet" in tool_names
        assert "create_pet" not in tool_names
        assert "delete_pet" not in tool_names

        # Generated code is valid
        syntax_errors = _validate_python_syntax(tmp_output)
        assert syntax_errors == [], f"Syntax errors: {syntax_errors}"


# ---------------------------------------------------------------------------
# Tests — Additional Rust backends (Axum, Rocket)
# ---------------------------------------------------------------------------

class TestRailsExplicitRoutes:
    """Integration test: Rails with explicit to:, =>, namespace, and only: routes."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, fake_rails_explicit_routes_app, tmp_output):
        manifest = await _run_pipeline(fake_rails_explicit_routes_app, tmp_output)

        _full_assertions(
            manifest, tmp_output,
            expected_tools={"get_users", "post_users", "get_status"},
            expected_strategy="http_call",
            min_tools=8,
        )

        # Hash-rocket routes should be extracted
        tool_names = _get_tool_names(manifest)
        assert any("legacy" in n or "items" in n for n in tool_names), (
            f"Expected legacy/items routes from => syntax, got: {tool_names}"
        )
        # Namespaced routes
        assert any("orders" in n for n in tool_names), (
            f"Expected namespaced api/orders routes, got: {tool_names}"
        )


class TestRustAxum:
    """Integration test: Rust Axum web framework."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, fake_axum_app, tmp_output):
        manifest = await _run_pipeline(fake_axum_app, tmp_output)

        _full_assertions(
            manifest, tmp_output,
            expected_tools={"get_users", "post_users", "get_health"},
            expected_strategy="http_call",
            min_tools=4,
        )

        # Verify Axum routes have the right HTTP methods
        design = manifest.design
        http_tools = {t.name: t for t in design.tools if t.impl.strategy == "http_call"}
        assert "get_users" in http_tools
        assert http_tools["get_users"].impl.http_method == "GET"


class TestRustRocket:
    """Integration test: Rust Rocket web framework."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, fake_rocket_app, tmp_output):
        manifest = await _run_pipeline(fake_rocket_app, tmp_output)

        _full_assertions(
            manifest, tmp_output,
            expected_tools={"get_users", "post_users", "get_health"},
            expected_strategy="http_call",
            min_tools=4,
        )

        # Verify a parameterized route was extracted
        tool_names = _get_tool_names(manifest)
        # Rocket uses <id> syntax → should appear as get_users_by_id or similar
        assert any("by_id" in n or "user" in n for n in tool_names), (
            f"Expected user-parameterized tool, got: {tool_names}"
        )


# ---------------------------------------------------------------------------
# Tests — Additional Go backends (Echo, Chi, gorilla/mux, net/http)
# ---------------------------------------------------------------------------

class TestGoEcho:
    """Integration test: Go Echo web framework."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, fake_go_echo_app, tmp_output):
        manifest = await _run_pipeline(fake_go_echo_app, tmp_output)

        tool_names = _get_tool_names(manifest)
        assert any("users" in n for n in tool_names), (
            f"Expected user-related tools, got: {tool_names}"
        )
        assert len(tool_names) >= 4

        design = manifest.design
        pkg_name = _package_name(design.server_name)
        _assert_standard_structure(tmp_output, pkg_name)
        syntax_errors = _validate_python_syntax(tmp_output)
        assert syntax_errors == [], f"Syntax errors:\n" + "\n".join(syntax_errors)
        server_mod = _import_server(tmp_output, pkg_name)
        assert hasattr(server_mod, "server")


class TestGoChi:
    """Integration test: Go Chi web framework."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, fake_go_chi_app, tmp_output):
        manifest = await _run_pipeline(fake_go_chi_app, tmp_output)

        tool_names = _get_tool_names(manifest)
        assert any("users" in n for n in tool_names), (
            f"Expected user-related tools, got: {tool_names}"
        )
        assert len(tool_names) >= 4

        design = manifest.design
        pkg_name = _package_name(design.server_name)
        _assert_standard_structure(tmp_output, pkg_name)
        syntax_errors = _validate_python_syntax(tmp_output)
        assert syntax_errors == [], f"Syntax errors:\n" + "\n".join(syntax_errors)
        server_mod = _import_server(tmp_output, pkg_name)
        assert hasattr(server_mod, "server")


class TestGoMux:
    """Integration test: Go gorilla/mux web framework."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, fake_go_mux_app, tmp_output):
        manifest = await _run_pipeline(fake_go_mux_app, tmp_output)

        _full_assertions(
            manifest, tmp_output,
            expected_tools={"get_users", "post_users", "get_health"},
            expected_strategy="http_call",
            min_tools=4,
        )


class TestGoNetHTTP:
    """Integration test: Go standard net/http (no framework)."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, fake_go_nethttp_app, tmp_output):
        manifest = await _run_pipeline(fake_go_nethttp_app, tmp_output)

        tool_names = _get_tool_names(manifest)
        assert any("users" in n or "health" in n or "products" in n for n in tool_names), (
            f"Expected route tools, got: {tool_names}"
        )
        assert len(tool_names) >= 3

        design = manifest.design
        pkg_name = _package_name(design.server_name)
        _assert_standard_structure(tmp_output, pkg_name)
        syntax_errors = _validate_python_syntax(tmp_output)
        assert syntax_errors == [], f"Syntax errors:\n" + "\n".join(syntax_errors)
        server_mod = _import_server(tmp_output, pkg_name)
        assert hasattr(server_mod, "server")


# ---------------------------------------------------------------------------
# Tests — Socket / XML-RPC backend
# ---------------------------------------------------------------------------

class TestSocketXMLRPC:
    """Integration test: Python XML-RPC server via SimpleXMLRPCServer."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, fake_socket_xmlrpc_app, tmp_output):
        manifest = await _run_pipeline(fake_socket_xmlrpc_app, tmp_output)

        # XML-RPC should be detected as SOCKET IPC
        assert manifest.analysis is not None
        mechanisms = [m.ipc_type.value for m in manifest.analysis.ipc_mechanisms]
        assert "socket" in mechanisms, f"Expected socket IPC, got: {mechanisms}"

        # Should produce tools from the registered functions
        tool_names = _get_tool_names(manifest)
        assert len(tool_names) >= 4, f"Expected >= 4 tools, got: {tool_names}"
        assert any("item" in n for n in tool_names), (
            f"Expected item-related tools, got: {tool_names}"
        )

        # Structure and syntax valid
        design = manifest.design
        pkg_name = _package_name(design.server_name)
        _assert_standard_structure(tmp_output, pkg_name)
        syntax_errors = _validate_python_syntax(tmp_output)
        assert syntax_errors == [], f"Syntax errors:\n" + "\n".join(syntax_errors)
        server_mod = _import_server(tmp_output, pkg_name)
        assert hasattr(server_mod, "server")

# ---------------------------------------------------------------------------
# Tests — Kotlin backends (Spring, JAX-RS)
# ---------------------------------------------------------------------------

class TestKotlinSpring:
    """Integration test: Kotlin + Spring Boot REST controller."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, fake_kotlin_spring_app, tmp_output):
        manifest = await _run_pipeline(fake_kotlin_spring_app, tmp_output)

        _full_assertions(
            manifest, tmp_output,
            expected_tools={"get_users", "post_users"},
            expected_strategy="http_call",
            min_tools=4,
        )

        tool_names = _get_tool_names(manifest)
        assert any("by_id" in n for n in tool_names), (
            f"Expected path-param tool (by_id), got: {tool_names}"
        )


class TestKotlinJaxRS:
    """Integration test: Kotlin + JAX-RS resource."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, fake_kotlin_jaxrs_app, tmp_output):
        manifest = await _run_pipeline(fake_kotlin_jaxrs_app, tmp_output)

        _full_assertions(
            manifest, tmp_output,
            expected_tools={"get_items", "post_items"},
            expected_strategy="http_call",
            min_tools=4,
        )

        tool_names = _get_tool_names(manifest)
        assert any("by_id" in n for n in tool_names), (
            f"Expected path-param tool (by_id), got: {tool_names}"
        )


# ---------------------------------------------------------------------------
# Tests — Spring MVC (separate from Spring Boot)
# ---------------------------------------------------------------------------

class TestSpringMVC:
    """Integration test: Spring MVC REST controller."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, fake_spring_mvc_app, tmp_output):
        manifest = await _run_pipeline(fake_spring_mvc_app, tmp_output)

        _full_assertions(
            manifest, tmp_output,
            expected_tools={"get_products", "post_products"},
            expected_strategy="http_call",
            min_tools=3,
        )


# ---------------------------------------------------------------------------
# Tests — TypeScript Express
# ---------------------------------------------------------------------------

class TestTypeScriptExpress:
    """Integration test: TypeScript Express server."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, fake_ts_express_app, tmp_output):
        manifest = await _run_pipeline(fake_ts_express_app, tmp_output)

        _full_assertions(
            manifest, tmp_output,
            expected_tools={"get_products", "post_orders"},
            expected_strategy="http_call",
            min_tools=4,
        )

        tool_names = _get_tool_names(manifest)
        assert any("by_id" in n or "users" in n for n in tool_names), (
            f"Expected parameterized or users tool, got: {tool_names}"
        )


# ---------------------------------------------------------------------------
# Tests — Python Click CLI
# ---------------------------------------------------------------------------

class TestPythonClick:
    """Integration test: Python Click CLI application."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, fake_click_app, tmp_output):
        manifest = await _run_pipeline(fake_click_app, tmp_output)

        _full_assertions(
            manifest, tmp_output,
            expected_tools={"fetch", "convert"},
            expected_strategy="cli_subcommand",
            min_tools=2,
        )

        assert manifest.analysis is not None
        ipc_types = {m.ipc_type for m in manifest.analysis.ipc_mechanisms}
        assert any("cli" in str(t).lower() for t in ipc_types), (
            f"Expected CLI IPC detection, got: {ipc_types}"
        )


# ---------------------------------------------------------------------------
# Tests — Rust Warp
# ---------------------------------------------------------------------------

class TestRustWarp:
    """Integration test: Rust Warp web framework."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, fake_warp_app, tmp_output):
        manifest = await _run_pipeline(fake_warp_app, tmp_output)

        tool_names = _get_tool_names(manifest)
        assert len(tool_names) >= 3, f"Expected >= 3 tools, got: {tool_names}"
        assert any("users" in n or "health" in n or "products" in n for n in tool_names), (
            f"Expected route-named tools, got: {tool_names}"
        )

        design = manifest.design
        pkg_name = _package_name(design.server_name)
        _assert_standard_structure(tmp_output, pkg_name)
        syntax_errors = _validate_python_syntax(tmp_output)
        assert syntax_errors == [], "Syntax errors:\n" + "\n".join(syntax_errors)
        server_mod = _import_server(tmp_output, pkg_name)
        assert hasattr(server_mod, "server")


# ---------------------------------------------------------------------------
# Tests — mcp-use TypeScript target
# ---------------------------------------------------------------------------

async def _run_pipeline_mcp_use(
    codebase_path: Path,
    output_dir: Path,
    *,
    name: str | None = None,
) -> GenerationManifest:
    """Run the full pipeline with --target mcp-use and return the manifest."""
    options = CLIOptions(
        codebase_path=codebase_path,
        output_dir=output_dir,
        name=name,
        no_llm=True,
        no_install=True,
        target="mcp-use",
    )
    console = Console(quiet=True)
    engine = PipelineEngine(options, console)
    await engine.run()

    manifest_path = output_dir / "mcp-anything-manifest.json"
    assert manifest_path.exists(), "Manifest file not created"
    return GenerationManifest.load(manifest_path)


def _assert_mcp_use_structure(output_dir: Path) -> None:
    """Assert expected TypeScript output files exist."""
    assert (output_dir / "src" / "server.ts").exists(), "src/server.ts missing"
    assert (output_dir / "package.json").exists(), "package.json missing"
    assert (output_dir / "tsconfig.json").exists(), "tsconfig.json missing"
    assert (output_dir / "mcp.json").exists(), "mcp.json missing"
    assert (output_dir / "AGENTS.md").exists(), "AGENTS.md missing"


class TestMcpUseHttp:
    """Integration test: mcp-use TypeScript target with HTTP tools (Flask fixture)."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, fake_flask_app, tmp_output):
        manifest = await _run_pipeline_mcp_use(fake_flask_app, tmp_output)

        assert manifest.completed_phases == [
            "analyze", "design", "implement", "document", "package"
        ], f"Phases: {manifest.completed_phases}"
        assert manifest.errors == [], f"Pipeline errors: {manifest.errors}"

        design = manifest.design
        assert design is not None
        assert len(design.tools) >= 2

        tool_names = _get_tool_names(manifest)
        assert "get_users" in tool_names or "get_items" in tool_names or any(
            "get" in n for n in tool_names
        ), f"Expected HTTP GET tools, got: {tool_names}"

        for tool in design.tools:
            assert tool.impl.strategy == "http_call", (
                f"Tool {tool.name}: expected http_call, got {tool.impl.strategy}"
            )

        _assert_mcp_use_structure(tmp_output)

        # server.ts must reference mcp-use and each tool name
        server_ts = (tmp_output / "src" / "server.ts").read_text()
        assert "mcp-use/server" in server_ts
        assert "MCPServer" in server_ts
        assert "server.tool(" in server_ts
        assert "await server.listen(3000)" in server_ts
        for name in tool_names:
            assert name in server_ts, f"Tool name {name!r} missing from server.ts"

        # package.json must depend on mcp-use
        import json
        pkg = json.loads((tmp_output / "package.json").read_text())
        assert "mcp-use" in pkg["dependencies"]

        # AGENTS.md must mention TypeScript runtime note
        agents_md = (tmp_output / "AGENTS.md").read_text()
        assert "npm" in agents_md

    @pytest.mark.asyncio
    async def test_no_python_files_generated(self, fake_flask_app, tmp_output):
        await _run_pipeline_mcp_use(fake_flask_app, tmp_output)

        python_files = list(tmp_output.rglob("*.py"))
        # Only allow conftest/setup files — no generated server Python modules
        generated_py = [
            f for f in python_files
            if f.name not in ("setup.py",) and "mcp_" in str(f)
        ]
        assert generated_py == [], (
            f"mcp-use target should not generate Python server files: {generated_py}"
        )


class TestMcpUseCLI:
    """Integration test: mcp-use TypeScript target with CLI tools (argparse fixture)."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, fake_cli_app, tmp_output):
        manifest = await _run_pipeline_mcp_use(fake_cli_app, tmp_output)

        assert manifest.completed_phases == [
            "analyze", "design", "implement", "document", "package"
        ], f"Phases: {manifest.completed_phases}"
        assert manifest.errors == [], f"Pipeline errors: {manifest.errors}"

        design = manifest.design
        assert design is not None
        assert len(design.tools) >= 1

        for tool in design.tools:
            assert tool.impl.strategy in ("cli_subcommand", "cli_function"), (
                f"Tool {tool.name}: expected CLI strategy, got {tool.impl.strategy}"
            )

        _assert_mcp_use_structure(tmp_output)

        server_ts = (tmp_output / "src" / "server.ts").read_text()
        assert "execAsync" in server_ts, "CLI tools must use execAsync"
        assert "BINARY_PATH" in server_ts, "CLI tools must reference BINARY_PATH"
        assert "await server.listen(3000)" in server_ts
