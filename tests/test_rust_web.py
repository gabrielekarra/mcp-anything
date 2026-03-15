"""Tests for Rust web framework detector and analyzer."""

from mcp_anything.analysis.detectors.rust_web_detector import RustWebDetector
from mcp_anything.analysis.rust_web_analyzer import (
    analyze_rust_web_file,
    rust_web_results_to_capabilities,
)
from mcp_anything.analysis.scanner import scan_codebase
from mcp_anything.models.analysis import IPCType


class TestRustWebDetector:
    def test_detects_actix(self, fake_rust_app):
        detector = RustWebDetector()
        files = scan_codebase(fake_rust_app)
        mechanisms = detector.detect(fake_rust_app, files)
        assert len(mechanisms) == 1
        assert mechanisms[0].ipc_type == IPCType.PROTOCOL
        assert mechanisms[0].details["framework"] == "actix"
        assert mechanisms[0].confidence >= 0.85

    def test_no_detection_on_python(self, fake_cli_app):
        detector = RustWebDetector()
        files = scan_codebase(fake_cli_app)
        mechanisms = detector.detect(fake_cli_app, files)
        assert len(mechanisms) == 0


class TestRustWebAnalyzer:
    def test_finds_actix_routes(self, fake_rust_app):
        files = scan_codebase(fake_rust_app)
        results = {}
        for fi in files:
            result = analyze_rust_web_file(fake_rust_app, fi)
            if result and result.routes:
                results[fi.path] = result

        all_routes = []
        for r in results.values():
            all_routes.extend(r.routes)
        # health + list + get + create + update + delete = 6
        assert len(all_routes) >= 6

    def test_extracts_http_methods(self, fake_rust_app):
        files = scan_codebase(fake_rust_app)
        methods = set()
        for fi in files:
            result = analyze_rust_web_file(fake_rust_app, fi)
            if result:
                for route in result.routes:
                    methods.add(route.http_method)
        assert "GET" in methods
        assert "POST" in methods
        assert "PUT" in methods
        assert "DELETE" in methods

    def test_extracts_path_params(self, fake_rust_app):
        files = scan_codebase(fake_rust_app)
        has_path_param = False
        for fi in files:
            result = analyze_rust_web_file(fake_rust_app, fi)
            if result:
                for route in result.routes:
                    if "{id}" in route.path:
                        has_path_param = True
        assert has_path_param


class TestRustWebCapabilities:
    def test_endpoints_become_capabilities(self, fake_rust_app):
        files = scan_codebase(fake_rust_app)
        results = {}
        for fi in files:
            result = analyze_rust_web_file(fake_rust_app, fi)
            if result and result.routes:
                results[fi.path] = result

        caps = rust_web_results_to_capabilities(results)
        assert len(caps) >= 6
        assert all(c.ipc_type == IPCType.PROTOCOL for c in caps)
