"""Tests for GraphQL detection and analysis."""

from pathlib import Path

import pytest

from mcp_anything.analysis.detectors.graphql_detector import GraphQLDetector
from mcp_anything.analysis.graphql_analyzer import (
    analyze_graphql_file,
    graphql_results_to_capabilities,
)
from mcp_anything.analysis.scanner import scan_codebase
from mcp_anything.models.analysis import IPCType


@pytest.fixture
def fake_graphql_app(fixtures_dir) -> Path:
    return fixtures_dir / "fake_graphql_app"


# ── Detector ──


class TestGraphQLDetector:
    def test_detects_graphql(self, fake_graphql_app):
        files = scan_codebase(fake_graphql_app)
        detector = GraphQLDetector()
        mechs = detector.detect(fake_graphql_app, files)
        assert len(mechs) == 1
        assert mechs[0].ipc_type == IPCType.PROTOCOL
        assert mechs[0].details["protocol"] == "graphql"
        assert mechs[0].confidence >= 0.9

    def test_no_detection_on_python(self, fake_cli_app):
        files = scan_codebase(fake_cli_app)
        detector = GraphQLDetector()
        mechs = detector.detect(fake_cli_app, files)
        assert len(mechs) == 0


# ── Analyzer ──


class TestGraphQLAnalyzer:
    def _analyze(self, fake_graphql_app):
        files = scan_codebase(fake_graphql_app)
        results = {}
        for fi in files:
            result = analyze_graphql_file(fake_graphql_app, fi)
            if result is not None:
                results[fi.path] = result
        return results

    def test_finds_queries(self, fake_graphql_app):
        results = self._analyze(fake_graphql_app)
        all_queries = [q for r in results.values() for q in r.queries]
        assert len(all_queries) == 4

    def test_finds_mutations(self, fake_graphql_app):
        results = self._analyze(fake_graphql_app)
        all_mutations = [m for r in results.values() for m in r.mutations]
        assert len(all_mutations) == 4

    def test_extracts_query_args(self, fake_graphql_app):
        results = self._analyze(fake_graphql_app)
        all_queries = [q for r in results.values() for q in r.queries]
        user_query = next(q for q in all_queries if q.name == "user")
        assert len(user_query.args) == 1
        assert user_query.args[0].name == "id"
        assert user_query.args[0].type == "string"
        assert user_query.args[0].required is True

    def test_maps_graphql_types(self, fake_graphql_app):
        results = self._analyze(fake_graphql_app)
        all_queries = [q for r in results.values() for q in r.queries]
        users_query = next(q for q in all_queries if q.name == "users")
        arg_types = {a.name: a.type for a in users_query.args}
        assert arg_types["limit"] == "integer"
        assert arg_types["offset"] == "integer"

        # Check type mapping on mutations as well (String -> string).
        all_mutations = [m for r in results.values() for m in r.mutations]
        create_user = next(m for m in all_mutations if m.name == "createUser")
        name_arg = next(a for a in create_user.args if a.name == "name")
        assert name_arg.type == "string"


# ── Capabilities ──


class TestGraphQLCapabilities:
    def test_queries_and_mutations_become_capabilities(self, fake_graphql_app):
        files = scan_codebase(fake_graphql_app)
        results = {}
        for fi in files:
            result = analyze_graphql_file(fake_graphql_app, fi)
            if result is not None:
                results[fi.path] = result
        caps = graphql_results_to_capabilities(results)
        assert len(caps) >= 8
        categories = {c.category for c in caps}
        assert "graphql_query" in categories
        assert "graphql_mutation" in categories
        for cap in caps:
            assert cap.ipc_type == IPCType.PROTOCOL
