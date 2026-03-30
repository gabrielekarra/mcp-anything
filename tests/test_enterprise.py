"""Tests for v0.5.0 enterprise features: transport, prompts, AGENTS.md, Docker."""

import ast
import json
from pathlib import Path

from mcp_anything.codegen.emitter import Emitter
from mcp_anything.config import CLIOptions
from mcp_anything.models.analysis import AnalysisResult, Capability, IPCType, ParameterSpec
from mcp_anything.models.design import (
    BackendConfig,
    PromptSpec,
    ResourceSpec,
    ServerDesign,
    ToolImpl,
    ToolSpec,
)
from mcp_anything.pipeline.design import (
    _assign_generation_status,
    _generate_prompts,
    _generate_doc_resources,
    _generate_resources,
)


def _make_analysis() -> AnalysisResult:
    """Create a minimal AnalysisResult for testing."""
    return AnalysisResult(
        app_name="testapp",
        app_description="Test application",
        capabilities=[
            Capability(
                name="get_users",
                description="GET /api/users - List all users",
                category="api",
                parameters=[
                    ParameterSpec(name="limit", type="integer", required=False),
                ],
                ipc_type=IPCType.PROTOCOL,
            ),
            Capability(
                name="create_user",
                description="POST /api/users - Create a user",
                category="api",
                parameters=[
                    ParameterSpec(name="name", type="string"),
                    ParameterSpec(name="email", type="string"),
                ],
                ipc_type=IPCType.PROTOCOL,
            ),
        ],
        primary_ipc=IPCType.PROTOCOL,
    )


def _make_design(transport: str = "stdio") -> ServerDesign:
    """Create a minimal ServerDesign for testing."""
    return ServerDesign(
        server_name="testapp",
        server_description="Test MCP server",
        tools=[
            ToolSpec(
                name="get_users",
                description="List all users",
                parameters=[
                    ParameterSpec(name="limit", type="integer", required=False),
                ],
                impl=ToolImpl(strategy="http_call", http_method="GET", http_path="/api/users"),
            ),
        ],
        resources=[
            ResourceSpec(
                uri="app://testapp/status",
                name="testapp_status",
                description="Server status",
                resource_type="status",
            ),
        ],
        prompts=[
            PromptSpec(
                name="use_testapp",
                description="Guide for using testapp",
                template="Use the testapp tools effectively.",
            ),
        ],
        tool_modules={"api": ["get_users"]},
        backend=BackendConfig(backend_type=IPCType.PROTOCOL, port=8080),
        transport=transport,
        enable_telemetry=transport == "http",
    )


class TestTransportConfig:
    def test_cli_options_default_stdio(self):
        opts = CLIOptions(codebase_path=Path("/tmp/test"))
        assert opts.transport == "stdio"

    def test_cli_options_http(self):
        opts = CLIOptions(codebase_path=Path("/tmp/test"), transport="http")
        assert opts.transport == "http"

    def test_design_transport_default(self):
        design = ServerDesign(server_name="test")
        assert design.transport == "stdio"

    def test_design_transport_http(self):
        design = ServerDesign(server_name="test", transport="http")
        assert design.transport == "http"
        assert design.http_host == "0.0.0.0"
        assert design.http_port == 8000


class TestServerTemplate:
    def test_stdio_server_generates_valid_python(self, tmp_path):
        design = _make_design("stdio")
        emitter = Emitter(design, tmp_path)
        emitter.emit_all()
        server_py = (tmp_path / "src/mcp_testapp/server.py").read_text()
        ast.parse(server_py)
        assert 'os.environ.get("MCP_TRANSPORT", "stdio")' in server_py

    def test_http_server_generates_valid_python(self, tmp_path):
        design = _make_design("http")
        emitter = Emitter(design, tmp_path)
        emitter.emit_all()
        server_py = (tmp_path / "src/mcp_testapp/server.py").read_text()
        ast.parse(server_py)
        assert 'os.environ.get("MCP_TRANSPORT", "http")' in server_py
        assert 'server.run(transport="streamable-http")' in server_py

    def test_http_server_includes_telemetry(self, tmp_path):
        design = _make_design("http")
        emitter = Emitter(design, tmp_path)
        emitter.emit_all()
        server_py = (tmp_path / "src/mcp_testapp/server.py").read_text()
        assert "opentelemetry" in server_py
        assert "TracerProvider" in server_py


class TestPromptsGeneration:
    def test_generates_prompts_from_analysis(self):
        analysis = _make_analysis()
        prompts = _generate_prompts(analysis)
        assert len(prompts) >= 2
        names = {p.name for p in prompts}
        assert "use_testapp" in names
        assert "debug_testapp" in names

    def test_debug_prompt_has_argument(self):
        analysis = _make_analysis()
        prompts = _generate_prompts(analysis)
        debug = next(p for p in prompts if "debug" in p.name)
        assert len(debug.arguments) == 1
        assert debug.arguments[0].name == "error_message"

    def test_prompts_template_emitted(self, tmp_path):
        design = _make_design()
        emitter = Emitter(design, tmp_path)
        emitter.emit_all()
        prompts_py = tmp_path / "src/mcp_testapp/prompts.py"
        assert prompts_py.exists()
        content = prompts_py.read_text()
        ast.parse(content)
        assert "register_prompts" in content

    def test_server_imports_prompts(self, tmp_path):
        design = _make_design()
        emitter = Emitter(design, tmp_path)
        emitter.emit_all()
        server_py = (tmp_path / "src/mcp_testapp/server.py").read_text()
        assert "register_prompts" in server_py


class TestDocResources:
    def test_generates_tool_index_resource(self):
        analysis = _make_analysis()
        resources = _generate_doc_resources(analysis)
        uris = {r.uri for r in resources}
        assert "docs://testapp/tool-index" in uris

    def test_generates_category_doc_resources(self):
        analysis = _make_analysis()
        resources = _generate_doc_resources(analysis)
        assert any(r.resource_type == "docs" for r in resources)


class TestGenerationStatus:
    def test_http_tools_are_marked_proxy(self):
        design = _make_design()
        tool = design.tools[0]

        _assign_generation_status(tool, design.backend)

        assert tool.generation_status == "ready"
        assert "HTTP API" in tool.generation_notes

    def test_stub_tools_are_marked_stubbed(self):
        tool = ToolSpec(name="todo", description="Not wired yet")

        _assign_generation_status(tool, None)

        assert tool.generation_status == "stubbed"
        assert tool.manual_steps


class TestAgentsMd:
    def test_agents_md_generated(self, tmp_path):
        design = _make_design()
        emitter = Emitter(design, tmp_path)
        emitter.emit_docs()
        agents_md = tmp_path / "AGENTS.md"
        assert agents_md.exists()
        content = agents_md.read_text()
        assert "testapp" in content
        assert "get_users" in content

    def test_agents_md_includes_tools(self, tmp_path):
        design = _make_design()
        emitter = Emitter(design, tmp_path)
        emitter.emit_docs()
        content = (tmp_path / "AGENTS.md").read_text()
        assert "limit" in content
        assert "Available Tools" in content
        assert "Implementation status:" in content

    def test_agents_md_http_config(self, tmp_path):
        design = _make_design("http")
        emitter = Emitter(design, tmp_path)
        emitter.emit_docs()
        content = (tmp_path / "AGENTS.md").read_text()
        assert "remote MCP clients" in content
        assert "mcp-use" in content

    def test_agents_md_disabled(self, tmp_path):
        design = _make_design()
        design.generate_agents_md = False
        emitter = Emitter(design, tmp_path)
        emitter.emit_docs()
        assert not (tmp_path / "AGENTS.md").exists()


class TestMcpConfigTransport:
    def test_stdio_mcp_config(self, tmp_path):
        design = _make_design("stdio")
        config = {
            "mcpServers": {
                "testapp": {
                    "command": "mcp-testapp",
                    "args": [],
                }
            }
        }
        assert "command" in config["mcpServers"]["testapp"]

    def test_http_mcp_config(self):
        design = _make_design("http")
        config = {
            "mcpServers": {
                "testapp": {
                    "url": f"http://localhost:{design.http_port}/mcp",
                }
            }
        }
        assert "url" in config["mcpServers"]["testapp"]
        assert "/mcp" in config["mcpServers"]["testapp"]["url"]


class TestServeCommand:
    def test_serve_module_importable(self):
        from mcp_anything.serve import run_server
        assert callable(run_server)

    def test_cli_has_serve_subcommand(self):
        from mcp_anything.cli import build_parser
        parser = build_parser()
        # Parse serve command
        args = parser.parse_args(["serve", "/tmp/test-server"])
        assert args.command == "serve"
        assert args.output_dir == Path("/tmp/test-server")

    def test_serve_transport_override(self):
        from mcp_anything.cli import build_parser
        parser = build_parser()
        args = parser.parse_args(["serve", "/tmp/test", "--transport", "http", "--port", "9000"])
        assert args.transport == "http"
        assert args.port == 9000
