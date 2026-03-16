"""Tests for Spring Boot support — detector, analyzer, and codegen."""

import ast
from pathlib import Path

import pytest

from mcp_anything.analysis.detectors.spring_detector import SpringDetector
from mcp_anything.analysis.java_analyzer import (
    JavaAnalysisResult,
    analyze_java_file,
    java_results_to_capabilities,
)
from mcp_anything.analysis.scanner import scan_codebase
from mcp_anything.codegen.emitter import Emitter
from mcp_anything.models.analysis import FileInfo, IPCType, Language, ParameterSpec
from mcp_anything.models.design import BackendConfig, ResourceSpec, ServerDesign, ToolImpl, ToolSpec


class TestSpringDetector:
    def test_detects_spring_boot(self, fake_spring_app):
        files = scan_codebase(fake_spring_app)
        detector = SpringDetector()
        mechanisms = detector.detect(fake_spring_app, files)

        assert len(mechanisms) == 1
        mech = mechanisms[0]
        assert mech.ipc_type == IPCType.PROTOCOL
        assert mech.confidence >= 0.9
        assert mech.details["protocol"] == "http"
        assert mech.details["framework"] == "spring-boot"

    def test_detects_port(self, fake_spring_app):
        files = scan_codebase(fake_spring_app)
        detector = SpringDetector()
        mechanisms = detector.detect(fake_spring_app, files)

        assert mechanisms[0].details["port"] == "8080"

    def test_finds_rest_controller_evidence(self, fake_spring_app):
        files = scan_codebase(fake_spring_app)
        detector = SpringDetector()
        mechanisms = detector.detect(fake_spring_app, files)

        evidence = mechanisms[0].evidence
        evidence_text = " ".join(evidence)
        assert "REST controller" in evidence_text
        assert "Spring Boot" in evidence_text

    def test_no_detection_on_non_spring(self, fake_cli_app):
        files = scan_codebase(fake_cli_app)
        detector = SpringDetector()
        mechanisms = detector.detect(fake_cli_app, files)
        assert mechanisms == []


class TestJavaAnalyzer:
    def test_finds_endpoints(self, fake_spring_app):
        fi = FileInfo(
            path="src/main/java/com/example/demo/UserController.java",
            language=Language.JAVA,
            size_bytes=500,
            line_count=30,
        )
        result = analyze_java_file(fake_spring_app, fi)

        assert result is not None
        assert len(result.endpoints) >= 5
        assert "UserController" in result.controllers

    def test_extracts_http_methods(self, fake_spring_app):
        fi = FileInfo(
            path="src/main/java/com/example/demo/UserController.java",
            language=Language.JAVA,
            size_bytes=500,
            line_count=30,
        )
        result = analyze_java_file(fake_spring_app, fi)

        methods = {ep.http_method for ep in result.endpoints}
        assert "GET" in methods
        assert "POST" in methods
        assert "PUT" in methods
        assert "DELETE" in methods

    def test_extracts_paths(self, fake_spring_app):
        fi = FileInfo(
            path="src/main/java/com/example/demo/UserController.java",
            language=Language.JAVA,
            size_bytes=500,
            line_count=30,
        )
        result = analyze_java_file(fake_spring_app, fi)

        paths = {ep.path for ep in result.endpoints}
        assert "/api/users" in paths
        assert "/api/users/{id}" in paths
        assert "/api/users/search" in paths

    def test_extracts_parameters(self, fake_spring_app):
        fi = FileInfo(
            path="src/main/java/com/example/demo/UserController.java",
            language=Language.JAVA,
            size_bytes=500,
            line_count=30,
        )
        result = analyze_java_file(fake_spring_app, fi)

        # Find the getUserById endpoint
        get_by_id = next(
            ep for ep in result.endpoints
            if ep.method_name == "getUserById"
        )
        assert len(get_by_id.parameters) == 1
        assert get_by_id.parameters[0].name == "id"
        assert get_by_id.parameters[0].type == "integer"
        assert get_by_id.parameters[0].required is True

    def test_extracts_request_params(self, fake_spring_app):
        fi = FileInfo(
            path="src/main/java/com/example/demo/UserController.java",
            language=Language.JAVA,
            size_bytes=500,
            line_count=30,
        )
        result = analyze_java_file(fake_spring_app, fi)

        search = next(
            ep for ep in result.endpoints
            if ep.method_name == "searchUsers"
        )
        param_names = [p.name for p in search.parameters]
        assert "query" in param_names
        assert "limit" in param_names

        query_param = next(p for p in search.parameters if p.name == "query")
        assert query_param.required is True

        limit_param = next(p for p in search.parameters if p.name == "limit")
        assert limit_param.required is False
        assert limit_param.default == "10"

    def test_detects_spring_boot_application(self, fake_spring_app):
        fi = FileInfo(
            path="src/main/java/com/example/demo/DemoApplication.java",
            language=Language.JAVA,
            size_bytes=200,
            line_count=10,
        )
        result = analyze_java_file(fake_spring_app, fi)
        assert result is not None
        assert result.has_spring_boot is True

    def test_skips_non_java(self, fake_spring_app):
        fi = FileInfo(path="foo.py", language=Language.PYTHON, size_bytes=100, line_count=10)
        result = analyze_java_file(fake_spring_app, fi)
        assert result is None


class TestJavaCapabilities:
    def test_endpoints_become_capabilities(self, fake_spring_app):
        fi = FileInfo(
            path="src/main/java/com/example/demo/UserController.java",
            language=Language.JAVA,
            size_bytes=500,
            line_count=30,
        )
        result = analyze_java_file(fake_spring_app, fi)
        caps = java_results_to_capabilities({fi.path: result})

        assert len(caps) >= 5
        cap_names = [c.name for c in caps]
        # Should generate names like get_users, get_users_by_id, post_users, etc.
        assert any("get" in n and "users" in n for n in cap_names)
        assert any("post" in n and "users" in n for n in cap_names)
        assert any("delete" in n and "users" in n for n in cap_names)

    def test_capabilities_have_correct_ipc_type(self, fake_spring_app):
        fi = FileInfo(
            path="src/main/java/com/example/demo/UserController.java",
            language=Language.JAVA,
            size_bytes=500,
            line_count=30,
        )
        result = analyze_java_file(fake_spring_app, fi)
        caps = java_results_to_capabilities({fi.path: result})

        for cap in caps:
            assert cap.ipc_type == IPCType.PROTOCOL
            assert cap.category == "api"


class TestSpringBootCodegen:
    @pytest.fixture
    def spring_design(self) -> ServerDesign:
        return ServerDesign(
            server_name="demo-api",
            server_description="Spring Boot demo API MCP server",
            tools=[
                ToolSpec(
                    name="get_users",
                    description="GET /api/users - Get all users",
                    parameters=[
                        ParameterSpec(name="role", type="string", description="Filter by role", required=False),
                    ],
                    return_type="string",
                    module="api",
                    ipc_type=IPCType.PROTOCOL,
                    impl=ToolImpl(
                        strategy="http_call",
                        http_method="GET",
                        http_path="/api/users",
                        arg_mapping={"role": {"style": "query"}},
                    ),
                ),
                ToolSpec(
                    name="get_users_by_id",
                    description="GET /api/users/{id} - Get user by ID",
                    parameters=[
                        ParameterSpec(name="id", type="integer", description="User ID", required=True),
                    ],
                    return_type="string",
                    module="api",
                    ipc_type=IPCType.PROTOCOL,
                    impl=ToolImpl(
                        strategy="http_call",
                        http_method="GET",
                        http_path="/api/users/{id}",
                        arg_mapping={"id": {"style": "path"}},
                    ),
                ),
                ToolSpec(
                    name="post_users",
                    description="POST /api/users - Create a user",
                    parameters=[
                        ParameterSpec(name="userData", type="object", description="User data", required=True),
                    ],
                    return_type="string",
                    module="api",
                    ipc_type=IPCType.PROTOCOL,
                    impl=ToolImpl(
                        strategy="http_call",
                        http_method="POST",
                        http_path="/api/users",
                        arg_mapping={"userData": {"style": "body"}},
                    ),
                ),
            ],
            resources=[
                ResourceSpec(
                    uri="app://demo-api/status",
                    name="demo_api_status",
                    description="API status",
                    resource_type="status",
                ),
            ],
            tool_modules={"api": ["get_users", "get_users_by_id", "post_users"]},
            backend=BackendConfig(
                backend_type=IPCType.PROTOCOL,
                host="localhost",
                port=8080,
                env_vars={"PROTOCOL": "http"},
            ),
            dependencies=["mcp>=1.0", "httpx>=0.27"],
        )

    def test_generates_valid_python(self, spring_design, tmp_path):
        emitter = Emitter(spring_design, tmp_path)
        files = emitter.emit_all()

        # All .py files should parse
        for rel in files:
            if rel.endswith(".py"):
                content = (tmp_path / rel).read_text()
                ast.parse(content)

    def test_generates_http_backend(self, spring_design, tmp_path):
        emitter = Emitter(spring_design, tmp_path)
        emitter.emit_all()

        backend_path = tmp_path / "src" / "mcp_demo_api" / "backend.py"
        assert backend_path.exists()
        content = backend_path.read_text()
        assert "httpx" in content
        assert "localhost" in content
        assert "8080" in content

    def test_generates_http_call_tools(self, spring_design, tmp_path):
        emitter = Emitter(spring_design, tmp_path)
        emitter.emit_all()

        tool_path = tmp_path / "src" / "mcp_demo_api" / "tools" / "api.py"
        assert tool_path.exists()
        content = tool_path.read_text()
        assert "backend.request" in content
        assert "/api/users" in content
        assert "GET" in content
        assert "POST" in content
