"""Server-delivered MCP prompts (skills) for github-scoped."""

from mcp.server.fastmcp import FastMCP


def register_prompts(server: FastMCP) -> None:
    """Register prompts with the server."""

    @server.prompt("use_github_scoped")
    async def use_github_scoped_prompt() -> str:
        """Guide for using github-scoped tools effectively"""
        return """You have access to the github-scoped MCP server with these tools:

- security_advisories_list_global_advisories: GET /advisories - List global security advisories
- security_advisories_get_global_advisory: GET /advisories/{ghsa_id} - Get a global security advisory
- gists_list: GET /gists - List gists for the authenticated user
- gists_create: POST /gists - Create a gist
- gists_get: GET /gists/{gist_id} - Get a gist
- gists_update: PATCH /gists/{gist_id} - Update a gist
- get_notifications: GET /notifications - List notifications for the authenticated user
- activity_mark_notifications_as_read: PUT /notifications - Mark notifications as read
- activity_get_thread: GET /notifications/threads/{thread_id} - Get a thread
- activity_mark_thread_as_done: DELETE /notifications/threads/{thread_id} - Mark a thread as done
- activity_set_thread_subscription: PUT /notifications/threads/{thread_id}/subscription - Set a thread subscription
- orgs_list_issue_types: GET /orgs/{org}/issue-types - List issue types for an organization
- teams_list: GET /orgs/{org}/teams - List teams
- teams_list_members_in_org: GET /orgs/{org}/teams/{team_slug}/members - List team members
- actions_download_job_logs_for_workflow_run: GET /repos/{owner}/{repo}/actions/jobs/{job_id}/logs - Download job logs for a workflow run
- actions_list_repo_workflows: GET /repos/{owner}/{repo}/actions/workflows - List repository workflows
- actions_get_workflow: GET /repos/{owner}/{repo}/actions/workflows/{workflow_id} - Get a workflow
- actions_create_workflow_dispatch: POST /repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches - Create a workflow dispatch event
- repos_list_branches: GET /repos/{owner}/{repo}/branches - List branches
- code_scanning_list_alerts_for_repo: GET /repos/{owner}/{repo}/code-scanning/alerts - List code scanning alerts for a repository

Use the appropriate tool based on the user's request. Always check required parameters before calling a tool."""

    @server.prompt("debug_github_scoped")
    async def debug_github_scoped_prompt(error_message: str) -> str:
        """Diagnose issues with github-scoped operations"""
        return """The user encountered an error while using github-scoped.

Error: {{error_message}}

Available tools: security_advisories_list_global_advisories, security_advisories_get_global_advisory, gists_list, gists_create, gists_get, gists_update, get_notifications, activity_mark_notifications_as_read, activity_get_thread, activity_mark_thread_as_done, activity_set_thread_subscription, orgs_list_issue_types, teams_list, teams_list_members_in_org, actions_download_job_logs_for_workflow_run

Diagnose the issue and suggest which tool to use to resolve it."""

