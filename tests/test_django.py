"""Tests for Django REST Framework detector and analyzer."""

from mcp_anything.analysis.detectors.django_detector import DjangoDetector
from mcp_anything.analysis.django_analyzer import (
    analyze_django_file,
    django_results_to_capabilities,
)
from mcp_anything.analysis.scanner import scan_codebase
from mcp_anything.models.analysis import IPCType


class TestDjangoDetector:
    def test_detects_django(self, fake_django_app):
        detector = DjangoDetector()
        files = scan_codebase(fake_django_app)
        mechanisms = detector.detect(fake_django_app, files)
        assert len(mechanisms) == 1
        assert mechanisms[0].ipc_type == IPCType.PROTOCOL
        assert mechanisms[0].details["framework"] == "django-rest-framework"
        assert mechanisms[0].confidence >= 0.85

    def test_no_detection_on_flask(self, fake_flask_app):
        detector = DjangoDetector()
        files = scan_codebase(fake_flask_app)
        mechanisms = detector.detect(fake_flask_app, files)
        assert len(mechanisms) == 0


class TestDjangoAnalyzer:
    def test_finds_viewset_endpoints(self, fake_django_app):
        files = scan_codebase(fake_django_app)
        results = {}
        for fi in files:
            result = analyze_django_file(fake_django_app, fi)
            if result and result.endpoints:
                results[fi.path] = result

        all_endpoints = []
        for r in results.values():
            all_endpoints.extend(r.endpoints)
        # Should find list, create, retrieve, update, destroy + 2 custom actions
        assert len(all_endpoints) >= 5

    def test_extracts_http_methods(self, fake_django_app):
        files = scan_codebase(fake_django_app)
        methods = set()
        for fi in files:
            result = analyze_django_file(fake_django_app, fi)
            if result:
                for ep in result.endpoints:
                    methods.add(ep.http_method)
        assert "GET" in methods
        assert "POST" in methods
        assert "PUT" in methods
        assert "DELETE" in methods

    def test_extracts_serializer_fields_as_params(self, fake_django_app):
        files = scan_codebase(fake_django_app)
        for fi in files:
            result = analyze_django_file(fake_django_app, fi)
            if result:
                create_eps = [e for e in result.endpoints if e.function_name == "create"]
                if create_eps:
                    param_names = {p.name for p in create_eps[0].parameters}
                    assert "name" in param_names
                    assert "email" in param_names

    def test_finds_custom_actions(self, fake_django_app):
        files = scan_codebase(fake_django_app)
        action_names = set()
        for fi in files:
            result = analyze_django_file(fake_django_app, fi)
            if result:
                for ep in result.endpoints:
                    action_names.add(ep.function_name)
        assert "activate" in action_names
        assert "active" in action_names


class TestDjangoCapabilities:
    def test_endpoints_become_capabilities(self, fake_django_app):
        files = scan_codebase(fake_django_app)
        results = {}
        for fi in files:
            result = analyze_django_file(fake_django_app, fi)
            if result and result.endpoints:
                results[fi.path] = result

        caps = django_results_to_capabilities(results)
        assert len(caps) >= 5
        assert all(c.ipc_type == IPCType.PROTOCOL for c in caps)
