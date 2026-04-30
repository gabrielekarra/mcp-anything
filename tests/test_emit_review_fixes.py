"""Regression tests for reviewed code generation paths."""

import ast
import sys
from types import SimpleNamespace

import pytest

from mcp_anything.codegen.renderer import create_mcp_use_jinja_env
from mcp_anything.conformance.reporter import ConformanceReporter
from mcp_anything.conformance.runner import EvalRunner
from mcp_anything.emit.python_fastmcp.phase import PythonFastMCPEmitter
from mcp_anything.emit.python_fastmcp.phase import PythonFastMCPEmitPhase
from mcp_anything.emit.typescript_mcp_use.phase import TypeScriptMcpUseEmitter
from mcp_anything.models.analysis import ParameterSpec
from mcp_anything.models.design import ServerDesign, ToolImpl, ToolSpec
from mcp_anything.models.validation import ConformanceReport, EvalCase, EvalResult
from mcp_anything.pipeline.tool_design import _openapi_to_tool_specs, _proto_to_tool_specs


def test_python_fastmcp_grpc_uses_actual_request_message(tmp_path):
    design = ServerDesign(
        server_name="greeter",
        tools=[
            ToolSpec(
                name="say_hello",
                description="Send a greeting request.",
                parameters=[
                    ParameterSpec(name="name", type="string", description="Name to greet"),
                ],
                impl=ToolImpl(
                    strategy="grpc_call",
                    grpc_service="Greeter",
                    grpc_method="SayHello",
                    grpc_proto_module="greeter",
                    grpc_request_type="HelloRequest",
                    grpc_response_type="HelloReply",
                ),
            )
        ],
    )

    PythonFastMCPEmitter(design, tmp_path).emit_all()

    tool_source = (tmp_path / "mcp_greeter" / "tools" / "say_hello.py").read_text()
    assert "request_type_name = 'HelloRequest'" in tool_source
    assert "SayHelloRequest()" not in tool_source


def test_mcp_use_template_uses_exec_file_for_python_call_only():
    design = ServerDesign(
        server_name="py-only",
        tools=[
            ToolSpec(
                name="run_task",
                description="Run the Python task.",
                parameters=[],
                impl=ToolImpl(
                    strategy="python_call",
                    python_module="tasks",
                    python_function="run",
                ),
            )
        ],
    )

    template = create_mcp_use_jinja_env().get_template("server.ts.j2")
    rendered = template.render(
        design=design,
        has_cli_tools=False,
        has_http_tools=False,
        binary_default="py-only",
        http_base_url="http://localhost:8080",
        auth=None,
    )

    assert 'import { execFile } from "child_process";' in rendered
    assert "const execFileAsync = promisify(execFile);" in rendered
    assert "execFileAsync(_python" in rendered
    assert 'join(" ")' not in rendered
    assert "BINARY_PATH" not in rendered


def test_python_fastmcp_class_method_params_are_not_constructor_args(tmp_path):
    design = ServerDesign(
        server_name="classy",
        tools=[
            ToolSpec(
                name="run_task",
                description="Run an instance method.",
                parameters=[
                    ParameterSpec(name="payload", type="string", description="Payload"),
                ],
                impl=ToolImpl(
                    strategy="python_call",
                    python_module="tasks",
                    python_class="Runner",
                    python_function="run",
                ),
            )
        ],
    )

    PythonFastMCPEmitter(design, tmp_path).emit_all()

    tool_source = (tmp_path / "mcp_classy" / "tools" / "run_task.py").read_text()
    assert "_init_keys = []" in tool_source
    assert "method_args = {k: v for k, v in params.items() if k not in _init_keys" in tool_source
    assert "list(params.keys())" not in tool_source


def test_python_fastmcp_requires_grpcio_tools_for_grpc_stubs(monkeypatch, tmp_path):
    phase = PythonFastMCPEmitPhase()
    design = ServerDesign(
        server_name="greeter",
        tools=[
            ToolSpec(
                name="say_hello",
                description="Send a greeting request.",
                impl=ToolImpl(
                    strategy="grpc_call",
                    grpc_service="Greeter",
                    grpc_method="SayHello",
                    grpc_proto_module="greeter",
                ),
            )
        ],
    )
    ctx = SimpleNamespace(
        console=SimpleNamespace(print=lambda *args, **kwargs: None),
        manifest=SimpleNamespace(codebase_path=str(tmp_path)),
    )
    monkeypatch.setitem(sys.modules, "grpc_tools", None)

    with pytest.raises(RuntimeError, match="grpcio-tools"):
        phase._compile_proto_stubs(ctx, tmp_path, "mcp_greeter", design)


def test_openapi_fallback_models_body_and_sanitizes_api_names(tmp_path):
    spec = {
        "openapi": "3.0.0",
        "paths": {
            "/reports/{api-version}": {
                "post": {
                    "operationId": "createReport",
                    "parameters": [
                        {"name": "api-version", "in": "path", "required": True,
                         "schema": {"type": "string"}},
                        {"name": "from", "in": "query", "required": False,
                         "schema": {"type": "string"}},
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["title"],
                                    "properties": {
                                        "title": {"type": "string"},
                                        "display-name": {"type": "string"},
                                    },
                                }
                            }
                        },
                    },
                }
            }
        },
    }

    tools = _openapi_to_tool_specs(spec)
    tool = tools[0]
    params = {p.name: p for p in tool.parameters}

    assert {"api_version", "from_", "title", "display_name", "verbose"} == set(params)
    assert params["api_version"].api_name == "api-version"
    assert params["from_"].api_name == "from"
    assert params["display_name"].api_name == "display-name"
    assert tool.impl.arg_mapping["api_version"] == {"style": "path", "api_name": "api-version"}
    assert tool.impl.arg_mapping["from_"] == {"style": "query", "api_name": "from"}
    assert tool.impl.arg_mapping["display_name"] == {"style": "body", "api_name": "display-name"}

    design = ServerDesign(server_name="reports", tools=tools)
    PythonFastMCPEmitter(design, tmp_path).emit_all()
    tool_source = (tmp_path / "mcp_reports" / "tools" / "createreport.py").read_text()
    ast.parse(tool_source)
    assert '"api-version": api_version' in tool_source
    assert '"from": from_' in tool_source
    assert '"display-name": display_name' in tool_source
    assert "body_fields[key] = val" in tool_source


def test_mcp_use_template_emits_http_query_constants():
    design = ServerDesign(
        server_name="wiki",
        tools=[
            ToolSpec(
                name="search_pages",
                description="Search wiki pages.",
                parameters=[
                    ParameterSpec(name="q", type="string", description="Search text"),
                ],
                impl=ToolImpl(
                    strategy="http_call",
                    http_method="GET",
                    http_path="/api.php",
                    http_query_constants={"action": "query", "format": "json"},
                ),
            )
        ],
    )

    template = create_mcp_use_jinja_env().get_template("server.ts.j2")
    rendered = template.render(
        design=design,
        has_cli_tools=False,
        has_python_call_tools=False,
        has_http_tools=True,
        binary_default="wiki",
        http_base_url="https://wiki.example",
        auth=None,
    )

    assert '_url.searchParams.set("q", String(q));' in rendered
    assert '_url.searchParams.set("action", "query");' in rendered
    assert '_url.searchParams.set("format", "json");' in rendered


def test_proto_fallback_exposes_request_message_fields():
    spec = {
        "_proto_text": """
syntax = "proto3";
service Greeter {
  rpc SayHello (HelloRequest) returns (HelloReply);
}
message HelloRequest {
  string name = 1;
  int32 count = 2;
}
message HelloReply { string message = 1; }
"""
    }

    tools = _proto_to_tool_specs(spec, "greeter.proto")

    param_names = {p.name for p in tools[0].parameters}
    assert {"name", "count", "verbose"} == param_names
    assert tools[0].parameters[0].api_name == "name"


def test_typescript_emitter_emits_http_query_constants(tmp_path):
    design = ServerDesign(
        server_name="wiki",
        tools=[
            ToolSpec(
                name="search_pages",
                description="Search wiki pages.",
                parameters=[],
                impl=ToolImpl(
                    strategy="http_call",
                    http_method="GET",
                    http_path="/api.php",
                    http_query_constants={"action": "query", "format": "json"},
                ),
            )
        ],
    )

    TypeScriptMcpUseEmitter(design, tmp_path).emit_all()

    tool_source = (tmp_path / "src" / "tools" / "search_pages.ts").read_text()
    assert 'Object.entries({"action": "query", "format": "json"})' in tool_source
    assert "url.searchParams.set(k, String(v));" in tool_source


def test_eval_runner_and_reporter_mark_live_eval_results(monkeypatch, tmp_path):
    cases = [
        EvalCase(
            id="ec-001",
            brief_item_id="uc-001",
            tool_name="ping",
            input_params={},
        )
    ]
    runner = EvalRunner(tmp_path, run_live=True)
    monkeypatch.setattr(
        runner,
        "_run_live",
        lambda eval_cases: [EvalResult(case_id="ec-001", passed=True, actual_output="pong")],
    )

    report = runner.run(cases)

    assert report.eval_run is True
    assert "Eval coverage: 100.0%" in ConformanceReporter.to_ci_output(report)

    report_with_legacy_flag = ConformanceReport(
        server_name="server",
        backend_target="fastmcp",
        results=[EvalResult(case_id="ec-001", passed=True, actual_output="pong")],
        coverage_ratio=1.0,
        threshold=0.8,
        eval_run=False,
    )
    assert "Eval coverage: 100.0%" in ConformanceReporter.to_ci_output(report_with_legacy_flag)
