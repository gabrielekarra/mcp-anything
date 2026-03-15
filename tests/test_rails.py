"""Tests for Ruby on Rails detector and analyzer."""

from mcp_anything.analysis.detectors.rails_detector import RailsDetector
from mcp_anything.analysis.rails_analyzer import (
    analyze_rails_routes,
    rails_results_to_capabilities,
)
from mcp_anything.analysis.scanner import scan_codebase
from mcp_anything.models.analysis import IPCType


class TestRailsDetector:
    def test_detects_rails(self, fake_rails_app):
        detector = RailsDetector()
        files = scan_codebase(fake_rails_app)
        mechanisms = detector.detect(fake_rails_app, files)
        assert len(mechanisms) == 1
        assert mechanisms[0].ipc_type == IPCType.PROTOCOL
        assert mechanisms[0].details["framework"] == "rails"

    def test_no_detection_on_python(self, fake_cli_app):
        detector = RailsDetector()
        files = scan_codebase(fake_cli_app)
        mechanisms = detector.detect(fake_cli_app, files)
        assert len(mechanisms) == 0


class TestRailsAnalyzer:
    def test_parses_routes_rb(self, fake_rails_app):
        result = analyze_rails_routes(fake_rails_app)
        assert result is not None
        # resources :users (5 actions) + resources :posts only: 3 + get health = 9
        assert len(result.routes) >= 8

    def test_extracts_http_methods(self, fake_rails_app):
        result = analyze_rails_routes(fake_rails_app)
        methods = {r.http_method for r in result.routes}
        assert "GET" in methods
        assert "POST" in methods
        assert "PUT" in methods
        assert "DELETE" in methods

    def test_namespace_prefix(self, fake_rails_app):
        result = analyze_rails_routes(fake_rails_app)
        paths = {r.path for r in result.routes}
        # All routes should have /api prefix from namespace
        assert all(p.startswith("/api") for p in paths)

    def test_only_constraint(self, fake_rails_app):
        result = analyze_rails_routes(fake_rails_app)
        post_routes = [r for r in result.routes if "posts" in r.path]
        post_methods = {r.action_name for r in post_routes}
        assert "index" in post_methods
        assert "show" in post_methods
        assert "create" in post_methods
        assert "update" not in post_methods
        assert "destroy" not in post_methods

    def test_explicit_routes(self, fake_rails_app):
        result = analyze_rails_routes(fake_rails_app)
        health_routes = [r for r in result.routes if "health" in r.path]
        assert len(health_routes) == 1
        assert health_routes[0].http_method == "GET"


class TestRailsCapabilities:
    def test_routes_become_capabilities(self, fake_rails_app):
        result = analyze_rails_routes(fake_rails_app)
        results = {"config/routes.rb": result}
        caps = rails_results_to_capabilities(results)
        assert len(caps) >= 8
        assert all(c.ipc_type == IPCType.PROTOCOL for c in caps)
