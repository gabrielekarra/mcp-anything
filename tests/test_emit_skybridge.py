"""Unit tests for the TypeScript/Skybridge emitter."""

import json
import tempfile
from pathlib import Path

import pytest

from mcp_anything.emit.base import EmitPhase
from mcp_anything.emit.typescript_skybridge.phase import TypeScriptSkybridgeEmitter, _to_pascal
from mcp_anything.models.analysis import IPCType, ParameterSpec
from mcp_anything.models.design import (
    BackendConfig,
    ServerDesign,
    ToolGroup,
    ToolImpl,
    ToolSpec,
)
from mcp_anything.models.domain import DomainModel, GlossaryTerm, UseCase


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_design(tools: list[ToolSpec] | None = None) -> ServerDesign:
    if tools is None:
        tools = [
            ToolSpec(
                name="list_items",
                description="Returns a paginated list of inventory items.",
                parameters=[
                    ParameterSpec(name="page", type="integer", required=False, description="Page number"),
                    ParameterSpec(name="limit", type="integer", required=False, description="Items per page"),
                ],
                return_type="object",
                impl=ToolImpl(
                    strategy="http_call",
                    http_method="GET",
                    http_path="/api/items",
                ),
            ),
            ToolSpec(
                name="create_item",
                description="Creates a new inventory item.",
                parameters=[
                    ParameterSpec(name="name", type="string", required=True, description="Item name"),
                    ParameterSpec(name="quantity", type="integer", required=True, description="Initial quantity"),
                ],
                return_type="object",
                impl=ToolImpl(
                    strategy="http_call",
                    http_method="POST",
                    http_path="/api/items",
                    arg_mapping={
                        "name": {"style": "body", "api_name": "name"},
                        "quantity": {"style": "body", "api_name": "quantity"},
                    },
                ),
            ),
        ]
    return ServerDesign(
        server_name="inventory-api",
        server_description="Inventory management MCP server.",
        tools=tools,
        tool_groups=[
            ToolGroup(name="items", disclosure_level="default", operations=["list_items", "create_item"]),
        ],
        backend=BackendConfig(backend_type=IPCType.PROTOCOL, host="localhost", port=8000),
        transport="stdio",
    )


def _make_domain_model() -> DomainModel:
    return DomainModel(
        server_name="inventory-api",
        domain_description="An inventory management system for warehouse operations.",
        use_cases=[
            UseCase(id="uc1", description="List all available items in the warehouse.", actor="agent"),
            UseCase(id="uc2", description="Create a new item when stock arrives.", actor="agent"),
        ],
        glossary=[
            GlossaryTerm(term="SKU", definition="Stock Keeping Unit — unique product identifier"),
        ],
    )


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _run_emitter(
    design: ServerDesign | None = None,
    domain: DomainModel | None = None,
    use_llm: bool = False,
) -> tuple[TypeScriptSkybridgeEmitter, Path]:
    if design is None:
        design = _make_design()
    # Use mkdtemp so the directory survives the function return for the caller to inspect.
    tmp = Path(tempfile.mkdtemp())
    out = tmp / "skybridge"
    out.mkdir(parents=True)
    emitter = TypeScriptSkybridgeEmitter(design, domain, out, use_llm=use_llm)
    emitter.emit_all()
    return emitter, out


# ---------------------------------------------------------------------------
# Directory layout
# ---------------------------------------------------------------------------

class TestDirectoryLayout:
    def test_expected_files_created(self) -> None:
        _, out = _run_emitter()
        assert (out / "src" / "server.ts").exists()
        assert (out / "src" / "discovery.ts").exists()
        assert (out / "src" / "telemetry.ts").exists()
        assert (out / "vite.config.ts").exists()
        assert (out / "index.html").exists()
        assert (out / "Dockerfile").exists()
        assert (out / "package.json").exists()
        assert (out / "tsconfig.json").exists()
        assert (out / "README.md").exists()

    def test_view_per_tool(self) -> None:
        design = _make_design()
        _, out = _run_emitter(design)
        for tool in design.tools:
            assert (out / "src" / "views" / f"{tool.name}.tsx").exists(), (
                f"Missing view for tool {tool.name}"
            )


# ---------------------------------------------------------------------------
# server.ts content
# ---------------------------------------------------------------------------

class TestServerTs:
    def test_skybridge_import(self) -> None:
        _, out = _run_emitter()
        content = (out / "src" / "server.ts").read_text()
        assert 'skybridge' in content

    def test_register_tool_calls(self) -> None:
        design = _make_design()
        _, out = _run_emitter(design)
        content = (out / "src" / "server.ts").read_text()
        for tool in design.tools:
            assert f'name: "{tool.name}"' in content

    def test_view_path_referenced_in_view(self) -> None:
        design = _make_design()
        _, out = _run_emitter(design)
        for tool in design.tools:
            assert (out / "src" / "views" / f"{tool.name}.tsx").exists()

    def test_server_name_in_server_ts(self) -> None:
        _, out = _run_emitter()
        content = (out / "src" / "server.ts").read_text()
        assert "inventory-api" in content

    def test_run_called(self) -> None:
        _, out = _run_emitter()
        content = (out / "src" / "server.ts").read_text()
        assert "server.run()" in content

    def test_discovery_resource(self) -> None:
        _, out = _run_emitter()
        content = (out / "src" / "server.ts").read_text()
        assert "mcp-discovery" in content
        assert "/.well-known/mcp" in content


# ---------------------------------------------------------------------------
# package.json
# ---------------------------------------------------------------------------

class TestPackageJson:
    def test_skybridge_dependency(self) -> None:
        _, out = _run_emitter()
        pkg = json.loads((out / "package.json").read_text())
        assert "skybridge" in pkg["dependencies"]

    def test_zod_dependency(self) -> None:
        _, out = _run_emitter()
        pkg = json.loads((out / "package.json").read_text())
        assert "zod" in pkg["dependencies"]

    def test_node_engine_requirement(self) -> None:
        _, out = _run_emitter()
        pkg = json.loads((out / "package.json").read_text())
        assert "22" in pkg["engines"]["node"]

    def test_dev_script(self) -> None:
        _, out = _run_emitter()
        pkg = json.loads((out / "package.json").read_text())
        assert "dev" in pkg["scripts"]

    def test_start_script(self) -> None:
        _, out = _run_emitter()
        pkg = json.loads((out / "package.json").read_text())
        assert "start" in pkg["scripts"]


# ---------------------------------------------------------------------------
# tsconfig.json
# ---------------------------------------------------------------------------

class TestTsConfig:
    def test_jsx_support(self) -> None:
        _, out = _run_emitter()
        tsconfig = json.loads((out / "tsconfig.json").read_text())
        assert tsconfig["compilerOptions"]["jsx"] in ("react-jsx", "react")

    def test_strict_mode(self) -> None:
        _, out = _run_emitter()
        tsconfig = json.loads((out / "tsconfig.json").read_text())
        assert tsconfig["compilerOptions"]["strict"] is True


# ---------------------------------------------------------------------------
# Placeholder views
# ---------------------------------------------------------------------------

class TestPlaceholderViews:
    def test_skybridge_client_import(self) -> None:
        _, out = _run_emitter(use_llm=False)
        for tsx in (out / "src" / "views").iterdir():
            content = tsx.read_text()
            assert "skybridge/web" in content

    def test_mount_view_called(self) -> None:
        _, out = _run_emitter(use_llm=False)
        for tsx in (out / "src" / "views").iterdir():
            content = tsx.read_text()
            assert "mountView(" in content

    def test_use_call_tool_hook(self) -> None:
        _, out = _run_emitter(use_llm=False)
        for tsx in (out / "src" / "views").iterdir():
            content = tsx.read_text()
            assert "useCallTool" in content
            assert "mountView" in content

    def test_all_states_handled(self) -> None:
        _, out = _run_emitter(use_llm=False)
        for tsx in (out / "src" / "views").iterdir():
            content = tsx.read_text()
            assert '"idle"' in content
            assert '"pending"' in content
            assert '"error"' in content

    def test_default_export(self) -> None:
        _, out = _run_emitter(use_llm=False)
        for tsx in (out / "src" / "views").iterdir():
            content = tsx.read_text()
            assert "export default" in content


# ---------------------------------------------------------------------------
# Vite config
# ---------------------------------------------------------------------------

class TestViteConfig:
    def test_skybridge_vite_plugin(self) -> None:
        _, out = _run_emitter()
        content = (out / "vite.config.ts").read_text()
        assert "skybridge/vite" in content


# ---------------------------------------------------------------------------
# Dockerfile
# ---------------------------------------------------------------------------

class TestDockerfile:
    def test_node_22(self) -> None:
        _, out = _run_emitter()
        content = (out / "Dockerfile").read_text()
        assert "node:22" in content


# ---------------------------------------------------------------------------
# Zod schema rendering
# ---------------------------------------------------------------------------

class TestZodSchema:
    def test_required_param_no_optional(self) -> None:
        tool = ToolSpec(
            name="get_user",
            description="Get a user by ID.",
            parameters=[
                ParameterSpec(name="user_id", type="string", required=True, description="User ID"),
            ],
            impl=ToolImpl(strategy="stub"),
        )
        design = _make_design(tools=[tool])
        _, out = _run_emitter(design)
        content = (out / "src" / "server.ts").read_text()
        assert "z.string()" in content
        assert ".optional()" not in content.split("user_id")[1].split("\n")[0]

    def test_optional_param_has_optional(self) -> None:
        tool = ToolSpec(
            name="search",
            description="Search items.",
            parameters=[
                ParameterSpec(name="query", type="string", required=False, description="Search query"),
            ],
            impl=ToolImpl(strategy="stub"),
        )
        design = _make_design(tools=[tool])
        _, out = _run_emitter(design)
        content = (out / "src" / "server.ts").read_text()
        assert ".optional()" in content


# ---------------------------------------------------------------------------
# HTTP call rendering
# ---------------------------------------------------------------------------

class TestHttpCallRendering:
    def test_http_method_in_fetch(self) -> None:
        _, out = _run_emitter()
        content = (out / "src" / "server.ts").read_text()
        assert 'method: "GET"' in content
        assert 'method: "POST"' in content

    def test_base_url_env_var(self) -> None:
        _, out = _run_emitter()
        content = (out / "src" / "server.ts").read_text()
        assert "INVENTORY_API_BASE_URL" in content


# ---------------------------------------------------------------------------
# Contract validation
# ---------------------------------------------------------------------------

class TestContractValidation:
    def test_no_critical_contract_failures(self) -> None:
        design = _make_design()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "skybridge"
            out.mkdir(parents=True)
            emitter = TypeScriptSkybridgeEmitter(design, None, out, use_llm=False)
            emitter.emit_all()

            class _TmpPhase(EmitPhase):
                name = "_test"
                backend_target = "skybridge"
                async def execute(self, ctx): pass

            results = _TmpPhase().validate_contract(design, out)
            # C-17 (Dockerfile) must pass
            dockerfile_check = next((r for r in results if r.id == "C-17"), None)
            if dockerfile_check:
                assert dockerfile_check.passed, f"Dockerfile contract check failed: {dockerfile_check}"


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

class TestUtility:
    def test_to_pascal(self) -> None:
        assert _to_pascal("list_items") == "ListItems"
        assert _to_pascal("get-user") == "GetUser"
        assert _to_pascal("single") == "Single"

    def test_generated_files_tracked(self) -> None:
        design = _make_design()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "skybridge"
            out.mkdir(parents=True)
            emitter = TypeScriptSkybridgeEmitter(design, None, out, use_llm=False)
            generated = emitter.emit_all()
            assert "src/server.ts" in generated
            assert "package.json" in generated
            assert all(f"src/views/{t.name}.tsx" in generated for t in design.tools)
