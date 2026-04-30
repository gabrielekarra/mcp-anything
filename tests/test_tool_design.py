"""Tests for Phase 2: ToolDesignPhase."""

import asyncio
from pathlib import Path

import pytest
import yaml

from mcp_anything.config import CLIOptions
from mcp_anything.models.design import ServerDesign, ToolGroup
from mcp_anything.models.domain import DomainModel, GlossaryTerm, UseCase
from mcp_anything.models.manifest import GenerationManifest
from mcp_anything.pipeline.context import PipelineContext
from mcp_anything.pipeline.tool_design import ToolDesignPhase, _parse_tool_spec
from rich.console import Console


@pytest.fixture
def domain_model() -> DomainModel:
    return DomainModel(
        server_name="task-manager",
        domain_description="Manages tasks and projects.",
        use_cases=[
            UseCase(id="uc-01", description="List all tasks in a project", actor="agent"),
            UseCase(id="uc-02", description="Create a new task", actor="agent"),
            UseCase(id="uc-03", description="Update task status", actor="agent"),
        ],
        glossary=[
            GlossaryTerm(term="Task", definition="A unit of work"),
            GlossaryTerm(term="Project", definition="A container for tasks"),
        ],
        domain_entities=["Task", "Project"],
        access_patterns=["List tasks by status", "Create task with assignee"],
        approved=True,
    )


@pytest.fixture
def ctx(tmp_path, domain_model) -> PipelineContext:
    opts = CLIOptions(
        codebase_path=tmp_path,
        output_dir=tmp_path / "output",
        name="task-manager",
        no_llm=True,
    )
    manifest = GenerationManifest(
        pipeline_mode="domain",
        codebase_path=str(tmp_path),
        output_dir=str(tmp_path / "output"),
        server_name="task-manager",
        domain_model=domain_model.model_dump(),
    )
    return PipelineContext(opts, manifest, Console(quiet=True))


def test_fallback_design_creates_tools(ctx):
    phase = ToolDesignPhase()
    asyncio.run(phase.execute(ctx))

    assert ctx.manifest.tool_spec is not None
    design = ServerDesign.model_validate(ctx.manifest.tool_spec)
    assert design.server_name == "task-manager"
    assert len(design.tools) > 0


def test_tool_spec_yaml_written(ctx, tmp_path):
    phase = ToolDesignPhase()
    asyncio.run(phase.execute(ctx))

    spec_path = tmp_path / "output" / "tool_spec.yaml"
    assert spec_path.exists()
    data = yaml.safe_load(spec_path.read_text())
    assert "tools" in data


def test_descriptions_yaml_written(ctx, tmp_path):
    phase = ToolDesignPhase()
    asyncio.run(phase.execute(ctx))

    desc_path = tmp_path / "output" / "descriptions.yaml"
    assert desc_path.exists()
    data = yaml.safe_load(desc_path.read_text())
    assert isinstance(data, dict)


def test_requires_domain_model():
    opts = CLIOptions(codebase_path=Path("."), no_llm=True)
    manifest = GenerationManifest(
        pipeline_mode="domain", codebase_path=".", output_dir=".", server_name="test"
    )
    ctx = PipelineContext(opts, manifest, Console(quiet=True))
    phase = ToolDesignPhase()
    errors = phase.validate_preconditions(ctx)
    assert len(errors) == 1
    assert "domain model" in errors[0].lower()


def test_parse_tool_spec_adds_verbose_param():
    data = {
        "server_name": "test",
        "server_description": "Test server",
        "tools": [
            {
                "name": "list_tasks",
                "description": "Returns all tasks in a project filtered by status.",
                "parameters": [
                    {"name": "project_id", "type": "string", "required": True}
                ],
                "impl": {"strategy": "http_call", "http_method": "GET", "http_path": "/tasks"},
            }
        ],
        "tool_groups": [],
        "composed_tools": [],
        "dependencies": ["mcp>=1.0"],
        "transport": "stdio",
    }
    design = _parse_tool_spec(data)
    param_names = {p.name for p in design.tools[0].parameters}
    assert "verbose" in param_names


def test_parse_tool_spec_discovery_and_telemetry():
    data = {
        "server_name": "test",
        "tools": [],
        "tool_groups": [],
        "composed_tools": [],
    }
    design = _parse_tool_spec(data)
    assert design.discovery_endpoint is True
    assert design.enable_telemetry is True


def test_fallback_design_derives_http_tools_from_openapi(tmp_path):
    """--no-llm fallback should walk OpenAPI paths and emit real http_call tools, not stubs."""
    from mcp_anything.models.domain import DataSource, DomainModel, UseCase

    domain_model = DomainModel(
        server_name="petstore",
        domain_description="Petstore",
        use_cases=[UseCase(id="uc-01", description="List pets", actor="agent")],
        data_sources=[DataSource(
            kind="openapi",
            path="<unused>",
            parsed_raw={
                "openapi": "3.0.0",
                "servers": [{"url": "https://api.example.com/v1"}],
                "paths": {
                    "/pets": {
                        "get": {"operationId": "listPets", "summary": "List all pets"},
                        "post": {"operationId": "createPet", "summary": "Create a pet"},
                    },
                    "/pets/{petId}": {
                        "get": {
                            "operationId": "getPetById",
                            "parameters": [{"name": "petId", "in": "path", "required": True,
                                            "schema": {"type": "string"}}],
                        }
                    },
                },
            },
        )],
        approved=True,
    )
    opts = CLIOptions(codebase_path=tmp_path, output_dir=tmp_path / "out", name="petstore", no_llm=True)
    manifest = GenerationManifest(
        pipeline_mode="domain", codebase_path=str(tmp_path), output_dir=str(tmp_path / "out"),
        server_name="petstore", domain_model=domain_model.model_dump(),
    )
    ctx = PipelineContext(opts, manifest, Console(quiet=True))

    asyncio.run(ToolDesignPhase().execute(ctx))

    design = ServerDesign.model_validate(ctx.manifest.tool_spec)
    names = {t.name for t in design.tools}
    assert names == {"listpets", "createpet", "getpetbyid"}
    # Real http_call strategy, no stubs:
    for t in design.tools:
        assert t.impl.strategy == "http_call", f"{t.name} should be http_call, got {t.impl.strategy}"
        assert t.impl.http_method
        assert t.impl.http_path
    assert design.backend_base_url == "https://api.example.com/v1"


def test_fallback_design_derives_grpc_tools_from_proto(tmp_path):
    """--no-llm fallback should parse a .proto and emit real grpc_call tools."""
    from mcp_anything.models.domain import DataSource, DomainModel, UseCase

    proto_path = tmp_path / "greeter.proto"
    proto_path.write_text('''
syntax = "proto3";
service Greeter {
  rpc SayHello (HelloRequest) returns (HelloReply);
  rpc SayGoodbye (HelloRequest) returns (HelloReply);
}
message HelloRequest { string name = 1; }
message HelloReply { string message = 1; }
''')
    domain_model = DomainModel(
        server_name="greeter",
        use_cases=[UseCase(id="uc-01", description="Greet", actor="agent")],
        data_sources=[DataSource(kind="grpc", path=str(proto_path))],
        approved=True,
    )
    opts = CLIOptions(codebase_path=tmp_path, output_dir=tmp_path / "out", name="greeter", no_llm=True)
    manifest = GenerationManifest(
        pipeline_mode="domain", codebase_path=str(tmp_path), output_dir=str(tmp_path / "out"),
        server_name="greeter", domain_model=domain_model.model_dump(),
    )
    ctx = PipelineContext(opts, manifest, Console(quiet=True))

    asyncio.run(ToolDesignPhase().execute(ctx))

    design = ServerDesign.model_validate(ctx.manifest.tool_spec)
    names = {t.name for t in design.tools}
    assert names == {"say_hello", "say_goodbye"}
    for t in design.tools:
        assert t.impl.strategy == "grpc_call"
        assert t.impl.grpc_service == "Greeter"
        assert t.impl.grpc_proto_module == "greeter"
        assert t.impl.grpc_request_type == "HelloRequest"
        assert t.impl.grpc_response_type == "HelloReply"
        assert "name" in {p.name for p in t.parameters}


def test_tool_design_2026_rules_group_crud():
    """Group-CRUD: if LLM returns tool_groups, they are preserved in ServerDesign."""
    data = {
        "server_name": "task-manager",
        "tools": [
            {
                "name": "manage_task",
                "description": "Creates, reads, updates, deletes, or lists tasks in a project.",
                "parameters": [
                    {"name": "operation", "type": "string", "required": True,
                     "description": "One of: create, read, update, delete, list"},
                    {"name": "project_id", "type": "string", "required": True},
                ],
                "impl": {"strategy": "http_call", "http_method": "GET", "http_path": "/tasks"},
            }
        ],
        "tool_groups": [
            {"name": "manage_task", "description": "CRUD for tasks", "operations": ["create","read","update","delete","list"]}
        ],
        "composed_tools": [],
    }
    design = _parse_tool_spec(data)
    assert len(design.tool_groups) == 1
    assert design.tool_groups[0].name == "manage_task"
    assert "create" in design.tool_groups[0].operations
