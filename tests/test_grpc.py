"""Tests for gRPC detection and proto file analysis."""

from pathlib import Path

import pytest

from mcp_anything.analysis.detectors.grpc_detector import GRPCDetector
from mcp_anything.analysis.grpc_analyzer import (
    analyze_proto_file,
    grpc_results_to_capabilities,
    parse_proto_file,
)
from mcp_anything.analysis.scanner import scan_codebase
from mcp_anything.models.analysis import Language


@pytest.fixture
def fake_grpc_app(fixtures_dir) -> Path:
    return fixtures_dir / "fake_grpc_app"


# ── Detector tests ───────────────────────────────────────────────────────────


class TestGRPCDetector:
    def test_detects_grpc(self, fake_grpc_app):
        files = scan_codebase(fake_grpc_app)
        detector = GRPCDetector()
        mechanisms = detector.detect(fake_grpc_app, files)
        assert len(mechanisms) == 1
        assert mechanisms[0].details.get("protocol") == "grpc"
        assert mechanisms[0].confidence >= 0.9

    def test_no_detection_on_python(self, fake_cli_app):
        files = scan_codebase(fake_cli_app)
        detector = GRPCDetector()
        mechanisms = detector.detect(fake_cli_app, files)
        assert len(mechanisms) == 0


# ── Analyzer tests ───────────────────────────────────────────────────────────


class TestGRPCAnalyzer:
    def _get_result(self, fake_grpc_app):
        files = scan_codebase(fake_grpc_app)
        proto_files = [f for f in files if f.language == Language.PROTOBUF]
        assert len(proto_files) >= 1
        result = analyze_proto_file(fake_grpc_app, proto_files[0])
        assert result is not None
        return result

    def test_finds_services(self, fake_grpc_app):
        result = self._get_result(fake_grpc_app)
        assert len(result.services) == 1
        assert result.services[0].name == "UserService"

    def test_finds_rpc_methods(self, fake_grpc_app):
        result = self._get_result(fake_grpc_app)
        methods = result.services[0].methods
        assert len(methods) == 6
        method_names = {m.name for m in methods}
        assert "GetUser" in method_names
        assert "ListUsers" in method_names
        assert "CreateUser" in method_names
        assert "UpdateUser" in method_names
        assert "DeleteUser" in method_names
        assert "StreamUsers" in method_names

    def test_finds_messages(self, fake_grpc_app):
        result = self._get_result(fake_grpc_app)
        assert len(result.messages) == 8

    def test_detects_streaming(self, fake_grpc_app):
        result = self._get_result(fake_grpc_app)
        stream_method = [
            m for m in result.services[0].methods if m.name == "StreamUsers"
        ]
        assert len(stream_method) == 1
        assert stream_method[0].server_streaming is True
        assert stream_method[0].client_streaming is False

    def test_extracts_message_fields(self, fake_grpc_app):
        result = self._get_result(fake_grpc_app)
        user_msg = result.messages["User"]
        assert len(user_msg.fields) == 4
        field_names = {f.name for f in user_msg.fields}
        assert field_names == {"id", "name", "email", "age"}


# ── Capability conversion tests ──────────────────────────────────────────────


class TestGRPCCapabilities:
    def test_methods_become_capabilities(self, fake_grpc_app):
        files = scan_codebase(fake_grpc_app)
        proto_files = [f for f in files if f.language == Language.PROTOBUF]
        results = {}
        for pf in proto_files:
            analysis = analyze_proto_file(fake_grpc_app, pf)
            if analysis:
                results[pf.path] = analysis

        capabilities = grpc_results_to_capabilities(results)
        assert len(capabilities) == 6
        cap_names = {c.name for c in capabilities}
        assert "UserService.GetUser" in cap_names
        assert "UserService.StreamUsers" in cap_names
        for cap in capabilities:
            assert cap.category == "grpc"
