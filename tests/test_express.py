"""Tests for Express.js detector and analyzer."""

from mcp_anything.analysis.detectors.express_detector import ExpressDetector
from mcp_anything.analysis.express_analyzer import (
    analyze_express_file,
    express_results_to_capabilities,
)
from mcp_anything.analysis.scanner import scan_codebase
from mcp_anything.models.analysis import IPCType


class TestExpressDetector:
    def test_detects_express(self, fake_express_app):
        detector = ExpressDetector()
        files = scan_codebase(fake_express_app)
        mechanisms = detector.detect(fake_express_app, files)
        assert len(mechanisms) == 1
        assert mechanisms[0].ipc_type == IPCType.PROTOCOL
        assert mechanisms[0].details["framework"] == "express"
        assert mechanisms[0].confidence >= 0.85

    def test_detects_port(self, fake_express_app):
        detector = ExpressDetector()
        files = scan_codebase(fake_express_app)
        mechanisms = detector.detect(fake_express_app, files)
        assert mechanisms[0].details["port"] == "3000"

    def test_no_detection_on_spring(self, fake_spring_app):
        detector = ExpressDetector()
        files = scan_codebase(fake_spring_app)
        mechanisms = detector.detect(fake_spring_app, files)
        assert len(mechanisms) == 0


class TestExpressAnalyzer:
    def test_finds_routes(self, fake_express_app):
        files = scan_codebase(fake_express_app)
        results = {}
        for fi in files:
            result = analyze_express_file(fake_express_app, fi)
            if result and result.routes:
                results[fi.path] = result

        all_routes = []
        for r in results.values():
            all_routes.extend(r.routes)
        assert len(all_routes) >= 4  # At least health + products routes

    def test_extracts_http_methods(self, fake_express_app):
        files = scan_codebase(fake_express_app)
        methods = set()
        for fi in files:
            result = analyze_express_file(fake_express_app, fi)
            if result:
                for route in result.routes:
                    methods.add(route.http_method)
        assert "GET" in methods
        assert "POST" in methods

    def test_extracts_path_params(self, fake_express_app):
        files = scan_codebase(fake_express_app)
        has_path_param = False
        for fi in files:
            result = analyze_express_file(fake_express_app, fi)
            if result:
                for route in result.routes:
                    if "{id}" in route.path:
                        has_path_param = True
                        id_params = [p for p in route.parameters if p.name == "id"]
                        assert len(id_params) == 1
                        assert id_params[0].required
        assert has_path_param


class TestExpressCapabilities:
    def test_endpoints_become_capabilities(self, fake_express_app):
        files = scan_codebase(fake_express_app)
        results = {}
        for fi in files:
            result = analyze_express_file(fake_express_app, fi)
            if result and result.routes:
                results[fi.path] = result

        caps = express_results_to_capabilities(results)
        assert len(caps) >= 4
        assert all(c.ipc_type == IPCType.PROTOCOL for c in caps)
        assert all(c.category == "api" for c in caps)
