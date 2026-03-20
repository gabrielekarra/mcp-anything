"""Resources for github-scoped."""

import json

from mcp.server.fastmcp import FastMCP

_TOOL_METADATA = {
    "security_advisories_list_global_advisories": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::security-advisories/list-global-advisories",
        "manual_steps": [],
    },
    "security_advisories_get_global_advisory": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::security-advisories/get-global-advisory",
        "manual_steps": [],
    },
    "gists_list": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::gists/list",
        "manual_steps": [],
    },
    "gists_create": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::gists/create",
        "manual_steps": [],
    },
    "gists_get": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::gists/get",
        "manual_steps": [],
    },
    "gists_update": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::gists/update",
        "manual_steps": [],
    },
    "get_notifications": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::activity/list-notifications-for-authenticated-user",
        "manual_steps": [],
    },
    "activity_mark_notifications_as_read": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::activity/mark-notifications-as-read",
        "manual_steps": [],
    },
    "activity_get_thread": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::activity/get-thread",
        "manual_steps": [],
    },
    "activity_mark_thread_as_done": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::activity/mark-thread-as-done",
        "manual_steps": [],
    },
    "activity_set_thread_subscription": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::activity/set-thread-subscription",
        "manual_steps": [],
    },
    "orgs_list_issue_types": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::orgs/list-issue-types",
        "manual_steps": [],
    },
    "teams_list": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::teams/list",
        "manual_steps": [],
    },
    "teams_list_members_in_org": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::teams/list-members-in-org",
        "manual_steps": [],
    },
    "actions_download_job_logs_for_workflow_run": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::actions/download-job-logs-for-workflow-run",
        "manual_steps": [],
    },
    "actions_list_repo_workflows": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::actions/list-repo-workflows",
        "manual_steps": [],
    },
    "actions_get_workflow": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::actions/get-workflow",
        "manual_steps": [],
    },
    "actions_create_workflow_dispatch": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::actions/create-workflow-dispatch",
        "manual_steps": [],
    },
    "repos_list_branches": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::repos/list-branches",
        "manual_steps": [],
    },
    "code_scanning_list_alerts_for_repo": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::code-scanning/list-alerts-for-repo",
        "manual_steps": [],
    },
    "code_scanning_get_alert": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::code-scanning/get-alert",
        "manual_steps": [],
    },
    "repos_list_commits": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::repos/list-commits",
        "manual_steps": [],
    },
    "repos_get_commit": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::repos/get-commit",
        "manual_steps": [],
    },
    "repos_get_content": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::repos/get-content",
        "manual_steps": [],
    },
    "repos_create_or_update_file_contents": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::repos/create-or-update-file-contents",
        "manual_steps": [],
    },
    "repos_delete_file": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::repos/delete-file",
        "manual_steps": [],
    },
    "dependabot_list_alerts_for_repo": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::dependabot/list-alerts-for-repo",
        "manual_steps": [],
    },
    "dependabot_get_alert": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::dependabot/get-alert",
        "manual_steps": [],
    },
    "repos_create_fork": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::repos/create-fork",
        "manual_steps": [],
    },
    "git_create_ref": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::git/create-ref",
        "manual_steps": [],
    },
    "git_get_tag": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::git/get-tag",
        "manual_steps": [],
    },
    "git_get_tree": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::git/get-tree",
        "manual_steps": [],
    },
    "issues_list_for_repo": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::issues/list-for-repo",
        "manual_steps": [],
    },
    "issues_create": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::issues/create",
        "manual_steps": [],
    },
    "issues_get": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::issues/get",
        "manual_steps": [],
    },
    "issues_update": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::issues/update",
        "manual_steps": [],
    },
    "issues_create_comment": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::issues/create-comment",
        "manual_steps": [],
    },
    "issues_add_sub_issue": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::issues/add-sub-issue",
        "manual_steps": [],
    },
    "issues_list_labels_for_repo": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::issues/list-labels-for-repo",
        "manual_steps": [],
    },
    "issues_create_label": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::issues/create-label",
        "manual_steps": [],
    },
    "issues_get_label": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::issues/get-label",
        "manual_steps": [],
    },
    "pulls_list": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::pulls/list",
        "manual_steps": [],
    },
    "pulls_create": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::pulls/create",
        "manual_steps": [],
    },
    "pulls_get": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::pulls/get",
        "manual_steps": [],
    },
    "pulls_update": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::pulls/update",
        "manual_steps": [],
    },
    "pulls_create_review_comment": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::pulls/create-review-comment",
        "manual_steps": [],
    },
    "pulls_create_reply_for_review_comment": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::pulls/create-reply-for-review-comment",
        "manual_steps": [],
    },
    "pulls_merge": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::pulls/merge",
        "manual_steps": [],
    },
    "pulls_submit_review": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::pulls/submit-review",
        "manual_steps": [],
    },
    "pulls_update_branch": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::pulls/update-branch",
        "manual_steps": [],
    },
    "repos_list_releases": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::repos/list-releases",
        "manual_steps": [],
    },
    "repos_get_latest_release": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::repos/get-latest-release",
        "manual_steps": [],
    },
    "repos_get_release_by_tag": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::repos/get-release-by-tag",
        "manual_steps": [],
    },
    "secret_scanning_list_alerts_for_repo": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::secret-scanning/list-alerts-for-repo",
        "manual_steps": [],
    },
    "secret_scanning_get_alert": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::secret-scanning/get-alert",
        "manual_steps": [],
    },
    "security_advisories_list_repository_advisories": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::security-advisories/list-repository-advisories",
        "manual_steps": [],
    },
    "activity_set_repo_subscription": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::activity/set-repo-subscription",
        "manual_steps": [],
    },
    "repos_list_tags": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::repos/list-tags",
        "manual_steps": [],
    },
    "search_code": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::search/code",
        "manual_steps": [],
    },
    "search_issues_and_pull_requests": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::search/issues-and-pull-requests",
        "manual_steps": [],
    },
    "search_repos": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::search/repos",
        "manual_steps": [],
    },
    "search_users": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::search/users",
        "manual_steps": [],
    },
    "users_get_authenticated": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::users/get-authenticated",
        "manual_steps": [],
    },
    "repos_create_for_authenticated_user": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::repos/create-for-authenticated-user",
        "manual_steps": [],
    },
    "activity_list_repos_starred_by_authenticated_user": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::activity/list-repos-starred-by-authenticated-user",
        "manual_steps": [],
    },
    "activity_star_repo_for_authenticated_user": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::activity/star-repo-for-authenticated-user",
        "manual_steps": [],
    },
    "activity_unstar_repo_for_authenticated_user": {
        "generation_status": "proxy",
        "generation_notes": "Proxies requests to the detected HTTP API.",
        "implementation_hint": "Source: openapi.json::activity/unstar-repo-for-authenticated-user",
        "manual_steps": [],
    },
}


def register_resources(server: FastMCP, backend) -> None:
    """Register resources with the server."""

    @server.resource("app://github-scoped/status")
    async def github_scoped_status() -> str:
        """Current status and version of github-scoped"""
        return json.dumps({
            "name": "github-scoped",
            "status": "running",
            "tool_generation": {
                "ready": 0,
                "proxy": 67,
                "scaffolded": 0,
                "stubbed": 0,
            },
        }, indent=2)

    @server.resource("app://github-scoped/commands")
    async def github_scoped_commands() -> str:
        """Available commands and tools in github-scoped"""
        tools = await server.list_tools()
        commands = []
        for tool in tools:
            metadata = _TOOL_METADATA.get(tool.name, {})
            commands.append({
                "name": tool.name,
                "description": tool.description or "",
                "generation_status": metadata.get("generation_status", "ready"),
                "generation_notes": metadata.get("generation_notes", ""),
                "manual_steps": metadata.get("manual_steps", []),
            })
        return json.dumps({"commands": commands}, indent=2)

    @server.resource("docs://github-scoped/tool-index")
    async def github_scoped_tool_index() -> str:
        """Complete index of all github-scoped tools with parameters and usage"""
        # Dynamic documentation resource
        tools = await server.list_tools()
        doc_entries = []
        for tool in tools:
            metadata = _TOOL_METADATA.get(tool.name, {})
            entry = {"name": tool.name, "description": tool.description or ""}
            if hasattr(tool, "inputSchema") and tool.inputSchema:
                entry["parameters"] = tool.inputSchema.get("properties", {})
                entry["required"] = tool.inputSchema.get("required", [])
            entry["generation_status"] = metadata.get("generation_status", "ready")
            entry["generation_notes"] = metadata.get("generation_notes", "")
            entry["implementation_hint"] = metadata.get("implementation_hint", "")
            entry["manual_steps"] = metadata.get("manual_steps", [])
            doc_entries.append(entry)
        return json.dumps({
            "server": "github-scoped",
            "resource": "docs://github-scoped/tool-index",
            "tools": doc_entries,
        }, indent=2)

    @server.resource("docs://github-scoped/api")
    async def github_scoped_api_docs() -> str:
        """Documentation for github-scoped api capabilities"""
        # Dynamic documentation resource
        tools = await server.list_tools()
        doc_entries = []
        for tool in tools:
            metadata = _TOOL_METADATA.get(tool.name, {})
            entry = {"name": tool.name, "description": tool.description or ""}
            if hasattr(tool, "inputSchema") and tool.inputSchema:
                entry["parameters"] = tool.inputSchema.get("properties", {})
                entry["required"] = tool.inputSchema.get("required", [])
            entry["generation_status"] = metadata.get("generation_status", "ready")
            entry["generation_notes"] = metadata.get("generation_notes", "")
            entry["implementation_hint"] = metadata.get("implementation_hint", "")
            entry["manual_steps"] = metadata.get("manual_steps", [])
            doc_entries.append(entry)
        return json.dumps({
            "server": "github-scoped",
            "resource": "docs://github-scoped/api",
            "tools": doc_entries,
        }, indent=2)

