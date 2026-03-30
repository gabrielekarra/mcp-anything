"""Tests for code generation."""

import ast
import py_compile
from pathlib import Path

import pytest

from mcp_anything.codegen.emitter import Emitter
from mcp_anything.codegen.renderer import create_jinja_env
from mcp_anything.models.analysis import IPCType, ParameterSpec
from mcp_anything.models.design import BackendConfig, ResourceSpec, ServerDesign, ToolImpl, ToolSpec


@pytest.fixture
def sample_design() -> ServerDesign:
    return ServerDesign(
        server_name="test-app",
        server_description="A test application MCP server",
        tools=[
            ToolSpec(
                name="process_file",
                description="Process an input file",
                parameters=[
                    ParameterSpec(name="input_path", type="string", description="Input file"),
                    ParameterSpec(name="format", type="string", description="Output format", required=False),
                ],
                return_type="string",
                module="file_ops",
            ),
            ToolSpec(
                name="get_status",
                description="Get application status",
                parameters=[],
                return_type="string",
                module="general",
            ),
        ],
        resources=[
            ResourceSpec(
                uri="app://test-app/status",
                name="test_app_status",
                description="Current status",
            ),
        ],
        tool_modules={
            "file_ops": ["process_file"],
            "general": ["get_status"],
        },
        backend=BackendConfig(backend_type=IPCType.CLI, command="test-app"),
    )


class TestJinjaEnvironment:
    def test_env_creates(self):
        env = create_jinja_env()
        assert env is not None

    def test_snake_case_filter(self):
        env = create_jinja_env()
        assert env.filters["snake_case"]("MyClassName") == "my_class_name"
        assert env.filters["snake_case"]("some-kebab") == "some_kebab"

    def test_pascal_case_filter(self):
        env = create_jinja_env()
        assert env.filters["pascal_case"]("my_func") == "MyFunc"

    def test_kebab_case_filter(self):
        env = create_jinja_env()
        assert env.filters["kebab_case"]("my_app") == "my-app"

    def test_python_type_filter(self):
        env = create_jinja_env()
        f = env.filters["python_type"]
        assert f("string") == "str"
        assert f("integer") == "int"
        assert f("boolean") == "bool"
        # Unknown/complex types from target projects → str
        assert f("Callable") == "str"
        assert f("TokenList") == "str"
        assert f("DBCursor") == "str"
        assert f("Iterable") == "str"
        # Built-in types pass through
        assert f("str") == "str"
        assert f("int") == "int"
        assert f("list") == "list"

    def test_safe_docstring_filter(self):
        env = create_jinja_env()
        f = env.filters["safe_docstring"]
        # Normal string unchanged
        assert f("Hello world") == "Hello world"
        # Triple quotes escaped
        assert '"""' not in f('Has """triple quotes"""')
        # Backslashes escaped
        assert "\\\\" in f("Has \\n backslash")
        # Multi-line truncated to first line
        assert f("First line\nSecond line") == "First line"
        # Empty string handled
        assert f("") == ""


class TestEmitter:
    def test_emit_all(self, sample_design, tmp_path):
        emitter = Emitter(sample_design, tmp_path)
        files = emitter.emit_all()

        assert len(files) > 0
        assert any("server.py" in f for f in files)
        assert any("__init__.py" in f for f in files)

    def test_generated_server_is_valid_python(self, sample_design, tmp_path):
        emitter = Emitter(sample_design, tmp_path)
        emitter.emit_all()

        server_path = tmp_path / "src" / "mcp_test_app" / "server.py"
        assert server_path.exists()

        # Parse as Python — should not raise SyntaxError
        content = server_path.read_text()
        ast.parse(content)

    def test_generated_tools_valid_python(self, sample_design, tmp_path):
        emitter = Emitter(sample_design, tmp_path)
        emitter.emit_all()

        for module_name in sample_design.tool_modules:
            module_path = tmp_path / "src" / "mcp_test_app" / "tools" / f"{module_name}.py"
            assert module_path.exists()
            content = module_path.read_text()
            ast.parse(content)

    def test_emit_packaging(self, sample_design, tmp_path):
        emitter = Emitter(sample_design, tmp_path)
        files = emitter.emit_packaging()

        assert any("pyproject.toml" in f for f in files)
        pyproject = (tmp_path / "pyproject.toml").read_text()
        assert "mcp-test-app-server" in pyproject

    def test_emit_docs(self, sample_design, tmp_path):
        emitter = Emitter(sample_design, tmp_path)
        files = emitter.emit_docs()

        assert any("README.md" in f for f in files)
        readme = (tmp_path / "README.md").read_text()
        assert "process_file" in readme
        assert "Implementation status:" in readme
        assert "Status meanings:" in readme

    def test_backend_generated(self, sample_design, tmp_path):
        emitter = Emitter(sample_design, tmp_path)
        emitter.emit_all()

        backend_path = tmp_path / "src" / "mcp_test_app" / "backend.py"
        assert backend_path.exists()
        content = backend_path.read_text()
        ast.parse(content)

    def test_resources_valid_python(self, sample_design, tmp_path):
        emitter = Emitter(sample_design, tmp_path)
        emitter.emit_all()

        resources_path = tmp_path / "src" / "mcp_test_app" / "resources.py"
        assert resources_path.exists()
        content = resources_path.read_text()
        ast.parse(content)

    def test_mcp_config_generated(self, sample_design, tmp_path):
        """PackagePhase should generate mcp.json config."""
        import json
        from unittest.mock import MagicMock

        from mcp_anything.config import CLIOptions
        from mcp_anything.models.manifest import GenerationManifest
        from mcp_anything.pipeline.context import PipelineContext
        from mcp_anything.pipeline.package import PackagePhase

        # First emit package files so structure exists
        emitter = Emitter(sample_design, tmp_path)
        emitter.emit_all()
        emitter.emit_packaging()

        manifest = GenerationManifest(
            codebase_path="/tmp/fake",
            output_dir=str(tmp_path),
            server_name="test-app",
            design=sample_design,
            generated_files=[],
        )
        options = CLIOptions(codebase_path=Path("/tmp/fake"))
        console = MagicMock()
        ctx = PipelineContext(options, manifest, console)

        phase = PackagePhase()
        phase._install_dependencies = MagicMock(return_value=[])

        import asyncio
        asyncio.run(phase.execute(ctx))

        config_path = tmp_path / "mcp.json"
        assert config_path.exists()
        config = json.loads(config_path.read_text())
        assert "mcpServers" in config
        assert "test-app" in config["mcpServers"]
        assert config["mcpServers"]["test-app"]["command"] == "mcp-test-app"

    def test_mcp_config_includes_base_url_for_http_call_tools(self, tmp_path):
        import json

        design = ServerDesign(
            server_name="test-app",
            tools=[
                ToolSpec(
                    name="get_users",
                    description="Fetch users",
                    module="api",
                    impl=ToolImpl(strategy="http_call", http_method="GET", http_path="/users"),
                )
            ],
            tool_modules={"api": ["get_users"]},
            backend=BackendConfig(
                backend_type=IPCType.SOCKET,
                host="api.internal",
                port=9000,
            ),
        )

        emitter = Emitter(design, tmp_path)
        emitter.emit_packaging()

        config = json.loads((tmp_path / "mcp.json").read_text())
        server_cfg = config["mcpServers"]["test-app"]
        assert server_cfg["env"]["TEST_APP_BASE_URL"] == "http://api.internal:9000"

    def test_http_tool_module_does_not_shadow_body_param(self, tmp_path):
        design = ServerDesign(
            server_name="test-app",
            tools=[
                ToolSpec(
                    name="post_items",
                    description="Create item",
                    module="api",
                    parameters=[ParameterSpec(name="body", type="object", description="Request body")],
                    impl=ToolImpl(
                        strategy="http_call",
                        http_method="POST",
                        http_path="/items",
                        arg_mapping={"body": {"style": "body"}},
                    ),
                )
            ],
            tool_modules={"api": ["post_items"]},
            backend=BackendConfig(backend_type=IPCType.PROTOCOL, host="localhost", port=8080),
        )

        emitter = Emitter(design, tmp_path)
        emitter.emit_all()

        module = (tmp_path / "src" / "mcp_test_app" / "tools" / "api.py").read_text()
        assert "request_body" in module
        assert "body=request_body" in module

    def test_serve_fallback_preserves_env(self, tmp_path):
        import json
        from unittest.mock import MagicMock

        from mcp_anything.config import CLIOptions
        from mcp_anything.models.manifest import GenerationManifest
        from mcp_anything.pipeline.context import PipelineContext
        from mcp_anything.pipeline.package import PackagePhase

        design = ServerDesign(server_name="test-app")
        (tmp_path / "mcp.json").write_text(json.dumps({
            "mcpServers": {
                "test-app": {
                    "command": "mcp-test-app",
                    "args": [],
                    "env": {
                        "TEST_APP_BASE_URL": "http://api.internal:9000",
                        "TEST_APP_TOKEN": "<set-me>",
                    },
                }
            }
        }, indent=2) + "\n")

        manifest = GenerationManifest(
            codebase_path="/tmp/fake",
            output_dir=str(tmp_path),
            server_name="test-app",
            design=design,
            generated_files=[],
        )
        ctx = PipelineContext(CLIOptions(codebase_path=Path("/tmp/fake")), manifest, MagicMock())

        PackagePhase()._rewrite_mcp_json_for_serve(ctx, tmp_path)

        config = json.loads((tmp_path / "mcp.json").read_text())
        server_cfg = config["mcpServers"]["test-app"]
        assert server_cfg["command"] == "mcp-anything"
        assert server_cfg["args"] == ["serve", str(tmp_path)]
        assert server_cfg["env"]["TEST_APP_BASE_URL"] == "http://api.internal:9000"
        assert server_cfg["env"]["TEST_APP_TOKEN"] == "<set-me>"
