"""Tests for github-scoped MCP server tools."""

import asyncio
import importlib
import json
import types
from unittest.mock import AsyncMock

import pytest



def _run(awaitable):
    """Run an async FastMCP helper from a synchronous pytest test."""
    return asyncio.run(awaitable)


def _tool_map(server):
    """Return registered tools keyed by tool name."""
    return {tool.name: tool for tool in _run(server.list_tools())}


def _extract_text_result(result):
    """Extract the text payload from FastMCP call_tool()."""
    contents = result[0] if isinstance(result, tuple) else result
    assert isinstance(contents, list)
    assert contents, "tool returned no content"
    first = contents[0]
    return getattr(first, "text", str(first))


class TestToolRegistration:
    """Verify generated tools are registered with the expected schemas."""

    def test_server_has_tools(self, server):
        tools = _tool_map(server)
        assert len(tools) == 67

    @pytest.mark.parametrize(
        ("tool_name", "property_names", "required_names"),
        [
            (
                "security_advisories_list_global_advisories",
                [
                    "ghsa_id",
                    "type",
                    "cve_id",
                    "ecosystem",
                    "severity",
                    "cwes",
                    "is_withdrawn",
                    "affects",
                    "published",
                    "updated",
                    "modified",
                    "epss_percentage",
                    "epss_percentile",
                    "before",
                    "after",
                    "direction",
                    "per_page",
                    "sort",
                ],
                [
                ],
            ),
            (
                "security_advisories_get_global_advisory",
                [
                    "ghsa_id",
                ],
                [
                    "ghsa_id",
                ],
            ),
            (
                "gists_list",
                [
                    "since",
                    "per_page",
                    "page",
                ],
                [
                ],
            ),
            (
                "gists_create",
                [
                    "description",
                    "files",
                    "public",
                ],
                [
                    "files",
                ],
            ),
            (
                "gists_get",
                [
                    "gist_id",
                ],
                [
                    "gist_id",
                ],
            ),
            (
                "gists_update",
                [
                    "gist_id",
                    "description",
                    "files",
                ],
                [
                    "gist_id",
                ],
            ),
            (
                "get_notifications",
                [
                    "all",
                    "participating",
                    "since",
                    "before",
                    "page",
                    "per_page",
                ],
                [
                ],
            ),
            (
                "activity_mark_notifications_as_read",
                [
                    "last_read_at",
                    "read",
                ],
                [
                ],
            ),
            (
                "activity_get_thread",
                [
                    "thread_id",
                ],
                [
                    "thread_id",
                ],
            ),
            (
                "activity_mark_thread_as_done",
                [
                    "thread_id",
                ],
                [
                    "thread_id",
                ],
            ),
            (
                "activity_set_thread_subscription",
                [
                    "thread_id",
                    "ignored",
                ],
                [
                    "thread_id",
                ],
            ),
            (
                "orgs_list_issue_types",
                [
                    "org",
                ],
                [
                    "org",
                ],
            ),
            (
                "teams_list",
                [
                    "org",
                    "per_page",
                    "page",
                    "team_type",
                ],
                [
                    "org",
                ],
            ),
            (
                "teams_list_members_in_org",
                [
                    "org",
                    "team_slug",
                    "role",
                    "per_page",
                    "page",
                ],
                [
                    "org",
                    "team_slug",
                ],
            ),
            (
                "actions_download_job_logs_for_workflow_run",
                [
                    "owner",
                    "repo",
                    "job_id",
                ],
                [
                    "owner",
                    "repo",
                    "job_id",
                ],
            ),
            (
                "actions_list_repo_workflows",
                [
                    "owner",
                    "repo",
                    "per_page",
                    "page",
                ],
                [
                    "owner",
                    "repo",
                ],
            ),
            (
                "actions_get_workflow",
                [
                    "owner",
                    "repo",
                    "workflow_id",
                ],
                [
                    "owner",
                    "repo",
                    "workflow_id",
                ],
            ),
            (
                "actions_create_workflow_dispatch",
                [
                    "owner",
                    "repo",
                    "workflow_id",
                    "ref",
                    "inputs",
                    "return_run_details",
                ],
                [
                    "owner",
                    "repo",
                    "workflow_id",
                    "ref",
                ],
            ),
            (
                "repos_list_branches",
                [
                    "owner",
                    "repo",
                    "protected",
                    "per_page",
                    "page",
                ],
                [
                    "owner",
                    "repo",
                ],
            ),
            (
                "code_scanning_list_alerts_for_repo",
                [
                    "owner",
                    "repo",
                    "tool_name",
                    "tool_guid",
                    "page",
                    "per_page",
                    "ref",
                    "pr",
                    "direction",
                    "before",
                    "after",
                    "sort",
                    "state",
                    "severity",
                    "assignees",
                ],
                [
                    "owner",
                    "repo",
                ],
            ),
            (
                "code_scanning_get_alert",
                [
                    "owner",
                    "repo",
                    "alert_number",
                ],
                [
                    "owner",
                    "repo",
                    "alert_number",
                ],
            ),
            (
                "repos_list_commits",
                [
                    "owner",
                    "repo",
                    "sha",
                    "path",
                    "author",
                    "committer",
                    "since",
                    "until",
                    "per_page",
                    "page",
                ],
                [
                    "owner",
                    "repo",
                ],
            ),
            (
                "repos_get_commit",
                [
                    "owner",
                    "repo",
                    "page",
                    "per_page",
                    "ref",
                ],
                [
                    "owner",
                    "repo",
                    "ref",
                ],
            ),
            (
                "repos_get_content",
                [
                    "owner",
                    "repo",
                    "path",
                    "ref",
                ],
                [
                    "owner",
                    "repo",
                    "path",
                ],
            ),
            (
                "repos_create_or_update_file_contents",
                [
                    "owner",
                    "repo",
                    "path",
                    "message",
                    "content",
                    "sha",
                    "branch",
                    "committer",
                    "author",
                ],
                [
                    "owner",
                    "repo",
                    "path",
                    "message",
                    "content",
                ],
            ),
            (
                "repos_delete_file",
                [
                    "owner",
                    "repo",
                    "path",
                    "message",
                    "sha",
                    "branch",
                    "committer",
                    "author",
                ],
                [
                    "owner",
                    "repo",
                    "path",
                    "message",
                    "sha",
                ],
            ),
            (
                "dependabot_list_alerts_for_repo",
                [
                    "owner",
                    "repo",
                    "state",
                    "severity",
                    "ecosystem",
                    "package",
                    "manifest",
                    "epss_percentage",
                    "has",
                    "assignee",
                    "scope",
                    "sort",
                    "direction",
                    "before",
                    "after",
                    "per_page",
                ],
                [
                    "owner",
                    "repo",
                ],
            ),
            (
                "dependabot_get_alert",
                [
                    "owner",
                    "repo",
                    "alert_number",
                ],
                [
                    "owner",
                    "repo",
                    "alert_number",
                ],
            ),
            (
                "repos_create_fork",
                [
                    "owner",
                    "repo",
                    "organization",
                    "name",
                    "default_branch_only",
                ],
                [
                    "owner",
                    "repo",
                ],
            ),
            (
                "git_create_ref",
                [
                    "owner",
                    "repo",
                    "ref",
                    "sha",
                ],
                [
                    "owner",
                    "repo",
                    "ref",
                    "sha",
                ],
            ),
            (
                "git_get_tag",
                [
                    "owner",
                    "repo",
                    "tag_sha",
                ],
                [
                    "owner",
                    "repo",
                    "tag_sha",
                ],
            ),
            (
                "git_get_tree",
                [
                    "owner",
                    "repo",
                    "tree_sha",
                    "recursive",
                ],
                [
                    "owner",
                    "repo",
                    "tree_sha",
                ],
            ),
            (
                "issues_list_for_repo",
                [
                    "owner",
                    "repo",
                    "milestone",
                    "state",
                    "assignee",
                    "type",
                    "creator",
                    "mentioned",
                    "labels",
                    "sort",
                    "direction",
                    "since",
                    "per_page",
                    "page",
                ],
                [
                    "owner",
                    "repo",
                ],
            ),
            (
                "issues_create",
                [
                    "owner",
                    "repo",
                    "title",
                    "body",
                    "assignee",
                    "milestone",
                    "labels",
                    "assignees",
                    "type",
                ],
                [
                    "owner",
                    "repo",
                    "title",
                ],
            ),
            (
                "issues_get",
                [
                    "owner",
                    "repo",
                    "issue_number",
                ],
                [
                    "owner",
                    "repo",
                    "issue_number",
                ],
            ),
            (
                "issues_update",
                [
                    "owner",
                    "repo",
                    "issue_number",
                    "title",
                    "body",
                    "assignee",
                    "state",
                    "state_reason",
                    "milestone",
                    "labels",
                    "assignees",
                    "issue_field_values",
                    "type",
                ],
                [
                    "owner",
                    "repo",
                    "issue_number",
                ],
            ),
            (
                "issues_create_comment",
                [
                    "owner",
                    "repo",
                    "issue_number",
                    "body",
                ],
                [
                    "owner",
                    "repo",
                    "issue_number",
                    "body",
                ],
            ),
            (
                "issues_add_sub_issue",
                [
                    "owner",
                    "repo",
                    "issue_number",
                    "sub_issue_id",
                    "replace_parent",
                ],
                [
                    "owner",
                    "repo",
                    "issue_number",
                    "sub_issue_id",
                ],
            ),
            (
                "issues_list_labels_for_repo",
                [
                    "owner",
                    "repo",
                    "per_page",
                    "page",
                ],
                [
                    "owner",
                    "repo",
                ],
            ),
            (
                "issues_create_label",
                [
                    "owner",
                    "repo",
                    "name",
                    "color",
                    "description",
                ],
                [
                    "owner",
                    "repo",
                    "name",
                ],
            ),
            (
                "issues_get_label",
                [
                    "owner",
                    "repo",
                    "name",
                ],
                [
                    "owner",
                    "repo",
                    "name",
                ],
            ),
            (
                "pulls_list",
                [
                    "owner",
                    "repo",
                    "state",
                    "head",
                    "base",
                    "sort",
                    "direction",
                    "per_page",
                    "page",
                ],
                [
                    "owner",
                    "repo",
                ],
            ),
            (
                "pulls_create",
                [
                    "owner",
                    "repo",
                    "title",
                    "head",
                    "head_repo",
                    "base",
                    "body",
                    "maintainer_can_modify",
                    "draft",
                    "issue",
                ],
                [
                    "owner",
                    "repo",
                    "head",
                    "base",
                ],
            ),
            (
                "pulls_get",
                [
                    "owner",
                    "repo",
                    "pull_number",
                ],
                [
                    "owner",
                    "repo",
                    "pull_number",
                ],
            ),
            (
                "pulls_update",
                [
                    "owner",
                    "repo",
                    "pull_number",
                    "title",
                    "body",
                    "state",
                    "base",
                    "maintainer_can_modify",
                ],
                [
                    "owner",
                    "repo",
                    "pull_number",
                ],
            ),
            (
                "pulls_create_review_comment",
                [
                    "owner",
                    "repo",
                    "pull_number",
                    "body",
                    "commit_id",
                    "path",
                    "position",
                    "side",
                    "line",
                    "start_line",
                    "start_side",
                    "in_reply_to",
                    "subject_type",
                ],
                [
                    "owner",
                    "repo",
                    "pull_number",
                    "body",
                    "commit_id",
                    "path",
                ],
            ),
            (
                "pulls_create_reply_for_review_comment",
                [
                    "owner",
                    "repo",
                    "pull_number",
                    "comment_id",
                    "body",
                ],
                [
                    "owner",
                    "repo",
                    "pull_number",
                    "comment_id",
                    "body",
                ],
            ),
            (
                "pulls_merge",
                [
                    "owner",
                    "repo",
                    "pull_number",
                    "commit_title",
                    "commit_message",
                    "sha",
                    "merge_method",
                ],
                [
                    "owner",
                    "repo",
                    "pull_number",
                ],
            ),
            (
                "pulls_submit_review",
                [
                    "owner",
                    "repo",
                    "pull_number",
                    "review_id",
                    "body",
                    "event",
                ],
                [
                    "owner",
                    "repo",
                    "pull_number",
                    "review_id",
                    "event",
                ],
            ),
            (
                "pulls_update_branch",
                [
                    "owner",
                    "repo",
                    "pull_number",
                    "expected_head_sha",
                ],
                [
                    "owner",
                    "repo",
                    "pull_number",
                ],
            ),
            (
                "repos_list_releases",
                [
                    "owner",
                    "repo",
                    "per_page",
                    "page",
                ],
                [
                    "owner",
                    "repo",
                ],
            ),
            (
                "repos_get_latest_release",
                [
                    "owner",
                    "repo",
                ],
                [
                    "owner",
                    "repo",
                ],
            ),
            (
                "repos_get_release_by_tag",
                [
                    "owner",
                    "repo",
                    "tag",
                ],
                [
                    "owner",
                    "repo",
                    "tag",
                ],
            ),
            (
                "secret_scanning_list_alerts_for_repo",
                [
                    "owner",
                    "repo",
                    "state",
                    "secret_type",
                    "resolution",
                    "assignee",
                    "sort",
                    "direction",
                    "page",
                    "per_page",
                    "before",
                    "after",
                    "validity",
                    "is_publicly_leaked",
                    "is_multi_repo",
                    "hide_secret",
                ],
                [
                    "owner",
                    "repo",
                ],
            ),
            (
                "secret_scanning_get_alert",
                [
                    "owner",
                    "repo",
                    "alert_number",
                    "hide_secret",
                ],
                [
                    "owner",
                    "repo",
                    "alert_number",
                ],
            ),
            (
                "security_advisories_list_repository_advisories",
                [
                    "owner",
                    "repo",
                    "direction",
                    "sort",
                    "before",
                    "after",
                    "per_page",
                    "state",
                ],
                [
                    "owner",
                    "repo",
                ],
            ),
            (
                "activity_set_repo_subscription",
                [
                    "owner",
                    "repo",
                    "subscribed",
                    "ignored",
                ],
                [
                    "owner",
                    "repo",
                ],
            ),
            (
                "repos_list_tags",
                [
                    "owner",
                    "repo",
                    "per_page",
                    "page",
                ],
                [
                    "owner",
                    "repo",
                ],
            ),
            (
                "search_code",
                [
                    "q",
                    "sort",
                    "order",
                    "per_page",
                    "page",
                ],
                [
                    "q",
                ],
            ),
            (
                "search_issues_and_pull_requests",
                [
                    "q",
                    "sort",
                    "order",
                    "per_page",
                    "page",
                    "advanced_search",
                ],
                [
                    "q",
                ],
            ),
            (
                "search_repos",
                [
                    "q",
                    "sort",
                    "order",
                    "per_page",
                    "page",
                ],
                [
                    "q",
                ],
            ),
            (
                "search_users",
                [
                    "q",
                    "sort",
                    "order",
                    "per_page",
                    "page",
                ],
                [
                    "q",
                ],
            ),
            (
                "users_get_authenticated",
                [
                ],
                [
                ],
            ),
            (
                "repos_create_for_authenticated_user",
                [
                    "name",
                    "description",
                    "homepage",
                    "private",
                    "has_issues",
                    "has_projects",
                    "has_wiki",
                    "has_discussions",
                    "team_id",
                    "auto_init",
                    "gitignore_template",
                    "license_template",
                    "allow_squash_merge",
                    "allow_merge_commit",
                    "allow_rebase_merge",
                    "allow_auto_merge",
                    "delete_branch_on_merge",
                    "squash_merge_commit_title",
                    "squash_merge_commit_message",
                    "merge_commit_title",
                    "merge_commit_message",
                    "has_downloads",
                    "is_template",
                ],
                [
                    "name",
                ],
            ),
            (
                "activity_list_repos_starred_by_authenticated_user",
                [
                    "sort",
                    "direction",
                    "per_page",
                    "page",
                ],
                [
                ],
            ),
            (
                "activity_star_repo_for_authenticated_user",
                [
                    "owner",
                    "repo",
                ],
                [
                    "owner",
                    "repo",
                ],
            ),
            (
                "activity_unstar_repo_for_authenticated_user",
                [
                    "owner",
                    "repo",
                ],
                [
                    "owner",
                    "repo",
                ],
            ),
        ],
    )
    def test_tool_schema_matches_design(self, server, tool_name, property_names, required_names):
        tools = _tool_map(server)
        assert tool_name in tools
        schema = tools[tool_name].inputSchema or {}
        assert sorted(schema.get("properties", {}).keys()) == sorted(property_names)
        assert sorted(schema.get("required", [])) == sorted(required_names)


class TestOptionalParameterHandling:
    """Verify omitted optional parameters are not forwarded downstream."""

    def test_security_advisories_list_global_advisories_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("security_advisories_list_global_advisories", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
None        )
        assert kwargs["body"] == (
None        )
        assert kwargs["path_params"] == (
None        )

    def test_gists_list_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("gists_list", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
None        )
        assert kwargs["body"] == (
None        )
        assert kwargs["path_params"] == (
None        )

    def test_gists_create_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
            "files": {"value": "sample_files"},
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("gists_create", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
None        )
        assert kwargs["body"] == (
{
            "value": "sample_files",
            }        )
        assert kwargs["path_params"] == (
None        )

    def test_gists_update_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
            "gist_id": "sample_gist_id",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("gists_update", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
None        )
        assert kwargs["body"] == (
None        )
        assert kwargs["path_params"] == (
{
            "gist_id": str(tool_input["gist_id"]),
            }        )

    def test_get_notifications_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("get_notifications", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
None        )
        assert kwargs["body"] == (
None        )
        assert kwargs["path_params"] == (
None        )

    def test_activity_mark_notifications_as_read_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("activity_mark_notifications_as_read", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
None        )
        assert kwargs["body"] == (
None        )
        assert kwargs["path_params"] == (
None        )

    def test_activity_set_thread_subscription_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
            "thread_id": 7,
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("activity_set_thread_subscription", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
None        )
        assert kwargs["body"] == (
None        )
        assert kwargs["path_params"] == (
{
            "thread_id": str(tool_input["thread_id"]),
            }        )

    def test_teams_list_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
            "org": "sample_org",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("teams_list", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
None        )
        assert kwargs["body"] == (
None        )
        assert kwargs["path_params"] == (
{
            "org": str(tool_input["org"]),
            }        )

    def test_teams_list_members_in_org_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
            "org": "sample_org",
            "team_slug": "sample_team_slug",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("teams_list_members_in_org", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
None        )
        assert kwargs["body"] == (
None        )
        assert kwargs["path_params"] == (
{
            "org": str(tool_input["org"]),
            "team_slug": str(tool_input["team_slug"]),
            }        )

    def test_actions_list_repo_workflows_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("actions_list_repo_workflows", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
None        )
        assert kwargs["body"] == (
None        )
        assert kwargs["path_params"] == (
{
            "owner": str(tool_input["owner"]),
            "repo": str(tool_input["repo"]),
            }        )

    def test_actions_create_workflow_dispatch_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "workflow_id": {"value": "sample_workflow_id"},
            "ref": "sample_ref",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("actions_create_workflow_dispatch", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
{
            "ref": str(tool_input["ref"]),
            }        )
        assert kwargs["body"] == (
None        )
        assert kwargs["path_params"] == (
{
            "owner": str(tool_input["owner"]),
            "repo": str(tool_input["repo"]),
            "workflow_id": str(tool_input["workflow_id"]),
            }        )

    def test_repos_list_branches_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("repos_list_branches", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
None        )
        assert kwargs["body"] == (
None        )
        assert kwargs["path_params"] == (
{
            "owner": str(tool_input["owner"]),
            "repo": str(tool_input["repo"]),
            }        )

    def test_code_scanning_list_alerts_for_repo_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("code_scanning_list_alerts_for_repo", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
None        )
        assert kwargs["body"] == (
None        )
        assert kwargs["path_params"] == (
{
            "owner": str(tool_input["owner"]),
            "repo": str(tool_input["repo"]),
            }        )

    def test_repos_list_commits_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("repos_list_commits", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
None        )
        assert kwargs["body"] == (
None        )
        assert kwargs["path_params"] == (
{
            "owner": str(tool_input["owner"]),
            "repo": str(tool_input["repo"]),
            }        )

    def test_repos_get_commit_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "ref": "sample_ref",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("repos_get_commit", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
None        )
        assert kwargs["body"] == (
None        )
        assert kwargs["path_params"] == (
{
            "owner": str(tool_input["owner"]),
            "repo": str(tool_input["repo"]),
            "ref": str(tool_input["ref"]),
            }        )

    def test_repos_get_content_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "path": "sample_path",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("repos_get_content", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
None        )
        assert kwargs["body"] == (
None        )
        assert kwargs["path_params"] == (
{
            "owner": str(tool_input["owner"]),
            "repo": str(tool_input["repo"]),
            "path": str(tool_input["path"]),
            }        )

    def test_repos_create_or_update_file_contents_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "path": "sample_path",
            "message": "sample_message",
            "content": "sample_content",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("repos_create_or_update_file_contents", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
{
            "message": str(tool_input["message"]),
            "content": str(tool_input["content"]),
            }        )
        assert kwargs["body"] == (
None        )
        assert kwargs["path_params"] == (
{
            "owner": str(tool_input["owner"]),
            "repo": str(tool_input["repo"]),
            "path": str(tool_input["path"]),
            }        )

    def test_repos_delete_file_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "path": "sample_path",
            "message": "sample_message",
            "sha": "sample_sha",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("repos_delete_file", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
{
            "message": str(tool_input["message"]),
            "sha": str(tool_input["sha"]),
            }        )
        assert kwargs["body"] == (
None        )
        assert kwargs["path_params"] == (
{
            "owner": str(tool_input["owner"]),
            "repo": str(tool_input["repo"]),
            "path": str(tool_input["path"]),
            }        )

    def test_dependabot_list_alerts_for_repo_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("dependabot_list_alerts_for_repo", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
None        )
        assert kwargs["body"] == (
None        )
        assert kwargs["path_params"] == (
{
            "owner": str(tool_input["owner"]),
            "repo": str(tool_input["repo"]),
            }        )

    def test_repos_create_fork_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("repos_create_fork", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
None        )
        assert kwargs["body"] == (
None        )
        assert kwargs["path_params"] == (
{
            "owner": str(tool_input["owner"]),
            "repo": str(tool_input["repo"]),
            }        )

    def test_git_get_tree_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "tree_sha": "sample_tree_sha",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("git_get_tree", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
None        )
        assert kwargs["body"] == (
None        )
        assert kwargs["path_params"] == (
{
            "owner": str(tool_input["owner"]),
            "repo": str(tool_input["repo"]),
            "tree_sha": str(tool_input["tree_sha"]),
            }        )

    def test_issues_list_for_repo_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("issues_list_for_repo", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
None        )
        assert kwargs["body"] == (
None        )
        assert kwargs["path_params"] == (
{
            "owner": str(tool_input["owner"]),
            "repo": str(tool_input["repo"]),
            }        )

    def test_issues_create_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "title": {"value": "sample_title"},
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("issues_create", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
None        )
        assert kwargs["body"] == (
{
            "value": "sample_title",
            }        )
        assert kwargs["path_params"] == (
{
            "owner": str(tool_input["owner"]),
            "repo": str(tool_input["repo"]),
            }        )

    def test_issues_update_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "issue_number": 7,
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("issues_update", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
None        )
        assert kwargs["body"] == (
None        )
        assert kwargs["path_params"] == (
{
            "owner": str(tool_input["owner"]),
            "repo": str(tool_input["repo"]),
            "issue_number": str(tool_input["issue_number"]),
            }        )

    def test_issues_add_sub_issue_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "issue_number": 7,
            "sub_issue_id": 7,
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("issues_add_sub_issue", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
{
            "sub_issue_id": str(tool_input["sub_issue_id"]),
            }        )
        assert kwargs["body"] == (
None        )
        assert kwargs["path_params"] == (
{
            "owner": str(tool_input["owner"]),
            "repo": str(tool_input["repo"]),
            "issue_number": str(tool_input["issue_number"]),
            }        )

    def test_issues_list_labels_for_repo_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("issues_list_labels_for_repo", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
None        )
        assert kwargs["body"] == (
None        )
        assert kwargs["path_params"] == (
{
            "owner": str(tool_input["owner"]),
            "repo": str(tool_input["repo"]),
            }        )

    def test_issues_create_label_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "name": "sample_name",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("issues_create_label", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
{
            "name": str(tool_input["name"]),
            }        )
        assert kwargs["body"] == (
None        )
        assert kwargs["path_params"] == (
{
            "owner": str(tool_input["owner"]),
            "repo": str(tool_input["repo"]),
            }        )

    def test_pulls_list_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("pulls_list", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
None        )
        assert kwargs["body"] == (
None        )
        assert kwargs["path_params"] == (
{
            "owner": str(tool_input["owner"]),
            "repo": str(tool_input["repo"]),
            }        )

    def test_pulls_create_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "head": "sample_head",
            "base": "sample_base",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("pulls_create", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
{
            "head": str(tool_input["head"]),
            "base": str(tool_input["base"]),
            }        )
        assert kwargs["body"] == (
None        )
        assert kwargs["path_params"] == (
{
            "owner": str(tool_input["owner"]),
            "repo": str(tool_input["repo"]),
            }        )

    def test_pulls_update_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "pull_number": 7,
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("pulls_update", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
None        )
        assert kwargs["body"] == (
None        )
        assert kwargs["path_params"] == (
{
            "owner": str(tool_input["owner"]),
            "repo": str(tool_input["repo"]),
            "pull_number": str(tool_input["pull_number"]),
            }        )

    def test_pulls_create_review_comment_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "pull_number": 7,
            "body": "sample_body",
            "commit_id": "sample_commit_id",
            "path": "sample_path",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("pulls_create_review_comment", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
{
            "body": str(tool_input["body"]),
            "commit_id": str(tool_input["commit_id"]),
            "path": str(tool_input["path"]),
            }        )
        assert kwargs["body"] == (
None        )
        assert kwargs["path_params"] == (
{
            "owner": str(tool_input["owner"]),
            "repo": str(tool_input["repo"]),
            "pull_number": str(tool_input["pull_number"]),
            }        )

    def test_pulls_merge_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "pull_number": 7,
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("pulls_merge", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
None        )
        assert kwargs["body"] == (
None        )
        assert kwargs["path_params"] == (
{
            "owner": str(tool_input["owner"]),
            "repo": str(tool_input["repo"]),
            "pull_number": str(tool_input["pull_number"]),
            }        )

    def test_pulls_submit_review_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "pull_number": 7,
            "review_id": 7,
            "event": "sample_event",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("pulls_submit_review", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
{
            "event": str(tool_input["event"]),
            }        )
        assert kwargs["body"] == (
None        )
        assert kwargs["path_params"] == (
{
            "owner": str(tool_input["owner"]),
            "repo": str(tool_input["repo"]),
            "pull_number": str(tool_input["pull_number"]),
            "review_id": str(tool_input["review_id"]),
            }        )

    def test_pulls_update_branch_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "pull_number": 7,
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("pulls_update_branch", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
None        )
        assert kwargs["body"] == (
None        )
        assert kwargs["path_params"] == (
{
            "owner": str(tool_input["owner"]),
            "repo": str(tool_input["repo"]),
            "pull_number": str(tool_input["pull_number"]),
            }        )

    def test_repos_list_releases_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("repos_list_releases", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
None        )
        assert kwargs["body"] == (
None        )
        assert kwargs["path_params"] == (
{
            "owner": str(tool_input["owner"]),
            "repo": str(tool_input["repo"]),
            }        )

    def test_secret_scanning_list_alerts_for_repo_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("secret_scanning_list_alerts_for_repo", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
None        )
        assert kwargs["body"] == (
None        )
        assert kwargs["path_params"] == (
{
            "owner": str(tool_input["owner"]),
            "repo": str(tool_input["repo"]),
            }        )

    def test_secret_scanning_get_alert_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "alert_number": 7,
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("secret_scanning_get_alert", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
None        )
        assert kwargs["body"] == (
None        )
        assert kwargs["path_params"] == (
{
            "owner": str(tool_input["owner"]),
            "repo": str(tool_input["repo"]),
            "alert_number": str(tool_input["alert_number"]),
            }        )

    def test_security_advisories_list_repository_advisories_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("security_advisories_list_repository_advisories", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
None        )
        assert kwargs["body"] == (
None        )
        assert kwargs["path_params"] == (
{
            "owner": str(tool_input["owner"]),
            "repo": str(tool_input["repo"]),
            }        )

    def test_activity_set_repo_subscription_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("activity_set_repo_subscription", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
None        )
        assert kwargs["body"] == (
None        )
        assert kwargs["path_params"] == (
{
            "owner": str(tool_input["owner"]),
            "repo": str(tool_input["repo"]),
            }        )

    def test_repos_list_tags_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("repos_list_tags", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
None        )
        assert kwargs["body"] == (
None        )
        assert kwargs["path_params"] == (
{
            "owner": str(tool_input["owner"]),
            "repo": str(tool_input["repo"]),
            }        )

    def test_search_code_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
            "q": "sample_q",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("search_code", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
{
            "q": str(tool_input["q"]),
            }        )
        assert kwargs["body"] == (
None        )
        assert kwargs["path_params"] == (
None        )

    def test_search_issues_and_pull_requests_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
            "q": "sample_q",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("search_issues_and_pull_requests", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
{
            "q": str(tool_input["q"]),
            }        )
        assert kwargs["body"] == (
None        )
        assert kwargs["path_params"] == (
None        )

    def test_search_repos_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
            "q": "sample_q",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("search_repos", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
{
            "q": str(tool_input["q"]),
            }        )
        assert kwargs["body"] == (
None        )
        assert kwargs["path_params"] == (
None        )

    def test_search_users_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
            "q": "sample_q",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("search_users", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
{
            "q": str(tool_input["q"]),
            }        )
        assert kwargs["body"] == (
None        )
        assert kwargs["path_params"] == (
None        )

    def test_repos_create_for_authenticated_user_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
            "name": "sample_name",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("repos_create_for_authenticated_user", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
{
            "name": str(tool_input["name"]),
            }        )
        assert kwargs["body"] == (
None        )
        assert kwargs["path_params"] == (
None        )

    def test_activity_list_repos_starred_by_authenticated_user_omits_optional_parameters(self, server, server_module, monkeypatch):
        tool_input = {
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("activity_list_repos_starred_by_authenticated_user", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        kwargs = mock_request.await_args.kwargs
        assert kwargs["params"] == (
None        )
        assert kwargs["body"] == (
None        )
        assert kwargs["path_params"] == (
None        )





class TestToolExecution:
    """Execute generated tool handlers with mocked dependencies."""

    def test_security_advisories_list_global_advisories_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "ghsa_id": "sample_ghsa_id",
            "type": "sample_type",
            "cve_id": "sample_cve_id",
            "ecosystem": "sample_ecosystem",
            "severity": "sample_severity",
            "cwes": {"value": "sample_cwes"},
            "is_withdrawn": True,
            "affects": {"value": "sample_affects"},
            "published": "sample_published",
            "updated": "sample_updated",
            "modified": "sample_modified",
            "epss_percentage": "sample_epss_percentage",
            "epss_percentile": "sample_epss_percentile",
            "before": "sample_before",
            "after": "sample_after",
            "direction": "sample_direction",
            "per_page": 7,
            "sort": "sample_sort",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("security_advisories_list_global_advisories", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "GET",
            "/advisories",
            params={
                "ghsa_id": str(tool_input["ghsa_id"]),
                "type": str(tool_input["type"]),
                "cve_id": str(tool_input["cve_id"]),
                "ecosystem": str(tool_input["ecosystem"]),
                "severity": str(tool_input["severity"]),
                "is_withdrawn": str(tool_input["is_withdrawn"]),
                "published": str(tool_input["published"]),
                "updated": str(tool_input["updated"]),
                "modified": str(tool_input["modified"]),
                "epss_percentage": str(tool_input["epss_percentage"]),
                "epss_percentile": str(tool_input["epss_percentile"]),
                "before": str(tool_input["before"]),
                "after": str(tool_input["after"]),
                "direction": str(tool_input["direction"]),
                "per_page": str(tool_input["per_page"]),
                "sort": str(tool_input["sort"]),
            },
            body={
                "value": "sample_cwes",
                "value": "sample_affects",
            },
            path_params=None,
        )

    def test_security_advisories_get_global_advisory_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "ghsa_id": "sample_ghsa_id",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("security_advisories_get_global_advisory", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "GET",
            "/advisories/{ghsa_id}",
            params=None,
            body=None,
            path_params={
                "ghsa_id": str(tool_input["ghsa_id"]),
            },
        )

    def test_gists_list_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "since": "sample_since",
            "per_page": 7,
            "page": 7,
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("gists_list", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "GET",
            "/gists",
            params={
                "since": str(tool_input["since"]),
                "per_page": str(tool_input["per_page"]),
                "page": str(tool_input["page"]),
            },
            body=None,
            path_params=None,
        )

    def test_gists_create_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "description": "sample_description",
            "files": {"value": "sample_files"},
            "public": {"value": "sample_public"},
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("gists_create", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "POST",
            "/gists",
            params={
                "description": str(tool_input["description"]),
            },
            body={
                "value": "sample_files",
                "value": "sample_public",
            },
            path_params=None,
        )

    def test_gists_get_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "gist_id": "sample_gist_id",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("gists_get", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "GET",
            "/gists/{gist_id}",
            params=None,
            body=None,
            path_params={
                "gist_id": str(tool_input["gist_id"]),
            },
        )

    def test_gists_update_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "gist_id": "sample_gist_id",
            "description": "sample_description",
            "files": {"value": "sample_files"},
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("gists_update", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "PATCH",
            "/gists/{gist_id}",
            params={
                "description": str(tool_input["description"]),
            },
            body={
                "value": "sample_files",
            },
            path_params={
                "gist_id": str(tool_input["gist_id"]),
            },
        )

    def test_get_notifications_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "all": True,
            "participating": True,
            "since": "sample_since",
            "before": "sample_before",
            "page": 7,
            "per_page": 7,
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("get_notifications", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "GET",
            "/notifications",
            params={
                "all": str(tool_input["all"]),
                "participating": str(tool_input["participating"]),
                "since": str(tool_input["since"]),
                "before": str(tool_input["before"]),
                "page": str(tool_input["page"]),
                "per_page": str(tool_input["per_page"]),
            },
            body=None,
            path_params=None,
        )

    def test_activity_mark_notifications_as_read_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "last_read_at": "sample_last_read_at",
            "read": True,
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("activity_mark_notifications_as_read", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "PUT",
            "/notifications",
            params={
                "last_read_at": str(tool_input["last_read_at"]),
                "read": str(tool_input["read"]),
            },
            body=None,
            path_params=None,
        )

    def test_activity_get_thread_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "thread_id": 7,
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("activity_get_thread", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "GET",
            "/notifications/threads/{thread_id}",
            params=None,
            body=None,
            path_params={
                "thread_id": str(tool_input["thread_id"]),
            },
        )

    def test_activity_mark_thread_as_done_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "thread_id": 7,
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("activity_mark_thread_as_done", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "DELETE",
            "/notifications/threads/{thread_id}",
            params=None,
            body=None,
            path_params={
                "thread_id": str(tool_input["thread_id"]),
            },
        )

    def test_activity_set_thread_subscription_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "thread_id": 7,
            "ignored": True,
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("activity_set_thread_subscription", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "PUT",
            "/notifications/threads/{thread_id}/subscription",
            params={
                "ignored": str(tool_input["ignored"]),
            },
            body=None,
            path_params={
                "thread_id": str(tool_input["thread_id"]),
            },
        )

    def test_orgs_list_issue_types_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "org": "sample_org",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("orgs_list_issue_types", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "GET",
            "/orgs/{org}/issue-types",
            params=None,
            body=None,
            path_params={
                "org": str(tool_input["org"]),
            },
        )

    def test_teams_list_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "org": "sample_org",
            "per_page": 7,
            "page": 7,
            "team_type": "sample_team_type",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("teams_list", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "GET",
            "/orgs/{org}/teams",
            params={
                "per_page": str(tool_input["per_page"]),
                "page": str(tool_input["page"]),
                "team_type": str(tool_input["team_type"]),
            },
            body=None,
            path_params={
                "org": str(tool_input["org"]),
            },
        )

    def test_teams_list_members_in_org_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "org": "sample_org",
            "team_slug": "sample_team_slug",
            "role": "sample_role",
            "per_page": 7,
            "page": 7,
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("teams_list_members_in_org", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "GET",
            "/orgs/{org}/teams/{team_slug}/members",
            params={
                "role": str(tool_input["role"]),
                "per_page": str(tool_input["per_page"]),
                "page": str(tool_input["page"]),
            },
            body=None,
            path_params={
                "org": str(tool_input["org"]),
                "team_slug": str(tool_input["team_slug"]),
            },
        )

    def test_actions_download_job_logs_for_workflow_run_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "job_id": 7,
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("actions_download_job_logs_for_workflow_run", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "GET",
            "/repos/{owner}/{repo}/actions/jobs/{job_id}/logs",
            params=None,
            body=None,
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
                "job_id": str(tool_input["job_id"]),
            },
        )

    def test_actions_list_repo_workflows_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "per_page": 7,
            "page": 7,
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("actions_list_repo_workflows", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "GET",
            "/repos/{owner}/{repo}/actions/workflows",
            params={
                "per_page": str(tool_input["per_page"]),
                "page": str(tool_input["page"]),
            },
            body=None,
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
            },
        )

    def test_actions_get_workflow_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "workflow_id": {"value": "sample_workflow_id"},
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("actions_get_workflow", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "GET",
            "/repos/{owner}/{repo}/actions/workflows/{workflow_id}",
            params=None,
            body=None,
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
                "workflow_id": str(tool_input["workflow_id"]),
            },
        )

    def test_actions_create_workflow_dispatch_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "workflow_id": {"value": "sample_workflow_id"},
            "ref": "sample_ref",
            "inputs": {"value": "sample_inputs"},
            "return_run_details": True,
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("actions_create_workflow_dispatch", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "POST",
            "/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches",
            params={
                "ref": str(tool_input["ref"]),
                "return_run_details": str(tool_input["return_run_details"]),
            },
            body={
                "value": "sample_inputs",
            },
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
                "workflow_id": str(tool_input["workflow_id"]),
            },
        )

    def test_repos_list_branches_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "protected": True,
            "per_page": 7,
            "page": 7,
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("repos_list_branches", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "GET",
            "/repos/{owner}/{repo}/branches",
            params={
                "protected": str(tool_input["protected"]),
                "per_page": str(tool_input["per_page"]),
                "page": str(tool_input["page"]),
            },
            body=None,
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
            },
        )

    def test_code_scanning_list_alerts_for_repo_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "tool_name": "sample_tool_name",
            "tool_guid": "sample_tool_guid",
            "page": 7,
            "per_page": 7,
            "ref": "sample_ref",
            "pr": 7,
            "direction": "sample_direction",
            "before": "sample_before",
            "after": "sample_after",
            "sort": "sample_sort",
            "state": "sample_state",
            "severity": "sample_severity",
            "assignees": "sample_assignees",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("code_scanning_list_alerts_for_repo", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "GET",
            "/repos/{owner}/{repo}/code-scanning/alerts",
            params={
                "tool_name": str(tool_input["tool_name"]),
                "tool_guid": str(tool_input["tool_guid"]),
                "page": str(tool_input["page"]),
                "per_page": str(tool_input["per_page"]),
                "ref": str(tool_input["ref"]),
                "pr": str(tool_input["pr"]),
                "direction": str(tool_input["direction"]),
                "before": str(tool_input["before"]),
                "after": str(tool_input["after"]),
                "sort": str(tool_input["sort"]),
                "state": str(tool_input["state"]),
                "severity": str(tool_input["severity"]),
                "assignees": str(tool_input["assignees"]),
            },
            body=None,
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
            },
        )

    def test_code_scanning_get_alert_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "alert_number": 7,
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("code_scanning_get_alert", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "GET",
            "/repos/{owner}/{repo}/code-scanning/alerts/{alert_number}",
            params=None,
            body=None,
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
                "alert_number": str(tool_input["alert_number"]),
            },
        )

    def test_repos_list_commits_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "sha": "sample_sha",
            "path": "sample_path",
            "author": "sample_author",
            "committer": "sample_committer",
            "since": "sample_since",
            "until": "sample_until",
            "per_page": 7,
            "page": 7,
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("repos_list_commits", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "GET",
            "/repos/{owner}/{repo}/commits",
            params={
                "sha": str(tool_input["sha"]),
                "path": str(tool_input["path"]),
                "author": str(tool_input["author"]),
                "committer": str(tool_input["committer"]),
                "since": str(tool_input["since"]),
                "until": str(tool_input["until"]),
                "per_page": str(tool_input["per_page"]),
                "page": str(tool_input["page"]),
            },
            body=None,
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
            },
        )

    def test_repos_get_commit_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "page": 7,
            "per_page": 7,
            "ref": "sample_ref",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("repos_get_commit", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "GET",
            "/repos/{owner}/{repo}/commits/{ref}",
            params={
                "page": str(tool_input["page"]),
                "per_page": str(tool_input["per_page"]),
            },
            body=None,
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
                "ref": str(tool_input["ref"]),
            },
        )

    def test_repos_get_content_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "path": "sample_path",
            "ref": "sample_ref",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("repos_get_content", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "GET",
            "/repos/{owner}/{repo}/contents/{path}",
            params={
                "ref": str(tool_input["ref"]),
            },
            body=None,
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
                "path": str(tool_input["path"]),
            },
        )

    def test_repos_create_or_update_file_contents_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "path": "sample_path",
            "message": "sample_message",
            "content": "sample_content",
            "sha": "sample_sha",
            "branch": "sample_branch",
            "committer": {"value": "sample_committer"},
            "author": {"value": "sample_author"},
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("repos_create_or_update_file_contents", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "PUT",
            "/repos/{owner}/{repo}/contents/{path}",
            params={
                "message": str(tool_input["message"]),
                "content": str(tool_input["content"]),
                "sha": str(tool_input["sha"]),
                "branch": str(tool_input["branch"]),
            },
            body={
                "value": "sample_committer",
                "value": "sample_author",
            },
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
                "path": str(tool_input["path"]),
            },
        )

    def test_repos_delete_file_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "path": "sample_path",
            "message": "sample_message",
            "sha": "sample_sha",
            "branch": "sample_branch",
            "committer": {"value": "sample_committer"},
            "author": {"value": "sample_author"},
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("repos_delete_file", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "DELETE",
            "/repos/{owner}/{repo}/contents/{path}",
            params={
                "message": str(tool_input["message"]),
                "sha": str(tool_input["sha"]),
                "branch": str(tool_input["branch"]),
            },
            body={
                "value": "sample_committer",
                "value": "sample_author",
            },
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
                "path": str(tool_input["path"]),
            },
        )

    def test_dependabot_list_alerts_for_repo_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "state": "sample_state",
            "severity": "sample_severity",
            "ecosystem": "sample_ecosystem",
            "package": "sample_package",
            "manifest": "sample_manifest",
            "epss_percentage": "sample_epss_percentage",
            "has": {"value": "sample_has"},
            "assignee": "sample_assignee",
            "scope": "sample_scope",
            "sort": "sample_sort",
            "direction": "sample_direction",
            "before": "sample_before",
            "after": "sample_after",
            "per_page": 7,
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("dependabot_list_alerts_for_repo", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "GET",
            "/repos/{owner}/{repo}/dependabot/alerts",
            params={
                "state": str(tool_input["state"]),
                "severity": str(tool_input["severity"]),
                "ecosystem": str(tool_input["ecosystem"]),
                "package": str(tool_input["package"]),
                "manifest": str(tool_input["manifest"]),
                "epss_percentage": str(tool_input["epss_percentage"]),
                "assignee": str(tool_input["assignee"]),
                "scope": str(tool_input["scope"]),
                "sort": str(tool_input["sort"]),
                "direction": str(tool_input["direction"]),
                "before": str(tool_input["before"]),
                "after": str(tool_input["after"]),
                "per_page": str(tool_input["per_page"]),
            },
            body={
                "value": "sample_has",
            },
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
            },
        )

    def test_dependabot_get_alert_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "alert_number": 7,
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("dependabot_get_alert", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "GET",
            "/repos/{owner}/{repo}/dependabot/alerts/{alert_number}",
            params=None,
            body=None,
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
                "alert_number": str(tool_input["alert_number"]),
            },
        )

    def test_repos_create_fork_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "organization": "sample_organization",
            "name": "sample_name",
            "default_branch_only": True,
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("repos_create_fork", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "POST",
            "/repos/{owner}/{repo}/forks",
            params={
                "organization": str(tool_input["organization"]),
                "name": str(tool_input["name"]),
                "default_branch_only": str(tool_input["default_branch_only"]),
            },
            body=None,
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
            },
        )

    def test_git_create_ref_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "ref": "sample_ref",
            "sha": "sample_sha",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("git_create_ref", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "POST",
            "/repos/{owner}/{repo}/git/refs",
            params={
                "ref": str(tool_input["ref"]),
                "sha": str(tool_input["sha"]),
            },
            body=None,
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
            },
        )

    def test_git_get_tag_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "tag_sha": "sample_tag_sha",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("git_get_tag", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "GET",
            "/repos/{owner}/{repo}/git/tags/{tag_sha}",
            params=None,
            body=None,
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
                "tag_sha": str(tool_input["tag_sha"]),
            },
        )

    def test_git_get_tree_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "tree_sha": "sample_tree_sha",
            "recursive": "sample_recursive",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("git_get_tree", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "GET",
            "/repos/{owner}/{repo}/git/trees/{tree_sha}",
            params={
                "recursive": str(tool_input["recursive"]),
            },
            body=None,
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
                "tree_sha": str(tool_input["tree_sha"]),
            },
        )

    def test_issues_list_for_repo_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "milestone": "sample_milestone",
            "state": "sample_state",
            "assignee": "sample_assignee",
            "type": "sample_type",
            "creator": "sample_creator",
            "mentioned": "sample_mentioned",
            "labels": "sample_labels",
            "sort": "sample_sort",
            "direction": "sample_direction",
            "since": "sample_since",
            "per_page": 7,
            "page": 7,
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("issues_list_for_repo", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "GET",
            "/repos/{owner}/{repo}/issues",
            params={
                "milestone": str(tool_input["milestone"]),
                "state": str(tool_input["state"]),
                "assignee": str(tool_input["assignee"]),
                "type": str(tool_input["type"]),
                "creator": str(tool_input["creator"]),
                "mentioned": str(tool_input["mentioned"]),
                "labels": str(tool_input["labels"]),
                "sort": str(tool_input["sort"]),
                "direction": str(tool_input["direction"]),
                "since": str(tool_input["since"]),
                "per_page": str(tool_input["per_page"]),
                "page": str(tool_input["page"]),
            },
            body=None,
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
            },
        )

    def test_issues_create_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "title": {"value": "sample_title"},
            "body": "sample_body",
            "assignee": "sample_assignee",
            "milestone": {"value": "sample_milestone"},
            "labels": ["sample_labels"],
            "assignees": ["sample_assignees"],
            "type": "sample_type",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("issues_create", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "POST",
            "/repos/{owner}/{repo}/issues",
            params={
                "body": str(tool_input["body"]),
                "assignee": str(tool_input["assignee"]),
                "labels": str(tool_input["labels"]),
                "assignees": str(tool_input["assignees"]),
                "type": str(tool_input["type"]),
            },
            body={
                "value": "sample_title",
                "value": "sample_milestone",
            },
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
            },
        )

    def test_issues_get_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "issue_number": 7,
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("issues_get", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "GET",
            "/repos/{owner}/{repo}/issues/{issue_number}",
            params=None,
            body=None,
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
                "issue_number": str(tool_input["issue_number"]),
            },
        )

    def test_issues_update_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "issue_number": 7,
            "title": {"value": "sample_title"},
            "body": "sample_body",
            "assignee": "sample_assignee",
            "state": "sample_state",
            "state_reason": "sample_state_reason",
            "milestone": {"value": "sample_milestone"},
            "labels": ["sample_labels"],
            "assignees": ["sample_assignees"],
            "issue_field_values": ["sample_issue_field_values"],
            "type": "sample_type",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("issues_update", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "PATCH",
            "/repos/{owner}/{repo}/issues/{issue_number}",
            params={
                "body": str(tool_input["body"]),
                "assignee": str(tool_input["assignee"]),
                "state": str(tool_input["state"]),
                "state_reason": str(tool_input["state_reason"]),
                "labels": str(tool_input["labels"]),
                "assignees": str(tool_input["assignees"]),
                "issue_field_values": str(tool_input["issue_field_values"]),
                "type": str(tool_input["type"]),
            },
            body={
                "value": "sample_title",
                "value": "sample_milestone",
            },
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
                "issue_number": str(tool_input["issue_number"]),
            },
        )

    def test_issues_create_comment_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "issue_number": 7,
            "body": "sample_body",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("issues_create_comment", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "POST",
            "/repos/{owner}/{repo}/issues/{issue_number}/comments",
            params={
                "body": str(tool_input["body"]),
            },
            body=None,
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
                "issue_number": str(tool_input["issue_number"]),
            },
        )

    def test_issues_add_sub_issue_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "issue_number": 7,
            "sub_issue_id": 7,
            "replace_parent": True,
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("issues_add_sub_issue", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "POST",
            "/repos/{owner}/{repo}/issues/{issue_number}/sub_issues",
            params={
                "sub_issue_id": str(tool_input["sub_issue_id"]),
                "replace_parent": str(tool_input["replace_parent"]),
            },
            body=None,
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
                "issue_number": str(tool_input["issue_number"]),
            },
        )

    def test_issues_list_labels_for_repo_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "per_page": 7,
            "page": 7,
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("issues_list_labels_for_repo", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "GET",
            "/repos/{owner}/{repo}/labels",
            params={
                "per_page": str(tool_input["per_page"]),
                "page": str(tool_input["page"]),
            },
            body=None,
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
            },
        )

    def test_issues_create_label_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "name": "sample_name",
            "color": "sample_color",
            "description": "sample_description",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("issues_create_label", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "POST",
            "/repos/{owner}/{repo}/labels",
            params={
                "name": str(tool_input["name"]),
                "color": str(tool_input["color"]),
                "description": str(tool_input["description"]),
            },
            body=None,
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
            },
        )

    def test_issues_get_label_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "name": "sample_name",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("issues_get_label", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "GET",
            "/repos/{owner}/{repo}/labels/{name}",
            params=None,
            body=None,
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
                "name": str(tool_input["name"]),
            },
        )

    def test_pulls_list_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "state": "sample_state",
            "head": "sample_head",
            "base": "sample_base",
            "sort": "sample_sort",
            "direction": "sample_direction",
            "per_page": 7,
            "page": 7,
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("pulls_list", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "GET",
            "/repos/{owner}/{repo}/pulls",
            params={
                "state": str(tool_input["state"]),
                "head": str(tool_input["head"]),
                "base": str(tool_input["base"]),
                "sort": str(tool_input["sort"]),
                "direction": str(tool_input["direction"]),
                "per_page": str(tool_input["per_page"]),
                "page": str(tool_input["page"]),
            },
            body=None,
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
            },
        )

    def test_pulls_create_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "title": "sample_title",
            "head": "sample_head",
            "head_repo": "sample_head_repo",
            "base": "sample_base",
            "body": "sample_body",
            "maintainer_can_modify": True,
            "draft": True,
            "issue": 7,
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("pulls_create", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "POST",
            "/repos/{owner}/{repo}/pulls",
            params={
                "title": str(tool_input["title"]),
                "head": str(tool_input["head"]),
                "head_repo": str(tool_input["head_repo"]),
                "base": str(tool_input["base"]),
                "body": str(tool_input["body"]),
                "maintainer_can_modify": str(tool_input["maintainer_can_modify"]),
                "draft": str(tool_input["draft"]),
                "issue": str(tool_input["issue"]),
            },
            body=None,
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
            },
        )

    def test_pulls_get_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "pull_number": 7,
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("pulls_get", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "GET",
            "/repos/{owner}/{repo}/pulls/{pull_number}",
            params=None,
            body=None,
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
                "pull_number": str(tool_input["pull_number"]),
            },
        )

    def test_pulls_update_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "pull_number": 7,
            "title": "sample_title",
            "body": "sample_body",
            "state": "sample_state",
            "base": "sample_base",
            "maintainer_can_modify": True,
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("pulls_update", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "PATCH",
            "/repos/{owner}/{repo}/pulls/{pull_number}",
            params={
                "title": str(tool_input["title"]),
                "body": str(tool_input["body"]),
                "state": str(tool_input["state"]),
                "base": str(tool_input["base"]),
                "maintainer_can_modify": str(tool_input["maintainer_can_modify"]),
            },
            body=None,
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
                "pull_number": str(tool_input["pull_number"]),
            },
        )

    def test_pulls_create_review_comment_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "pull_number": 7,
            "body": "sample_body",
            "commit_id": "sample_commit_id",
            "path": "sample_path",
            "position": 7,
            "side": "sample_side",
            "line": 7,
            "start_line": 7,
            "start_side": "sample_start_side",
            "in_reply_to": 7,
            "subject_type": "sample_subject_type",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("pulls_create_review_comment", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "POST",
            "/repos/{owner}/{repo}/pulls/{pull_number}/comments",
            params={
                "body": str(tool_input["body"]),
                "commit_id": str(tool_input["commit_id"]),
                "path": str(tool_input["path"]),
                "position": str(tool_input["position"]),
                "side": str(tool_input["side"]),
                "line": str(tool_input["line"]),
                "start_line": str(tool_input["start_line"]),
                "start_side": str(tool_input["start_side"]),
                "in_reply_to": str(tool_input["in_reply_to"]),
                "subject_type": str(tool_input["subject_type"]),
            },
            body=None,
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
                "pull_number": str(tool_input["pull_number"]),
            },
        )

    def test_pulls_create_reply_for_review_comment_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "pull_number": 7,
            "comment_id": 7,
            "body": "sample_body",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("pulls_create_reply_for_review_comment", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "POST",
            "/repos/{owner}/{repo}/pulls/{pull_number}/comments/{comment_id}/replies",
            params={
                "body": str(tool_input["body"]),
            },
            body=None,
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
                "pull_number": str(tool_input["pull_number"]),
                "comment_id": str(tool_input["comment_id"]),
            },
        )

    def test_pulls_merge_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "pull_number": 7,
            "commit_title": "sample_commit_title",
            "commit_message": "sample_commit_message",
            "sha": "sample_sha",
            "merge_method": "sample_merge_method",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("pulls_merge", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "PUT",
            "/repos/{owner}/{repo}/pulls/{pull_number}/merge",
            params={
                "commit_title": str(tool_input["commit_title"]),
                "commit_message": str(tool_input["commit_message"]),
                "sha": str(tool_input["sha"]),
                "merge_method": str(tool_input["merge_method"]),
            },
            body=None,
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
                "pull_number": str(tool_input["pull_number"]),
            },
        )

    def test_pulls_submit_review_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "pull_number": 7,
            "review_id": 7,
            "body": "sample_body",
            "event": "sample_event",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("pulls_submit_review", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "POST",
            "/repos/{owner}/{repo}/pulls/{pull_number}/reviews/{review_id}/events",
            params={
                "body": str(tool_input["body"]),
                "event": str(tool_input["event"]),
            },
            body=None,
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
                "pull_number": str(tool_input["pull_number"]),
                "review_id": str(tool_input["review_id"]),
            },
        )

    def test_pulls_update_branch_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "pull_number": 7,
            "expected_head_sha": "sample_expected_head_sha",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("pulls_update_branch", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "PUT",
            "/repos/{owner}/{repo}/pulls/{pull_number}/update-branch",
            params={
                "expected_head_sha": str(tool_input["expected_head_sha"]),
            },
            body=None,
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
                "pull_number": str(tool_input["pull_number"]),
            },
        )

    def test_repos_list_releases_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "per_page": 7,
            "page": 7,
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("repos_list_releases", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "GET",
            "/repos/{owner}/{repo}/releases",
            params={
                "per_page": str(tool_input["per_page"]),
                "page": str(tool_input["page"]),
            },
            body=None,
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
            },
        )

    def test_repos_get_latest_release_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("repos_get_latest_release", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "GET",
            "/repos/{owner}/{repo}/releases/latest",
            params=None,
            body=None,
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
            },
        )

    def test_repos_get_release_by_tag_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "tag": "sample_tag",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("repos_get_release_by_tag", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "GET",
            "/repos/{owner}/{repo}/releases/tags/{tag}",
            params=None,
            body=None,
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
                "tag": str(tool_input["tag"]),
            },
        )

    def test_secret_scanning_list_alerts_for_repo_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "state": "sample_state",
            "secret_type": "sample_secret_type",
            "resolution": "sample_resolution",
            "assignee": "sample_assignee",
            "sort": "sample_sort",
            "direction": "sample_direction",
            "page": 7,
            "per_page": 7,
            "before": "sample_before",
            "after": "sample_after",
            "validity": "sample_validity",
            "is_publicly_leaked": True,
            "is_multi_repo": True,
            "hide_secret": True,
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("secret_scanning_list_alerts_for_repo", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "GET",
            "/repos/{owner}/{repo}/secret-scanning/alerts",
            params={
                "state": str(tool_input["state"]),
                "secret_type": str(tool_input["secret_type"]),
                "resolution": str(tool_input["resolution"]),
                "assignee": str(tool_input["assignee"]),
                "sort": str(tool_input["sort"]),
                "direction": str(tool_input["direction"]),
                "page": str(tool_input["page"]),
                "per_page": str(tool_input["per_page"]),
                "before": str(tool_input["before"]),
                "after": str(tool_input["after"]),
                "validity": str(tool_input["validity"]),
                "is_publicly_leaked": str(tool_input["is_publicly_leaked"]),
                "is_multi_repo": str(tool_input["is_multi_repo"]),
                "hide_secret": str(tool_input["hide_secret"]),
            },
            body=None,
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
            },
        )

    def test_secret_scanning_get_alert_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "alert_number": 7,
            "hide_secret": True,
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("secret_scanning_get_alert", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "GET",
            "/repos/{owner}/{repo}/secret-scanning/alerts/{alert_number}",
            params={
                "hide_secret": str(tool_input["hide_secret"]),
            },
            body=None,
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
                "alert_number": str(tool_input["alert_number"]),
            },
        )

    def test_security_advisories_list_repository_advisories_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "direction": "sample_direction",
            "sort": "sample_sort",
            "before": "sample_before",
            "after": "sample_after",
            "per_page": 7,
            "state": "sample_state",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("security_advisories_list_repository_advisories", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "GET",
            "/repos/{owner}/{repo}/security-advisories",
            params={
                "direction": str(tool_input["direction"]),
                "sort": str(tool_input["sort"]),
                "before": str(tool_input["before"]),
                "after": str(tool_input["after"]),
                "per_page": str(tool_input["per_page"]),
                "state": str(tool_input["state"]),
            },
            body=None,
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
            },
        )

    def test_activity_set_repo_subscription_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "subscribed": True,
            "ignored": True,
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("activity_set_repo_subscription", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "PUT",
            "/repos/{owner}/{repo}/subscription",
            params={
                "subscribed": str(tool_input["subscribed"]),
                "ignored": str(tool_input["ignored"]),
            },
            body=None,
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
            },
        )

    def test_repos_list_tags_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
            "per_page": 7,
            "page": 7,
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("repos_list_tags", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "GET",
            "/repos/{owner}/{repo}/tags",
            params={
                "per_page": str(tool_input["per_page"]),
                "page": str(tool_input["page"]),
            },
            body=None,
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
            },
        )

    def test_search_code_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "q": "sample_q",
            "sort": "sample_sort",
            "order": "sample_order",
            "per_page": 7,
            "page": 7,
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("search_code", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "GET",
            "/search/code",
            params={
                "q": str(tool_input["q"]),
                "sort": str(tool_input["sort"]),
                "order": str(tool_input["order"]),
                "per_page": str(tool_input["per_page"]),
                "page": str(tool_input["page"]),
            },
            body=None,
            path_params=None,
        )

    def test_search_issues_and_pull_requests_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "q": "sample_q",
            "sort": "sample_sort",
            "order": "sample_order",
            "per_page": 7,
            "page": 7,
            "advanced_search": "sample_advanced_search",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("search_issues_and_pull_requests", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "GET",
            "/search/issues",
            params={
                "q": str(tool_input["q"]),
                "sort": str(tool_input["sort"]),
                "order": str(tool_input["order"]),
                "per_page": str(tool_input["per_page"]),
                "page": str(tool_input["page"]),
                "advanced_search": str(tool_input["advanced_search"]),
            },
            body=None,
            path_params=None,
        )

    def test_search_repos_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "q": "sample_q",
            "sort": "sample_sort",
            "order": "sample_order",
            "per_page": 7,
            "page": 7,
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("search_repos", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "GET",
            "/search/repositories",
            params={
                "q": str(tool_input["q"]),
                "sort": str(tool_input["sort"]),
                "order": str(tool_input["order"]),
                "per_page": str(tool_input["per_page"]),
                "page": str(tool_input["page"]),
            },
            body=None,
            path_params=None,
        )

    def test_search_users_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "q": "sample_q",
            "sort": "sample_sort",
            "order": "sample_order",
            "per_page": 7,
            "page": 7,
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("search_users", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "GET",
            "/search/users",
            params={
                "q": str(tool_input["q"]),
                "sort": str(tool_input["sort"]),
                "order": str(tool_input["order"]),
                "per_page": str(tool_input["per_page"]),
                "page": str(tool_input["page"]),
            },
            body=None,
            path_params=None,
        )

    def test_users_get_authenticated_behavior(self, server, server_module, monkeypatch):
        tool_input = {
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("users_get_authenticated", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "GET",
            "/user",
            params=None,
            body=None,
            path_params=None,
        )

    def test_repos_create_for_authenticated_user_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "name": "sample_name",
            "description": "sample_description",
            "homepage": "sample_homepage",
            "private": True,
            "has_issues": True,
            "has_projects": True,
            "has_wiki": True,
            "has_discussions": True,
            "team_id": 7,
            "auto_init": True,
            "gitignore_template": "sample_gitignore_template",
            "license_template": "sample_license_template",
            "allow_squash_merge": True,
            "allow_merge_commit": True,
            "allow_rebase_merge": True,
            "allow_auto_merge": True,
            "delete_branch_on_merge": True,
            "squash_merge_commit_title": "sample_squash_merge_commit_title",
            "squash_merge_commit_message": "sample_squash_merge_commit_message",
            "merge_commit_title": "sample_merge_commit_title",
            "merge_commit_message": "sample_merge_commit_message",
            "has_downloads": True,
            "is_template": True,
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("repos_create_for_authenticated_user", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "POST",
            "/user/repos",
            params={
                "name": str(tool_input["name"]),
                "description": str(tool_input["description"]),
                "homepage": str(tool_input["homepage"]),
                "private": str(tool_input["private"]),
                "has_issues": str(tool_input["has_issues"]),
                "has_projects": str(tool_input["has_projects"]),
                "has_wiki": str(tool_input["has_wiki"]),
                "has_discussions": str(tool_input["has_discussions"]),
                "team_id": str(tool_input["team_id"]),
                "auto_init": str(tool_input["auto_init"]),
                "gitignore_template": str(tool_input["gitignore_template"]),
                "license_template": str(tool_input["license_template"]),
                "allow_squash_merge": str(tool_input["allow_squash_merge"]),
                "allow_merge_commit": str(tool_input["allow_merge_commit"]),
                "allow_rebase_merge": str(tool_input["allow_rebase_merge"]),
                "allow_auto_merge": str(tool_input["allow_auto_merge"]),
                "delete_branch_on_merge": str(tool_input["delete_branch_on_merge"]),
                "squash_merge_commit_title": str(tool_input["squash_merge_commit_title"]),
                "squash_merge_commit_message": str(tool_input["squash_merge_commit_message"]),
                "merge_commit_title": str(tool_input["merge_commit_title"]),
                "merge_commit_message": str(tool_input["merge_commit_message"]),
                "has_downloads": str(tool_input["has_downloads"]),
                "is_template": str(tool_input["is_template"]),
            },
            body=None,
            path_params=None,
        )

    def test_activity_list_repos_starred_by_authenticated_user_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "sort": "sample_sort",
            "direction": "sample_direction",
            "per_page": 7,
            "page": 7,
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("activity_list_repos_starred_by_authenticated_user", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "GET",
            "/user/starred",
            params={
                "sort": str(tool_input["sort"]),
                "direction": str(tool_input["direction"]),
                "per_page": str(tool_input["per_page"]),
                "page": str(tool_input["page"]),
            },
            body=None,
            path_params=None,
        )

    def test_activity_star_repo_for_authenticated_user_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("activity_star_repo_for_authenticated_user", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "PUT",
            "/user/starred/{owner}/{repo}",
            params=None,
            body=None,
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
            },
        )

    def test_activity_unstar_repo_for_authenticated_user_behavior(self, server, server_module, monkeypatch):
        tool_input = {
            "owner": "sample_owner",
            "repo": "sample_repo",
        }
        mock_request = AsyncMock(return_value="http-call-ok")
        monkeypatch.setattr(server_module._backend, "request", mock_request)

        result = _run(server.call_tool("activity_unstar_repo_for_authenticated_user", tool_input))

        assert _extract_text_result(result) == "http-call-ok"
        mock_request.assert_awaited_once_with(
            "DELETE",
            "/user/starred/{owner}/{repo}",
            params=None,
            body=None,
            path_params={
                "owner": str(tool_input["owner"]),
                "repo": str(tool_input["repo"]),
            },
        )

