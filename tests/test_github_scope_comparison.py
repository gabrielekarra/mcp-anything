"""End-to-end comparison: scope-filter our generated GitHub server to match
the official github/github-mcp-server's ~82 hand-curated tools.

This test proves that --scope-file can narrow 1,093 auto-generated tools
down to the same set the official server exposes — validating the scope
feature's real-world utility for large API surfaces.

The mapping is derived from:
  - Official tool names: pkg/github/__toolsnaps__/*.snap in github/github-mcp-server
  - Our tool names: OpenAPI operationId-based names from GitHub's REST API spec

Some official tools use GraphQL (discussions, projects) or Copilot-specific
APIs that don't appear in the REST OpenAPI spec — these are expected gaps.
"""

import ast
import json
import re
import sys
from pathlib import Path

import pytest
import yaml

from rich.console import Console

from mcp_anything.config import CLIOptions
from mcp_anything.models.analysis import AnalysisResult, Capability, IPCType
from mcp_anything.pipeline.engine import PipelineEngine
from mcp_anything.models.manifest import GenerationManifest
from mcp_anything.pipeline.scope import apply_scope


# ---------------------------------------------------------------------------
# Mapping: official GitHub MCP tool name → our OpenAPI-derived tool name
# None = no REST API equivalent (GraphQL-only, Copilot-specific, etc.)
# ---------------------------------------------------------------------------

OFFICIAL_TO_OURS = {
    # Context tools
    "get_me": "users_get_authenticated",
    "get_teams": "teams_list",
    "get_team_members": "teams_list_members_in_org",

    # Repository tools
    "search_repositories": "search_repos",
    "get_file_contents": "repos_get_content",
    "list_commits": "repos_list_commits",
    "search_code": "search_code",
    "get_commit": "repos_get_commit",
    "list_branches": "repos_list_branches",
    "list_tags": "repos_list_tags",
    "get_tag": "git_get_tag",
    "list_releases": "repos_list_releases",
    "get_latest_release": "repos_get_latest_release",
    "get_release_by_tag": "repos_get_release_by_tag",
    "create_or_update_file": "repos_create_or_update_file_contents",
    "create_repository": "repos_create_for_authenticated_user",
    "fork_repository": "repos_create_fork",
    "create_branch": "git_create_ref",
    "push_files": "repos_create_or_update_file_contents",  # composite in official
    "delete_file": "repos_delete_file",
    "list_starred_repositories": "activity_list_repos_starred_by_authenticated_user",
    "star_repository": "activity_star_repo_for_authenticated_user",
    "unstar_repository": "activity_unstar_repo_for_authenticated_user",

    # Git tools
    "get_repository_tree": "git_get_tree",

    # Issue tools
    "create_issue": "issues_create",
    "issue_read": "issues_get",
    "search_issues": "search_issues_and_pull_requests",
    "list_issues": "issues_list_for_repo",
    "list_issue_types": "orgs_list_issue_types",
    "issue_write": "issues_update",
    "add_issue_comment": "issues_create_comment",
    "sub_issue_write": "issues_add_sub_issue",

    # User tools
    "search_users": "search_users",

    # Organization tools
    "search_orgs": None,  # no direct REST match

    # Pull request tools
    "pull_request_read": "pulls_get",
    "list_pull_requests": "pulls_list",
    "search_pull_requests": "search_issues_and_pull_requests",  # shared endpoint
    "merge_pull_request": "pulls_merge",
    "update_pull_request_branch": "pulls_update_branch",
    "create_pull_request": "pulls_create",
    "update_pull_request": "pulls_update",
    "pull_request_review_write": "pulls_submit_review",
    "add_comment_to_pending_review": "pulls_create_review_comment",
    "add_reply_to_pull_request_comment": "pulls_create_reply_for_review_comment",

    # Copilot tools (not in REST API)
    "assign_copilot_to_issue": None,
    "request_copilot_review": None,

    # Code security tools
    "get_code_scanning_alert": "code_scanning_get_alert",
    "list_code_scanning_alerts": "code_scanning_list_alerts_for_repo",

    # Secret protection tools
    "get_secret_scanning_alert": "secret_scanning_get_alert",
    "list_secret_scanning_alerts": "secret_scanning_list_alerts_for_repo",

    # Dependabot tools
    "get_dependabot_alert": "dependabot_get_alert",
    "list_dependabot_alerts": "dependabot_list_alerts_for_repo",

    # Notification tools
    "list_notifications": "get_notifications",
    "get_notification_details": "activity_get_thread",
    "dismiss_notification": "activity_mark_thread_as_done",
    "mark_all_notifications_read": "activity_mark_notifications_as_read",
    "manage_notification_subscription": "activity_set_thread_subscription",
    "manage_repository_notification_subscription": "activity_set_repo_subscription",

    # Discussion tools (GraphQL only)
    "list_discussions": None,
    "get_discussion": None,
    "get_discussion_comments": None,
    "list_discussion_categories": None,

    # Actions tools
    "actions_list": "actions_list_repo_workflows",
    "actions_get": "actions_get_workflow",
    "actions_run_trigger": "actions_create_workflow_dispatch",
    "get_job_logs": "actions_download_job_logs_for_workflow_run",

    # Security advisories tools
    "list_global_security_advisories": "security_advisories_list_global_advisories",
    "get_global_security_advisory": "security_advisories_get_global_advisory",
    "list_repository_security_advisories": "security_advisories_list_repository_advisories",
    "list_org_repository_security_advisories": None,

    # Gist tools
    "list_gists": "gists_list",
    "get_gist": "gists_get",
    "create_gist": "gists_create",
    "update_gist": "gists_update",

    # Project tools (GraphQL only)
    "projects_list": None,
    "projects_get": None,
    "projects_write": None,

    # Label tools
    "get_label": "issues_get_label",
    "list_label": "issues_list_labels_for_repo",
    "label_write": "issues_create_label",
}

# Our tool names that correspond to official tools (deduplicated)
OUR_EXPECTED_TOOLS = {v for v in OFFICIAL_TO_OURS.values() if v is not None}

# Official tools that have no REST API equivalent
GRAPHQL_OR_COPILOT_ONLY = {k for k, v in OFFICIAL_TO_OURS.items() if v is None}

# Path to the generated GitHub server example
GITHUB_EXAMPLE = Path(__file__).parent.parent / "examples" / "github-server"
TOOLS_FILE = GITHUB_EXAMPLE / "src" / "mcp_github" / "tools" / "api.py"


def _extract_tool_names_from_code() -> set[str]:
    """Extract tool function names from the generated api.py without importing."""
    if not TOOLS_FILE.exists():
        return set()
    content = TOOLS_FILE.read_text()
    return set(re.findall(r"async def (\w+)\(", content))


def _build_synthetic_analysis(tool_names: set[str]) -> AnalysisResult:
    """Build a synthetic AnalysisResult from extracted tool names."""
    capabilities = [
        Capability(
            name=name,
            description=f"GitHub API: {name}",
            category="api",
            ipc_type=IPCType.PROTOCOL,
        )
        for name in sorted(tool_names)
    ]
    return AnalysisResult(
        app_name="github",
        app_description="GitHub REST API",
        capabilities=capabilities,
        primary_ipc=IPCType.PROTOCOL,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestGitHubMapping:
    """Validate the official→ours mapping is complete and correct."""

    def test_mapping_covers_all_80_official_tools(self):
        assert len(OFFICIAL_TO_OURS) == 80, (
            f"Expected 80 official tools, mapping has {len(OFFICIAL_TO_OURS)}"
        )

    def test_graphql_gaps_are_documented(self):
        expected_gaps = {
            "list_discussions", "get_discussion", "get_discussion_comments",
            "list_discussion_categories", "projects_list", "projects_get",
            "projects_write", "assign_copilot_to_issue", "request_copilot_review",
            "search_orgs", "list_org_repository_security_advisories",
        }
        assert GRAPHQL_OR_COPILOT_ONLY == expected_gaps

    def test_rest_coverage(self):
        """69 of 80 official tools have REST API equivalents."""
        rest_count = len(OFFICIAL_TO_OURS) - len(GRAPHQL_OR_COPILOT_ONLY)
        assert rest_count == 69, f"Expected 69 REST-mappable tools, got {rest_count}"

    def test_unique_tool_count(self):
        """Some official tools map to the same endpoint (deduplication)."""
        # push_files and create_or_update_file → same endpoint
        # search_issues and search_pull_requests → same endpoint
        assert len(OUR_EXPECTED_TOOLS) < 71, (
            "Expected deduplication from shared endpoints"
        )


@pytest.mark.skipif(
    not TOOLS_FILE.exists(),
    reason="examples/github-server not generated — run the GitHub example first",
)
class TestGitHubScopeComparison:
    """Prove scope filtering can narrow 1,093 tools to match the official set."""

    @pytest.fixture
    def all_tools(self):
        return _extract_tool_names_from_code()

    @pytest.fixture
    def analysis(self, all_tools):
        return _build_synthetic_analysis(all_tools)

    def test_generated_output_has_1000_plus_tools(self, all_tools):
        assert len(all_tools) > 1000, (
            f"Expected 1000+ tools, got {len(all_tools)}"
        )

    def test_all_mapped_tools_exist_in_generated(self, all_tools):
        """Every tool in our mapping exists in the generated output."""
        missing = OUR_EXPECTED_TOOLS - all_tools
        assert missing == set(), (
            f"Mapped tools not found in generated output: {sorted(missing)}"
        )

    def test_scope_file_narrows_to_official_set(self, analysis, tmp_path):
        """A scope file narrows 1,093 tools to the ~69 that match official."""
        scope_path = tmp_path / "github-scope.yaml"
        scope_doc = {
            "include_patterns": [],
            "exclude_patterns": [],
            "capabilities": [
                {"name": cap.name, "enabled": cap.name in OUR_EXPECTED_TOOLS}
                for cap in analysis.capabilities
            ],
        }
        with open(scope_path, "w") as f:
            yaml.dump(scope_doc, f)

        filtered = apply_scope(analysis, scope_file=scope_path)
        filtered_names = {c.name for c in filtered.capabilities}

        assert filtered_names == OUR_EXPECTED_TOOLS, (
            f"Extra: {sorted(filtered_names - OUR_EXPECTED_TOOLS)}\n"
            f"Missing: {sorted(OUR_EXPECTED_TOOLS - filtered_names)}"
        )

        # Dramatic reduction: 1093 → ~69
        original = len(analysis.capabilities)
        scoped = len(filtered.capabilities)
        reduction = (1 - scoped / original) * 100
        assert reduction > 90, (
            f"Expected >90% reduction, got {reduction:.1f}% ({original} → {scoped})"
        )

    def test_include_patterns_by_api_domain(self, analysis):
        """Include patterns can select specific API domains."""
        filtered = apply_scope(analysis, include_patterns=["repos_*", "pulls_*"])
        names = {c.name for c in filtered.capabilities}

        assert any(n.startswith("repos_") for n in names)
        assert any(n.startswith("pulls_") for n in names)
        assert not any(n.startswith("gists_") for n in names)
        assert not any(n.startswith("actions_") for n in names)
        assert len(names) < len(analysis.capabilities) / 2

    def test_exclude_patterns_remove_domains(self, analysis):
        """Exclude patterns can remove entire API domains."""
        filtered = apply_scope(
            analysis,
            exclude_patterns=["apps_*", "orgs_*", "teams_*", "*admin*"],
        )
        names = {c.name for c in filtered.capabilities}

        assert not any(n.startswith("apps_") for n in names)
        assert not any(n.startswith("orgs_") for n in names)
        assert not any(n.startswith("teams_") for n in names)
        assert "repos_get_content" in names
        assert "issues_get" in names

    def test_combined_include_exclude(self, analysis):
        """Include + exclude together provide precise control."""
        filtered = apply_scope(
            analysis,
            include_patterns=["issues_*", "pulls_*"],
            exclude_patterns=["*lock*", "*milestone*"],
        )
        names = {c.name for c in filtered.capabilities}

        assert any(n.startswith("issues_") for n in names)
        assert any(n.startswith("pulls_") for n in names)
        assert not any("lock" in n for n in names)
        assert not any("milestone" in n for n in names)
        assert not any(n.startswith("repos_") for n in names)

    @pytest.mark.asyncio
    async def test_scope_file_full_pipeline_with_mini_spec(self, tmp_path):
        """Full pipeline: scope file + mini OpenAPI spec → valid server."""
        # Create a mini spec with 10 endpoints
        mini_spec = {
            "openapi": "3.0.3",
            "info": {"title": "GitHub REST API (mini)", "version": "1.0.0"},
            "servers": [{"url": "https://api.github.com"}],
            "paths": {
                "/repos/{owner}/{repo}": {
                    "get": {
                        "operationId": "repos_get",
                        "summary": "Get a repository",
                        "parameters": [
                            {"name": "owner", "in": "path", "required": True, "schema": {"type": "string"}},
                            {"name": "repo", "in": "path", "required": True, "schema": {"type": "string"}},
                        ],
                        "responses": {"200": {"description": "OK"}},
                    }
                },
                "/repos/{owner}/{repo}/issues": {
                    "get": {
                        "operationId": "issues_list_for_repo",
                        "summary": "List issues",
                        "parameters": [
                            {"name": "owner", "in": "path", "required": True, "schema": {"type": "string"}},
                            {"name": "repo", "in": "path", "required": True, "schema": {"type": "string"}},
                            {"name": "state", "in": "query", "schema": {"type": "string"}},
                        ],
                        "responses": {"200": {"description": "OK"}},
                    },
                    "post": {
                        "operationId": "issues_create",
                        "summary": "Create an issue",
                        "parameters": [
                            {"name": "owner", "in": "path", "required": True, "schema": {"type": "string"}},
                            {"name": "repo", "in": "path", "required": True, "schema": {"type": "string"}},
                        ],
                        "responses": {"201": {"description": "Created"}},
                    },
                },
                "/repos/{owner}/{repo}/pulls": {
                    "get": {
                        "operationId": "pulls_list",
                        "summary": "List pull requests",
                        "parameters": [
                            {"name": "owner", "in": "path", "required": True, "schema": {"type": "string"}},
                            {"name": "repo", "in": "path", "required": True, "schema": {"type": "string"}},
                        ],
                        "responses": {"200": {"description": "OK"}},
                    },
                    "post": {
                        "operationId": "pulls_create",
                        "summary": "Create a pull request",
                        "parameters": [
                            {"name": "owner", "in": "path", "required": True, "schema": {"type": "string"}},
                            {"name": "repo", "in": "path", "required": True, "schema": {"type": "string"}},
                        ],
                        "responses": {"201": {"description": "Created"}},
                    },
                },
                "/search/code": {
                    "get": {
                        "operationId": "search_code",
                        "summary": "Search code",
                        "parameters": [
                            {"name": "q", "in": "query", "required": True, "schema": {"type": "string"}},
                        ],
                        "responses": {"200": {"description": "OK"}},
                    }
                },
                "/gists": {
                    "get": {
                        "operationId": "gists_list",
                        "summary": "List gists",
                        "responses": {"200": {"description": "OK"}},
                    },
                    "post": {
                        "operationId": "gists_create",
                        "summary": "Create a gist",
                        "responses": {"201": {"description": "Created"}},
                    },
                },
                "/repos/{owner}/{repo}/actions/workflows": {
                    "get": {
                        "operationId": "actions_list_workflows",
                        "summary": "List workflows",
                        "parameters": [
                            {"name": "owner", "in": "path", "required": True, "schema": {"type": "string"}},
                            {"name": "repo", "in": "path", "required": True, "schema": {"type": "string"}},
                        ],
                        "responses": {"200": {"description": "OK"}},
                    }
                },
                "/user": {
                    "get": {
                        "operationId": "users_get_authenticated",
                        "summary": "Get the authenticated user",
                        "responses": {"200": {"description": "OK"}},
                    }
                },
            },
        }

        spec_dir = tmp_path / "github-mini"
        spec_dir.mkdir()
        (spec_dir / "openapi.json").write_text(json.dumps(mini_spec, indent=2))

        # Create a scope file that excludes gists and actions
        scope_path = tmp_path / "scope.yaml"
        scope_doc = {
            "include_patterns": [],
            "exclude_patterns": ["gists_*", "actions_*"],
            "capabilities": [],
        }
        with open(scope_path, "w") as f:
            yaml.dump(scope_doc, f)

        # Run the full pipeline
        output_dir = tmp_path / "mcp-github-mini"
        options = CLIOptions(
            codebase_path=spec_dir,
            output_dir=output_dir,
            name="github-mini",
            no_llm=True,
            no_install=True,
            scope_file=scope_path,
        )
        console = Console(quiet=True)
        engine = PipelineEngine(options, console)

        await engine.run()

        manifest = GenerationManifest.load(output_dir / "mcp-anything-manifest.json")
        assert manifest.completed_phases == [
            "analyze", "design", "implement", "test", "document", "package"
        ]
        assert manifest.errors == []

        # Verify scoping worked
        tool_names = {t.name for t in manifest.design.tools}
        assert "issues_list_for_repo" in tool_names
        assert "pulls_list" in tool_names
        assert "search_code" in tool_names
        assert "users_get_authenticated" in tool_names
        # These should be excluded
        assert "gists_list" not in tool_names
        assert "gists_create" not in tool_names
        assert "actions_list_workflows" not in tool_names

        # Valid Python
        for py_file in output_dir.rglob("*.py"):
            ast.parse(py_file.read_text(), filename=str(py_file))

        # Server importable
        src_path = str(output_dir / "src")
        sys.path.insert(0, src_path)
        try:
            import importlib
            mod = importlib.import_module("mcp_github_mini.server")
            assert hasattr(mod, "server")
        finally:
            sys.path.remove(src_path)
            for k in list(sys.modules):
                if k.startswith("mcp_github_mini"):
                    del sys.modules[k]
