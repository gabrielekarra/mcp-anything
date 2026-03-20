"""Protocol compliance tests for github-scoped MCP server."""

import asyncio
import json

import pytest



def _run(awaitable):
    """Run async FastMCP helpers in synchronous pytest tests."""
    return asyncio.run(awaitable)


def _resource_text(contents):
    """Extract plain text from FastMCP read_resource()."""
    assert isinstance(contents, list)
    assert contents, "resource returned no content"
    first = contents[0]
    return getattr(first, "content", str(first))


class TestMCPCompliance:
    """Verify generated server integration points."""

    def test_server_creation(self, server):
        assert server is not None
        assert server.name == "github-scoped"

    def test_registered_tools_match_design(self, server):
        tools = _run(server.list_tools())
        names = {tool.name for tool in tools}
        assert names == {
            "security_advisories_list_global_advisories",
            "security_advisories_get_global_advisory",
            "gists_list",
            "gists_create",
            "gists_get",
            "gists_update",
            "get_notifications",
            "activity_mark_notifications_as_read",
            "activity_get_thread",
            "activity_mark_thread_as_done",
            "activity_set_thread_subscription",
            "orgs_list_issue_types",
            "teams_list",
            "teams_list_members_in_org",
            "actions_download_job_logs_for_workflow_run",
            "actions_list_repo_workflows",
            "actions_get_workflow",
            "actions_create_workflow_dispatch",
            "repos_list_branches",
            "code_scanning_list_alerts_for_repo",
            "code_scanning_get_alert",
            "repos_list_commits",
            "repos_get_commit",
            "repos_get_content",
            "repos_create_or_update_file_contents",
            "repos_delete_file",
            "dependabot_list_alerts_for_repo",
            "dependabot_get_alert",
            "repos_create_fork",
            "git_create_ref",
            "git_get_tag",
            "git_get_tree",
            "issues_list_for_repo",
            "issues_create",
            "issues_get",
            "issues_update",
            "issues_create_comment",
            "issues_add_sub_issue",
            "issues_list_labels_for_repo",
            "issues_create_label",
            "issues_get_label",
            "pulls_list",
            "pulls_create",
            "pulls_get",
            "pulls_update",
            "pulls_create_review_comment",
            "pulls_create_reply_for_review_comment",
            "pulls_merge",
            "pulls_submit_review",
            "pulls_update_branch",
            "repos_list_releases",
            "repos_get_latest_release",
            "repos_get_release_by_tag",
            "secret_scanning_list_alerts_for_repo",
            "secret_scanning_get_alert",
            "security_advisories_list_repository_advisories",
            "activity_set_repo_subscription",
            "repos_list_tags",
            "search_code",
            "search_issues_and_pull_requests",
            "search_repos",
            "search_users",
            "users_get_authenticated",
            "repos_create_for_authenticated_user",
            "activity_list_repos_starred_by_authenticated_user",
            "activity_star_repo_for_authenticated_user",
            "activity_unstar_repo_for_authenticated_user",
        }

    def test_registered_resources_match_design(self, server):
        resources = _run(server.list_resources())
        uris = {str(resource.uri) for resource in resources}
        assert uris == {
            "app://github-scoped/status",
            "app://github-scoped/commands",
            "docs://github-scoped/tool-index",
            "docs://github-scoped/api",
        }

    def test_commands_resource_lists_tools(self, server):
        payload = _resource_text(_run(server.read_resource("app://github-scoped/commands")))
        data = json.loads(payload)
        command_names = {item["name"] for item in data["commands"]}
        assert {
            "security_advisories_list_global_advisories",
            "security_advisories_get_global_advisory",
            "gists_list",
            "gists_create",
            "gists_get",
            "gists_update",
            "get_notifications",
            "activity_mark_notifications_as_read",
            "activity_get_thread",
            "activity_mark_thread_as_done",
            "activity_set_thread_subscription",
            "orgs_list_issue_types",
            "teams_list",
            "teams_list_members_in_org",
            "actions_download_job_logs_for_workflow_run",
            "actions_list_repo_workflows",
            "actions_get_workflow",
            "actions_create_workflow_dispatch",
            "repos_list_branches",
            "code_scanning_list_alerts_for_repo",
            "code_scanning_get_alert",
            "repos_list_commits",
            "repos_get_commit",
            "repos_get_content",
            "repos_create_or_update_file_contents",
            "repos_delete_file",
            "dependabot_list_alerts_for_repo",
            "dependabot_get_alert",
            "repos_create_fork",
            "git_create_ref",
            "git_get_tag",
            "git_get_tree",
            "issues_list_for_repo",
            "issues_create",
            "issues_get",
            "issues_update",
            "issues_create_comment",
            "issues_add_sub_issue",
            "issues_list_labels_for_repo",
            "issues_create_label",
            "issues_get_label",
            "pulls_list",
            "pulls_create",
            "pulls_get",
            "pulls_update",
            "pulls_create_review_comment",
            "pulls_create_reply_for_review_comment",
            "pulls_merge",
            "pulls_submit_review",
            "pulls_update_branch",
            "repos_list_releases",
            "repos_get_latest_release",
            "repos_get_release_by_tag",
            "secret_scanning_list_alerts_for_repo",
            "secret_scanning_get_alert",
            "security_advisories_list_repository_advisories",
            "activity_set_repo_subscription",
            "repos_list_tags",
            "search_code",
            "search_issues_and_pull_requests",
            "search_repos",
            "search_users",
            "users_get_authenticated",
            "repos_create_for_authenticated_user",
            "activity_list_repos_starred_by_authenticated_user",
            "activity_star_repo_for_authenticated_user",
            "activity_unstar_repo_for_authenticated_user",
        }.issubset(command_names)
        for item in data["commands"]:
            assert item["generation_status"] in {"ready", "proxy", "scaffolded", "stubbed"}
            assert "generation_notes" in item
            assert "manual_steps" in item

    def test_reads_resource_1(self, server):
        payload = _resource_text(_run(server.read_resource("app://github-scoped/status")))
        data = json.loads(payload)
        assert isinstance(data, dict)
        assert data["name"] == "github-scoped"
        assert "tool_generation" in data

    def test_reads_resource_2(self, server):
        payload = _resource_text(_run(server.read_resource("app://github-scoped/commands")))
        data = json.loads(payload)
        assert isinstance(data, dict)
        assert "commands" in data

    def test_reads_resource_3(self, server):
        payload = _resource_text(_run(server.read_resource("docs://github-scoped/tool-index")))
        data = json.loads(payload)
        assert isinstance(data, dict)
        assert data["server"] == "github-scoped"
        for entry in data["tools"]:
            assert entry["generation_status"] in {"ready", "proxy", "scaffolded", "stubbed"}
            assert "implementation_hint" in entry

    def test_reads_resource_4(self, server):
        payload = _resource_text(_run(server.read_resource("docs://github-scoped/api")))
        data = json.loads(payload)
        assert isinstance(data, dict)
        assert data["server"] == "github-scoped"
        for entry in data["tools"]:
            assert entry["generation_status"] in {"ready", "proxy", "scaffolded", "stubbed"}
            assert "implementation_hint" in entry


    def test_registered_prompts_match_design(self, server):
        prompts = _run(server.list_prompts())
        names = {prompt.name for prompt in prompts}
        assert names == {
            "use_github_scoped",
            "debug_github_scoped",
        }

    def test_get_prompt_use_github_scoped(self, server):
        prompt_result = _run(server.get_prompt("use_github_scoped", {
        }))
        assert prompt_result.messages
        message = prompt_result.messages[0]
        assert getattr(message.content, "text", "")

    def test_get_prompt_debug_github_scoped(self, server):
        prompt_result = _run(server.get_prompt("debug_github_scoped", {
            "error_message": "sample_error_message",
        }))
        assert prompt_result.messages
        message = prompt_result.messages[0]
        assert getattr(message.content, "text", "")

