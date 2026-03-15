"""Tests for Go web framework detector and analyzer."""

from mcp_anything.analysis.detectors.go_web_detector import GoWebDetector
from mcp_anything.analysis.go_analyzer import (
    analyze_go_file,
    go_results_to_capabilities,
)
from mcp_anything.analysis.scanner import scan_codebase
from mcp_anything.models.analysis import IPCType


class TestGoWebDetector:
    def test_detects_gin(self, fake_go_app):
        detector = GoWebDetector()
        files = scan_codebase(fake_go_app)
        mechanisms = detector.detect(fake_go_app, files)
        assert len(mechanisms) == 1
        assert mechanisms[0].ipc_type == IPCType.PROTOCOL
        assert mechanisms[0].details["framework"] == "gin"
        assert mechanisms[0].confidence >= 0.85

    def test_detects_port(self, fake_go_app):
        detector = GoWebDetector()
        files = scan_codebase(fake_go_app)
        mechanisms = detector.detect(fake_go_app, files)
        assert mechanisms[0].details["port"] == "8080"

    def test_no_detection_on_python(self, fake_cli_app):
        detector = GoWebDetector()
        files = scan_codebase(fake_cli_app)
        mechanisms = detector.detect(fake_cli_app, files)
        assert len(mechanisms) == 0


class TestGoAnalyzer:
    def test_finds_gin_routes(self, fake_go_app):
        files = scan_codebase(fake_go_app)
        results = {}
        for fi in files:
            result = analyze_go_file(fake_go_app, fi)
            if result and result.routes:
                results[fi.path] = result

        all_routes = []
        for r in results.values():
            all_routes.extend(r.routes)
        # health + 5 user routes
        assert len(all_routes) >= 6

    def test_extracts_http_methods(self, fake_go_app):
        files = scan_codebase(fake_go_app)
        methods = set()
        for fi in files:
            result = analyze_go_file(fake_go_app, fi)
            if result:
                for route in result.routes:
                    methods.add(route.http_method)
        assert "GET" in methods
        assert "POST" in methods
        assert "PUT" in methods
        assert "DELETE" in methods

    def test_handles_route_groups(self, fake_go_app):
        files = scan_codebase(fake_go_app)
        paths = set()
        for fi in files:
            result = analyze_go_file(fake_go_app, fi)
            if result:
                for route in result.routes:
                    paths.add(route.path)
        # Should have prefixed paths from the group
        assert any("/api/v1/users" in p for p in paths)

    def test_extracts_path_params(self, fake_go_app):
        files = scan_codebase(fake_go_app)
        has_path_param = False
        for fi in files:
            result = analyze_go_file(fake_go_app, fi)
            if result:
                for route in result.routes:
                    if "{id}" in route.path:
                        has_path_param = True
        assert has_path_param


class TestGoCapabilities:
    def test_endpoints_become_capabilities(self, fake_go_app):
        files = scan_codebase(fake_go_app)
        results = {}
        for fi in files:
            result = analyze_go_file(fake_go_app, fi)
            if result and result.routes:
                results[fi.path] = result

        caps = go_results_to_capabilities(results)
        assert len(caps) >= 6
        assert all(c.ipc_type == IPCType.PROTOCOL for c in caps)
