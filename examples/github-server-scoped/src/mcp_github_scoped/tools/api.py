"""api tools for github-scoped."""

import inspect
import json
import sys
import importlib
import importlib.util
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from mcp_github_scoped.backend import BackendError

# Instance cache for reusing class instances across tool calls
_instance_cache: dict[str, object] = {}


def _get_or_create_instance(mod, class_name: str, **init_kwargs):
    """Get a cached class instance or create a new one."""
    cache_key = f"{mod.__name__}.{class_name}"
    if init_kwargs:
        # When explicit init args are provided, always create fresh
        cls = getattr(mod, class_name)
        return cls(**init_kwargs)
    if cache_key not in _instance_cache:
        cls = getattr(mod, class_name)
        try:
            _instance_cache[cache_key] = cls()
        except TypeError:
            # __init__ requires arguments we don't have — try with empty defaults
            import inspect as _ins
            sig = _ins.signature(cls.__init__)
            kwargs = {}
            for name, param in sig.parameters.items():
                if name == "self":
                    continue
                if param.default is not _ins.Parameter.empty:
                    kwargs[name] = param.default
                elif param.annotation is str or param.annotation == "str":
                    kwargs[name] = ""
                elif param.annotation is int or param.annotation == "int":
                    kwargs[name] = 0
                elif param.annotation is bool or param.annotation == "bool":
                    kwargs[name] = False
                elif param.annotation is list or param.annotation == "list":
                    kwargs[name] = []
                elif param.annotation is dict or param.annotation == "dict":
                    kwargs[name] = {}
                else:
                    kwargs[name] = None
            _instance_cache[cache_key] = cls(**kwargs)
    return _instance_cache[cache_key]


def _setup_import_path(codebase_path: str):
    """Add codebase to sys.path for imports."""
    codebase = Path(codebase_path)
    for path in [str(codebase), str(codebase.parent)]:
        if path not in sys.path:
            sys.path.insert(0, path)


def _load_source_module(codebase_path: str, module_path: str):
    """Load a module from the source codebase, avoiding package name collisions.

    Strategy:
    1. If codebase is inside a proper Python package (has __init__.py in parent),
       use the package's canonical import path.
    2. Otherwise, use importlib.util.spec_from_file_location to load directly
       from the source file, bypassing sys.modules name conflicts.
    """
    codebase = Path(codebase_path)

    # Check if codebase is itself a Python package (e.g., /path/to/wand/)
    if (codebase / "__init__.py").exists():
        # This is a package — import using package.module path
        package_name = codebase.name
        parent_dir = str(codebase.parent)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        full_module = f"{package_name}.{module_path}" if module_path != package_name else package_name
        try:
            return importlib.import_module(full_module)
        except ImportError:
            pass

    # For standalone files, load directly by file path to avoid name collisions
    parts = module_path.split(".")
    file_path = codebase / (parts[-1] + ".py") if len(parts) == 1 else codebase / "/".join(parts[:-1]) / (parts[-1] + ".py")
    if not file_path.exists():
        file_path = codebase / (module_path.replace(".", "/") + ".py")
    if not file_path.exists():
        # Final fallback: regular import
        return importlib.import_module(module_path)

    # Use a collision-safe name in sys.modules
    safe_name = f"_mcp_src_{codebase.name}_.{module_path}"
    if safe_name in sys.modules:
        return sys.modules[safe_name]

    spec = importlib.util.spec_from_file_location(safe_name, file_path,
        submodule_search_locations=[str(codebase)])
    if spec is None or spec.loader is None:
        return importlib.import_module(module_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[safe_name] = mod
    spec.loader.exec_module(mod)
    return mod


def register_tools(server: FastMCP, backend) -> None:
    """Register api tools with the server."""

    @server.tool()
    async def security_advisories_list_global_advisories(
        ghsa_id: str | None = None,
        type: str | None = None,
        cve_id: str | None = None,
        ecosystem: str | None = None,
        severity: str | None = None,
        cwes: dict | None = None,
        is_withdrawn: bool | None = None,
        affects: dict | None = None,
        published: str | None = None,
        updated: str | None = None,
        modified: str | None = None,
        epss_percentage: str | None = None,
        epss_percentile: str | None = None,
        before: str | None = None,
        after: str | None = None,
        direction: str | None = None,
        per_page: int | None = None,
        sort: str | None = None,
    ) -> str:
        """GET /advisories - List global security advisories"""
        # HTTP GET /advisories
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        if ghsa_id is not None:
            query_params["ghsa_id"] = str(ghsa_id)
        if type is not None:
            query_params["type"] = str(type)
        if cve_id is not None:
            query_params["cve_id"] = str(cve_id)
        if ecosystem is not None:
            query_params["ecosystem"] = str(ecosystem)
        if severity is not None:
            query_params["severity"] = str(severity)
        request_body = cwes if isinstance(cwes, dict) else {"data": cwes}
        if is_withdrawn is not None:
            query_params["is_withdrawn"] = str(is_withdrawn)
        request_body = affects if isinstance(affects, dict) else {"data": affects}
        if published is not None:
            query_params["published"] = str(published)
        if updated is not None:
            query_params["updated"] = str(updated)
        if modified is not None:
            query_params["modified"] = str(modified)
        if epss_percentage is not None:
            query_params["epss_percentage"] = str(epss_percentage)
        if epss_percentile is not None:
            query_params["epss_percentile"] = str(epss_percentile)
        if before is not None:
            query_params["before"] = str(before)
        if after is not None:
            query_params["after"] = str(after)
        if direction is not None:
            query_params["direction"] = str(direction)
        if per_page is not None:
            query_params["per_page"] = str(per_page)
        if sort is not None:
            query_params["sort"] = str(sort)
        try:
            return await backend.request(
                "GET",
                "/advisories",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def security_advisories_get_global_advisory(
        ghsa_id: str,
    ) -> str:
        """GET /advisories/{ghsa_id} - Get a global security advisory"""
        # HTTP GET /advisories/{ghsa_id}
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["ghsa_id"] = str(ghsa_id)
        try:
            return await backend.request(
                "GET",
                "/advisories/{ghsa_id}",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def gists_list(
        since: str | None = None,
        per_page: int | None = None,
        page: int | None = None,
    ) -> str:
        """GET /gists - List gists for the authenticated user"""
        # HTTP GET /gists
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        if since is not None:
            query_params["since"] = str(since)
        if per_page is not None:
            query_params["per_page"] = str(per_page)
        if page is not None:
            query_params["page"] = str(page)
        try:
            return await backend.request(
                "GET",
                "/gists",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def gists_create(
        files: dict,
        description: str | None = None,
        public: dict | None = None,
    ) -> str:
        """POST /gists - Create a gist"""
        # HTTP POST /gists
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        if description is not None:
            query_params["description"] = str(description)
        request_body = files if isinstance(files, dict) else {"data": files}
        request_body = public if isinstance(public, dict) else {"data": public}
        try:
            return await backend.request(
                "POST",
                "/gists",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def gists_get(
        gist_id: str,
    ) -> str:
        """GET /gists/{gist_id} - Get a gist"""
        # HTTP GET /gists/{gist_id}
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["gist_id"] = str(gist_id)
        try:
            return await backend.request(
                "GET",
                "/gists/{gist_id}",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def gists_update(
        gist_id: str,
        description: str | None = None,
        files: dict | None = None,
    ) -> str:
        """PATCH /gists/{gist_id} - Update a gist"""
        # HTTP PATCH /gists/{gist_id}
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["gist_id"] = str(gist_id)
        if description is not None:
            query_params["description"] = str(description)
        request_body = files if isinstance(files, dict) else {"data": files}
        try:
            return await backend.request(
                "PATCH",
                "/gists/{gist_id}",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def get_notifications(
        all: bool | None = None,
        participating: bool | None = None,
        since: str | None = None,
        before: str | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> str:
        """GET /notifications - List notifications for the authenticated user"""
        # HTTP GET /notifications
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        if all is not None:
            query_params["all"] = str(all)
        if participating is not None:
            query_params["participating"] = str(participating)
        if since is not None:
            query_params["since"] = str(since)
        if before is not None:
            query_params["before"] = str(before)
        if page is not None:
            query_params["page"] = str(page)
        if per_page is not None:
            query_params["per_page"] = str(per_page)
        try:
            return await backend.request(
                "GET",
                "/notifications",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def activity_mark_notifications_as_read(
        last_read_at: str | None = None,
        read: bool | None = None,
    ) -> str:
        """PUT /notifications - Mark notifications as read"""
        # HTTP PUT /notifications
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        if last_read_at is not None:
            query_params["last_read_at"] = str(last_read_at)
        if read is not None:
            query_params["read"] = str(read)
        try:
            return await backend.request(
                "PUT",
                "/notifications",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def activity_get_thread(
        thread_id: int,
    ) -> str:
        """GET /notifications/threads/{thread_id} - Get a thread"""
        # HTTP GET /notifications/threads/{thread_id}
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["thread_id"] = str(thread_id)
        try:
            return await backend.request(
                "GET",
                "/notifications/threads/{thread_id}",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def activity_mark_thread_as_done(
        thread_id: int,
    ) -> str:
        """DELETE /notifications/threads/{thread_id} - Mark a thread as done"""
        # HTTP DELETE /notifications/threads/{thread_id}
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["thread_id"] = str(thread_id)
        try:
            return await backend.request(
                "DELETE",
                "/notifications/threads/{thread_id}",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def activity_set_thread_subscription(
        thread_id: int,
        ignored: bool | None = None,
    ) -> str:
        """PUT /notifications/threads/{thread_id}/subscription - Set a thread subscription"""
        # HTTP PUT /notifications/threads/{thread_id}/subscription
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["thread_id"] = str(thread_id)
        if ignored is not None:
            query_params["ignored"] = str(ignored)
        try:
            return await backend.request(
                "PUT",
                "/notifications/threads/{thread_id}/subscription",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def orgs_list_issue_types(
        org: str,
    ) -> str:
        """GET /orgs/{org}/issue-types - List issue types for an organization"""
        # HTTP GET /orgs/{org}/issue-types
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["org"] = str(org)
        try:
            return await backend.request(
                "GET",
                "/orgs/{org}/issue-types",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def teams_list(
        org: str,
        per_page: int | None = None,
        page: int | None = None,
        team_type: str | None = None,
    ) -> str:
        """GET /orgs/{org}/teams - List teams"""
        # HTTP GET /orgs/{org}/teams
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["org"] = str(org)
        if per_page is not None:
            query_params["per_page"] = str(per_page)
        if page is not None:
            query_params["page"] = str(page)
        if team_type is not None:
            query_params["team_type"] = str(team_type)
        try:
            return await backend.request(
                "GET",
                "/orgs/{org}/teams",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def teams_list_members_in_org(
        org: str,
        team_slug: str,
        role: str | None = None,
        per_page: int | None = None,
        page: int | None = None,
    ) -> str:
        """GET /orgs/{org}/teams/{team_slug}/members - List team members"""
        # HTTP GET /orgs/{org}/teams/{team_slug}/members
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["org"] = str(org)
        path_params["team_slug"] = str(team_slug)
        if role is not None:
            query_params["role"] = str(role)
        if per_page is not None:
            query_params["per_page"] = str(per_page)
        if page is not None:
            query_params["page"] = str(page)
        try:
            return await backend.request(
                "GET",
                "/orgs/{org}/teams/{team_slug}/members",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def actions_download_job_logs_for_workflow_run(
        owner: str,
        repo: str,
        job_id: int,
    ) -> str:
        """GET /repos/{owner}/{repo}/actions/jobs/{job_id}/logs - Download job logs for a workflow run"""
        # HTTP GET /repos/{owner}/{repo}/actions/jobs/{job_id}/logs
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        path_params["job_id"] = str(job_id)
        try:
            return await backend.request(
                "GET",
                "/repos/{owner}/{repo}/actions/jobs/{job_id}/logs",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def actions_list_repo_workflows(
        owner: str,
        repo: str,
        per_page: int | None = None,
        page: int | None = None,
    ) -> str:
        """GET /repos/{owner}/{repo}/actions/workflows - List repository workflows"""
        # HTTP GET /repos/{owner}/{repo}/actions/workflows
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        if per_page is not None:
            query_params["per_page"] = str(per_page)
        if page is not None:
            query_params["page"] = str(page)
        try:
            return await backend.request(
                "GET",
                "/repos/{owner}/{repo}/actions/workflows",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def actions_get_workflow(
        owner: str,
        repo: str,
        workflow_id: dict,
    ) -> str:
        """GET /repos/{owner}/{repo}/actions/workflows/{workflow_id} - Get a workflow"""
        # HTTP GET /repos/{owner}/{repo}/actions/workflows/{workflow_id}
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        path_params["workflow_id"] = str(workflow_id)
        try:
            return await backend.request(
                "GET",
                "/repos/{owner}/{repo}/actions/workflows/{workflow_id}",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def actions_create_workflow_dispatch(
        owner: str,
        repo: str,
        workflow_id: dict,
        ref: str,
        inputs: dict | None = None,
        return_run_details: bool | None = None,
    ) -> str:
        """POST /repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches - Create a workflow dispatch event"""
        # HTTP POST /repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        path_params["workflow_id"] = str(workflow_id)
        if ref is not None:
            query_params["ref"] = str(ref)
        request_body = inputs if isinstance(inputs, dict) else {"data": inputs}
        if return_run_details is not None:
            query_params["return_run_details"] = str(return_run_details)
        try:
            return await backend.request(
                "POST",
                "/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def repos_list_branches(
        owner: str,
        repo: str,
        protected: bool | None = None,
        per_page: int | None = None,
        page: int | None = None,
    ) -> str:
        """GET /repos/{owner}/{repo}/branches - List branches"""
        # HTTP GET /repos/{owner}/{repo}/branches
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        if protected is not None:
            query_params["protected"] = str(protected)
        if per_page is not None:
            query_params["per_page"] = str(per_page)
        if page is not None:
            query_params["page"] = str(page)
        try:
            return await backend.request(
                "GET",
                "/repos/{owner}/{repo}/branches",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def code_scanning_list_alerts_for_repo(
        owner: str,
        repo: str,
        tool_name: str | None = None,
        tool_guid: str | None = None,
        page: int | None = None,
        per_page: int | None = None,
        ref: str | None = None,
        pr: int | None = None,
        direction: str | None = None,
        before: str | None = None,
        after: str | None = None,
        sort: str | None = None,
        state: str | None = None,
        severity: str | None = None,
        assignees: str | None = None,
    ) -> str:
        """GET /repos/{owner}/{repo}/code-scanning/alerts - List code scanning alerts for a repository"""
        # HTTP GET /repos/{owner}/{repo}/code-scanning/alerts
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        if tool_name is not None:
            query_params["tool_name"] = str(tool_name)
        if tool_guid is not None:
            query_params["tool_guid"] = str(tool_guid)
        if page is not None:
            query_params["page"] = str(page)
        if per_page is not None:
            query_params["per_page"] = str(per_page)
        if ref is not None:
            query_params["ref"] = str(ref)
        if pr is not None:
            query_params["pr"] = str(pr)
        if direction is not None:
            query_params["direction"] = str(direction)
        if before is not None:
            query_params["before"] = str(before)
        if after is not None:
            query_params["after"] = str(after)
        if sort is not None:
            query_params["sort"] = str(sort)
        if state is not None:
            query_params["state"] = str(state)
        if severity is not None:
            query_params["severity"] = str(severity)
        if assignees is not None:
            query_params["assignees"] = str(assignees)
        try:
            return await backend.request(
                "GET",
                "/repos/{owner}/{repo}/code-scanning/alerts",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def code_scanning_get_alert(
        owner: str,
        repo: str,
        alert_number: int,
    ) -> str:
        """GET /repos/{owner}/{repo}/code-scanning/alerts/{alert_number} - Get a code scanning alert"""
        # HTTP GET /repos/{owner}/{repo}/code-scanning/alerts/{alert_number}
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        path_params["alert_number"] = str(alert_number)
        try:
            return await backend.request(
                "GET",
                "/repos/{owner}/{repo}/code-scanning/alerts/{alert_number}",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def repos_list_commits(
        owner: str,
        repo: str,
        sha: str | None = None,
        path: str | None = None,
        author: str | None = None,
        committer: str | None = None,
        since: str | None = None,
        until: str | None = None,
        per_page: int | None = None,
        page: int | None = None,
    ) -> str:
        """GET /repos/{owner}/{repo}/commits - List commits"""
        # HTTP GET /repos/{owner}/{repo}/commits
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        if sha is not None:
            query_params["sha"] = str(sha)
        if path is not None:
            query_params["path"] = str(path)
        if author is not None:
            query_params["author"] = str(author)
        if committer is not None:
            query_params["committer"] = str(committer)
        if since is not None:
            query_params["since"] = str(since)
        if until is not None:
            query_params["until"] = str(until)
        if per_page is not None:
            query_params["per_page"] = str(per_page)
        if page is not None:
            query_params["page"] = str(page)
        try:
            return await backend.request(
                "GET",
                "/repos/{owner}/{repo}/commits",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def repos_get_commit(
        owner: str,
        repo: str,
        ref: str,
        page: int | None = None,
        per_page: int | None = None,
    ) -> str:
        """GET /repos/{owner}/{repo}/commits/{ref} - Get a commit"""
        # HTTP GET /repos/{owner}/{repo}/commits/{ref}
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        if page is not None:
            query_params["page"] = str(page)
        if per_page is not None:
            query_params["per_page"] = str(per_page)
        path_params["ref"] = str(ref)
        try:
            return await backend.request(
                "GET",
                "/repos/{owner}/{repo}/commits/{ref}",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def repos_get_content(
        owner: str,
        repo: str,
        path: str,
        ref: str | None = None,
    ) -> str:
        """GET /repos/{owner}/{repo}/contents/{path} - Get repository content"""
        # HTTP GET /repos/{owner}/{repo}/contents/{path}
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        path_params["path"] = str(path)
        if ref is not None:
            query_params["ref"] = str(ref)
        try:
            return await backend.request(
                "GET",
                "/repos/{owner}/{repo}/contents/{path}",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def repos_create_or_update_file_contents(
        owner: str,
        repo: str,
        path: str,
        message: str,
        content: str,
        sha: str | None = None,
        branch: str | None = None,
        committer: dict | None = None,
        author: dict | None = None,
    ) -> str:
        """PUT /repos/{owner}/{repo}/contents/{path} - Create or update file contents"""
        # HTTP PUT /repos/{owner}/{repo}/contents/{path}
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        path_params["path"] = str(path)
        if message is not None:
            query_params["message"] = str(message)
        if content is not None:
            query_params["content"] = str(content)
        if sha is not None:
            query_params["sha"] = str(sha)
        if branch is not None:
            query_params["branch"] = str(branch)
        request_body = committer if isinstance(committer, dict) else {"data": committer}
        request_body = author if isinstance(author, dict) else {"data": author}
        try:
            return await backend.request(
                "PUT",
                "/repos/{owner}/{repo}/contents/{path}",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def repos_delete_file(
        owner: str,
        repo: str,
        path: str,
        message: str,
        sha: str,
        branch: str | None = None,
        committer: dict | None = None,
        author: dict | None = None,
    ) -> str:
        """DELETE /repos/{owner}/{repo}/contents/{path} - Delete a file"""
        # HTTP DELETE /repos/{owner}/{repo}/contents/{path}
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        path_params["path"] = str(path)
        if message is not None:
            query_params["message"] = str(message)
        if sha is not None:
            query_params["sha"] = str(sha)
        if branch is not None:
            query_params["branch"] = str(branch)
        request_body = committer if isinstance(committer, dict) else {"data": committer}
        request_body = author if isinstance(author, dict) else {"data": author}
        try:
            return await backend.request(
                "DELETE",
                "/repos/{owner}/{repo}/contents/{path}",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def dependabot_list_alerts_for_repo(
        owner: str,
        repo: str,
        state: str | None = None,
        severity: str | None = None,
        ecosystem: str | None = None,
        package: str | None = None,
        manifest: str | None = None,
        epss_percentage: str | None = None,
        has: dict | None = None,
        assignee: str | None = None,
        scope: str | None = None,
        sort: str | None = None,
        direction: str | None = None,
        before: str | None = None,
        after: str | None = None,
        per_page: int | None = None,
    ) -> str:
        """GET /repos/{owner}/{repo}/dependabot/alerts - List Dependabot alerts for a repository"""
        # HTTP GET /repos/{owner}/{repo}/dependabot/alerts
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        if state is not None:
            query_params["state"] = str(state)
        if severity is not None:
            query_params["severity"] = str(severity)
        if ecosystem is not None:
            query_params["ecosystem"] = str(ecosystem)
        if package is not None:
            query_params["package"] = str(package)
        if manifest is not None:
            query_params["manifest"] = str(manifest)
        if epss_percentage is not None:
            query_params["epss_percentage"] = str(epss_percentage)
        request_body = has if isinstance(has, dict) else {"data": has}
        if assignee is not None:
            query_params["assignee"] = str(assignee)
        if scope is not None:
            query_params["scope"] = str(scope)
        if sort is not None:
            query_params["sort"] = str(sort)
        if direction is not None:
            query_params["direction"] = str(direction)
        if before is not None:
            query_params["before"] = str(before)
        if after is not None:
            query_params["after"] = str(after)
        if per_page is not None:
            query_params["per_page"] = str(per_page)
        try:
            return await backend.request(
                "GET",
                "/repos/{owner}/{repo}/dependabot/alerts",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def dependabot_get_alert(
        owner: str,
        repo: str,
        alert_number: int,
    ) -> str:
        """GET /repos/{owner}/{repo}/dependabot/alerts/{alert_number} - Get a Dependabot alert"""
        # HTTP GET /repos/{owner}/{repo}/dependabot/alerts/{alert_number}
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        path_params["alert_number"] = str(alert_number)
        try:
            return await backend.request(
                "GET",
                "/repos/{owner}/{repo}/dependabot/alerts/{alert_number}",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def repos_create_fork(
        owner: str,
        repo: str,
        organization: str | None = None,
        name: str | None = None,
        default_branch_only: bool | None = None,
    ) -> str:
        """POST /repos/{owner}/{repo}/forks - Create a fork"""
        # HTTP POST /repos/{owner}/{repo}/forks
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        if organization is not None:
            query_params["organization"] = str(organization)
        if name is not None:
            query_params["name"] = str(name)
        if default_branch_only is not None:
            query_params["default_branch_only"] = str(default_branch_only)
        try:
            return await backend.request(
                "POST",
                "/repos/{owner}/{repo}/forks",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def git_create_ref(
        owner: str,
        repo: str,
        ref: str,
        sha: str,
    ) -> str:
        """POST /repos/{owner}/{repo}/git/refs - Create a reference"""
        # HTTP POST /repos/{owner}/{repo}/git/refs
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        if ref is not None:
            query_params["ref"] = str(ref)
        if sha is not None:
            query_params["sha"] = str(sha)
        try:
            return await backend.request(
                "POST",
                "/repos/{owner}/{repo}/git/refs",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def git_get_tag(
        owner: str,
        repo: str,
        tag_sha: str,
    ) -> str:
        """GET /repos/{owner}/{repo}/git/tags/{tag_sha} - Get a tag"""
        # HTTP GET /repos/{owner}/{repo}/git/tags/{tag_sha}
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        path_params["tag_sha"] = str(tag_sha)
        try:
            return await backend.request(
                "GET",
                "/repos/{owner}/{repo}/git/tags/{tag_sha}",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def git_get_tree(
        owner: str,
        repo: str,
        tree_sha: str,
        recursive: str | None = None,
    ) -> str:
        """GET /repos/{owner}/{repo}/git/trees/{tree_sha} - Get a tree"""
        # HTTP GET /repos/{owner}/{repo}/git/trees/{tree_sha}
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        path_params["tree_sha"] = str(tree_sha)
        if recursive is not None:
            query_params["recursive"] = str(recursive)
        try:
            return await backend.request(
                "GET",
                "/repos/{owner}/{repo}/git/trees/{tree_sha}",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def issues_list_for_repo(
        owner: str,
        repo: str,
        milestone: str | None = None,
        state: str | None = None,
        assignee: str | None = None,
        type: str | None = None,
        creator: str | None = None,
        mentioned: str | None = None,
        labels: str | None = None,
        sort: str | None = None,
        direction: str | None = None,
        since: str | None = None,
        per_page: int | None = None,
        page: int | None = None,
    ) -> str:
        """GET /repos/{owner}/{repo}/issues - List repository issues"""
        # HTTP GET /repos/{owner}/{repo}/issues
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        if milestone is not None:
            query_params["milestone"] = str(milestone)
        if state is not None:
            query_params["state"] = str(state)
        if assignee is not None:
            query_params["assignee"] = str(assignee)
        if type is not None:
            query_params["type"] = str(type)
        if creator is not None:
            query_params["creator"] = str(creator)
        if mentioned is not None:
            query_params["mentioned"] = str(mentioned)
        if labels is not None:
            query_params["labels"] = str(labels)
        if sort is not None:
            query_params["sort"] = str(sort)
        if direction is not None:
            query_params["direction"] = str(direction)
        if since is not None:
            query_params["since"] = str(since)
        if per_page is not None:
            query_params["per_page"] = str(per_page)
        if page is not None:
            query_params["page"] = str(page)
        try:
            return await backend.request(
                "GET",
                "/repos/{owner}/{repo}/issues",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def issues_create(
        owner: str,
        repo: str,
        title: dict,
        body: str | None = None,
        assignee: str | None = None,
        milestone: dict | None = None,
        labels: list | None = None,
        assignees: list | None = None,
        type: str | None = None,
    ) -> str:
        """POST /repos/{owner}/{repo}/issues - Create an issue"""
        # HTTP POST /repos/{owner}/{repo}/issues
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        request_body = title if isinstance(title, dict) else {"data": title}
        if body is not None:
            query_params["body"] = str(body)
        if assignee is not None:
            query_params["assignee"] = str(assignee)
        request_body = milestone if isinstance(milestone, dict) else {"data": milestone}
        if labels is not None:
            query_params["labels"] = str(labels)
        if assignees is not None:
            query_params["assignees"] = str(assignees)
        if type is not None:
            query_params["type"] = str(type)
        try:
            return await backend.request(
                "POST",
                "/repos/{owner}/{repo}/issues",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def issues_get(
        owner: str,
        repo: str,
        issue_number: int,
    ) -> str:
        """GET /repos/{owner}/{repo}/issues/{issue_number} - Get an issue"""
        # HTTP GET /repos/{owner}/{repo}/issues/{issue_number}
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        path_params["issue_number"] = str(issue_number)
        try:
            return await backend.request(
                "GET",
                "/repos/{owner}/{repo}/issues/{issue_number}",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def issues_update(
        owner: str,
        repo: str,
        issue_number: int,
        title: dict | None = None,
        body: str | None = None,
        assignee: str | None = None,
        state: str | None = None,
        state_reason: str | None = None,
        milestone: dict | None = None,
        labels: list | None = None,
        assignees: list | None = None,
        issue_field_values: list | None = None,
        type: str | None = None,
    ) -> str:
        """PATCH /repos/{owner}/{repo}/issues/{issue_number} - Update an issue"""
        # HTTP PATCH /repos/{owner}/{repo}/issues/{issue_number}
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        path_params["issue_number"] = str(issue_number)
        request_body = title if isinstance(title, dict) else {"data": title}
        if body is not None:
            query_params["body"] = str(body)
        if assignee is not None:
            query_params["assignee"] = str(assignee)
        if state is not None:
            query_params["state"] = str(state)
        if state_reason is not None:
            query_params["state_reason"] = str(state_reason)
        request_body = milestone if isinstance(milestone, dict) else {"data": milestone}
        if labels is not None:
            query_params["labels"] = str(labels)
        if assignees is not None:
            query_params["assignees"] = str(assignees)
        if issue_field_values is not None:
            query_params["issue_field_values"] = str(issue_field_values)
        if type is not None:
            query_params["type"] = str(type)
        try:
            return await backend.request(
                "PATCH",
                "/repos/{owner}/{repo}/issues/{issue_number}",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def issues_create_comment(
        owner: str,
        repo: str,
        issue_number: int,
        body: str,
    ) -> str:
        """POST /repos/{owner}/{repo}/issues/{issue_number}/comments - Create an issue comment"""
        # HTTP POST /repos/{owner}/{repo}/issues/{issue_number}/comments
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        path_params["issue_number"] = str(issue_number)
        if body is not None:
            query_params["body"] = str(body)
        try:
            return await backend.request(
                "POST",
                "/repos/{owner}/{repo}/issues/{issue_number}/comments",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def issues_add_sub_issue(
        owner: str,
        repo: str,
        issue_number: int,
        sub_issue_id: int,
        replace_parent: bool | None = None,
    ) -> str:
        """POST /repos/{owner}/{repo}/issues/{issue_number}/sub_issues - Add sub-issue"""
        # HTTP POST /repos/{owner}/{repo}/issues/{issue_number}/sub_issues
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        path_params["issue_number"] = str(issue_number)
        if sub_issue_id is not None:
            query_params["sub_issue_id"] = str(sub_issue_id)
        if replace_parent is not None:
            query_params["replace_parent"] = str(replace_parent)
        try:
            return await backend.request(
                "POST",
                "/repos/{owner}/{repo}/issues/{issue_number}/sub_issues",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def issues_list_labels_for_repo(
        owner: str,
        repo: str,
        per_page: int | None = None,
        page: int | None = None,
    ) -> str:
        """GET /repos/{owner}/{repo}/labels - List labels for a repository"""
        # HTTP GET /repos/{owner}/{repo}/labels
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        if per_page is not None:
            query_params["per_page"] = str(per_page)
        if page is not None:
            query_params["page"] = str(page)
        try:
            return await backend.request(
                "GET",
                "/repos/{owner}/{repo}/labels",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def issues_create_label(
        owner: str,
        repo: str,
        name: str,
        color: str | None = None,
        description: str | None = None,
    ) -> str:
        """POST /repos/{owner}/{repo}/labels - Create a label"""
        # HTTP POST /repos/{owner}/{repo}/labels
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        if name is not None:
            query_params["name"] = str(name)
        if color is not None:
            query_params["color"] = str(color)
        if description is not None:
            query_params["description"] = str(description)
        try:
            return await backend.request(
                "POST",
                "/repos/{owner}/{repo}/labels",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def issues_get_label(
        owner: str,
        repo: str,
        name: str,
    ) -> str:
        """GET /repos/{owner}/{repo}/labels/{name} - Get a label"""
        # HTTP GET /repos/{owner}/{repo}/labels/{name}
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        path_params["name"] = str(name)
        try:
            return await backend.request(
                "GET",
                "/repos/{owner}/{repo}/labels/{name}",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def pulls_list(
        owner: str,
        repo: str,
        state: str | None = None,
        head: str | None = None,
        base: str | None = None,
        sort: str | None = None,
        direction: str | None = None,
        per_page: int | None = None,
        page: int | None = None,
    ) -> str:
        """GET /repos/{owner}/{repo}/pulls - List pull requests"""
        # HTTP GET /repos/{owner}/{repo}/pulls
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        if state is not None:
            query_params["state"] = str(state)
        if head is not None:
            query_params["head"] = str(head)
        if base is not None:
            query_params["base"] = str(base)
        if sort is not None:
            query_params["sort"] = str(sort)
        if direction is not None:
            query_params["direction"] = str(direction)
        if per_page is not None:
            query_params["per_page"] = str(per_page)
        if page is not None:
            query_params["page"] = str(page)
        try:
            return await backend.request(
                "GET",
                "/repos/{owner}/{repo}/pulls",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def pulls_create(
        owner: str,
        repo: str,
        head: str,
        base: str,
        title: str | None = None,
        head_repo: str | None = None,
        body: str | None = None,
        maintainer_can_modify: bool | None = None,
        draft: bool | None = None,
        issue: int | None = None,
    ) -> str:
        """POST /repos/{owner}/{repo}/pulls - Create a pull request"""
        # HTTP POST /repos/{owner}/{repo}/pulls
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        if title is not None:
            query_params["title"] = str(title)
        if head is not None:
            query_params["head"] = str(head)
        if head_repo is not None:
            query_params["head_repo"] = str(head_repo)
        if base is not None:
            query_params["base"] = str(base)
        if body is not None:
            query_params["body"] = str(body)
        if maintainer_can_modify is not None:
            query_params["maintainer_can_modify"] = str(maintainer_can_modify)
        if draft is not None:
            query_params["draft"] = str(draft)
        if issue is not None:
            query_params["issue"] = str(issue)
        try:
            return await backend.request(
                "POST",
                "/repos/{owner}/{repo}/pulls",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def pulls_get(
        owner: str,
        repo: str,
        pull_number: int,
    ) -> str:
        """GET /repos/{owner}/{repo}/pulls/{pull_number} - Get a pull request"""
        # HTTP GET /repos/{owner}/{repo}/pulls/{pull_number}
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        path_params["pull_number"] = str(pull_number)
        try:
            return await backend.request(
                "GET",
                "/repos/{owner}/{repo}/pulls/{pull_number}",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def pulls_update(
        owner: str,
        repo: str,
        pull_number: int,
        title: str | None = None,
        body: str | None = None,
        state: str | None = None,
        base: str | None = None,
        maintainer_can_modify: bool | None = None,
    ) -> str:
        """PATCH /repos/{owner}/{repo}/pulls/{pull_number} - Update a pull request"""
        # HTTP PATCH /repos/{owner}/{repo}/pulls/{pull_number}
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        path_params["pull_number"] = str(pull_number)
        if title is not None:
            query_params["title"] = str(title)
        if body is not None:
            query_params["body"] = str(body)
        if state is not None:
            query_params["state"] = str(state)
        if base is not None:
            query_params["base"] = str(base)
        if maintainer_can_modify is not None:
            query_params["maintainer_can_modify"] = str(maintainer_can_modify)
        try:
            return await backend.request(
                "PATCH",
                "/repos/{owner}/{repo}/pulls/{pull_number}",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def pulls_create_review_comment(
        owner: str,
        repo: str,
        pull_number: int,
        body: str,
        commit_id: str,
        path: str,
        position: int | None = None,
        side: str | None = None,
        line: int | None = None,
        start_line: int | None = None,
        start_side: str | None = None,
        in_reply_to: int | None = None,
        subject_type: str | None = None,
    ) -> str:
        """POST /repos/{owner}/{repo}/pulls/{pull_number}/comments - Create a review comment for a pull request"""
        # HTTP POST /repos/{owner}/{repo}/pulls/{pull_number}/comments
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        path_params["pull_number"] = str(pull_number)
        if body is not None:
            query_params["body"] = str(body)
        if commit_id is not None:
            query_params["commit_id"] = str(commit_id)
        if path is not None:
            query_params["path"] = str(path)
        if position is not None:
            query_params["position"] = str(position)
        if side is not None:
            query_params["side"] = str(side)
        if line is not None:
            query_params["line"] = str(line)
        if start_line is not None:
            query_params["start_line"] = str(start_line)
        if start_side is not None:
            query_params["start_side"] = str(start_side)
        if in_reply_to is not None:
            query_params["in_reply_to"] = str(in_reply_to)
        if subject_type is not None:
            query_params["subject_type"] = str(subject_type)
        try:
            return await backend.request(
                "POST",
                "/repos/{owner}/{repo}/pulls/{pull_number}/comments",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def pulls_create_reply_for_review_comment(
        owner: str,
        repo: str,
        pull_number: int,
        comment_id: int,
        body: str,
    ) -> str:
        """POST /repos/{owner}/{repo}/pulls/{pull_number}/comments/{comment_id}/replies - Create a reply for a review comment"""
        # HTTP POST /repos/{owner}/{repo}/pulls/{pull_number}/comments/{comment_id}/replies
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        path_params["pull_number"] = str(pull_number)
        path_params["comment_id"] = str(comment_id)
        if body is not None:
            query_params["body"] = str(body)
        try:
            return await backend.request(
                "POST",
                "/repos/{owner}/{repo}/pulls/{pull_number}/comments/{comment_id}/replies",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def pulls_merge(
        owner: str,
        repo: str,
        pull_number: int,
        commit_title: str | None = None,
        commit_message: str | None = None,
        sha: str | None = None,
        merge_method: str | None = None,
    ) -> str:
        """PUT /repos/{owner}/{repo}/pulls/{pull_number}/merge - Merge a pull request"""
        # HTTP PUT /repos/{owner}/{repo}/pulls/{pull_number}/merge
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        path_params["pull_number"] = str(pull_number)
        if commit_title is not None:
            query_params["commit_title"] = str(commit_title)
        if commit_message is not None:
            query_params["commit_message"] = str(commit_message)
        if sha is not None:
            query_params["sha"] = str(sha)
        if merge_method is not None:
            query_params["merge_method"] = str(merge_method)
        try:
            return await backend.request(
                "PUT",
                "/repos/{owner}/{repo}/pulls/{pull_number}/merge",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def pulls_submit_review(
        owner: str,
        repo: str,
        pull_number: int,
        review_id: int,
        event: str,
        body: str | None = None,
    ) -> str:
        """POST /repos/{owner}/{repo}/pulls/{pull_number}/reviews/{review_id}/events - Submit a review for a pull request"""
        # HTTP POST /repos/{owner}/{repo}/pulls/{pull_number}/reviews/{review_id}/events
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        path_params["pull_number"] = str(pull_number)
        path_params["review_id"] = str(review_id)
        if body is not None:
            query_params["body"] = str(body)
        if event is not None:
            query_params["event"] = str(event)
        try:
            return await backend.request(
                "POST",
                "/repos/{owner}/{repo}/pulls/{pull_number}/reviews/{review_id}/events",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def pulls_update_branch(
        owner: str,
        repo: str,
        pull_number: int,
        expected_head_sha: str | None = None,
    ) -> str:
        """PUT /repos/{owner}/{repo}/pulls/{pull_number}/update-branch - Update a pull request branch"""
        # HTTP PUT /repos/{owner}/{repo}/pulls/{pull_number}/update-branch
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        path_params["pull_number"] = str(pull_number)
        if expected_head_sha is not None:
            query_params["expected_head_sha"] = str(expected_head_sha)
        try:
            return await backend.request(
                "PUT",
                "/repos/{owner}/{repo}/pulls/{pull_number}/update-branch",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def repos_list_releases(
        owner: str,
        repo: str,
        per_page: int | None = None,
        page: int | None = None,
    ) -> str:
        """GET /repos/{owner}/{repo}/releases - List releases"""
        # HTTP GET /repos/{owner}/{repo}/releases
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        if per_page is not None:
            query_params["per_page"] = str(per_page)
        if page is not None:
            query_params["page"] = str(page)
        try:
            return await backend.request(
                "GET",
                "/repos/{owner}/{repo}/releases",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def repos_get_latest_release(
        owner: str,
        repo: str,
    ) -> str:
        """GET /repos/{owner}/{repo}/releases/latest - Get the latest release"""
        # HTTP GET /repos/{owner}/{repo}/releases/latest
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        try:
            return await backend.request(
                "GET",
                "/repos/{owner}/{repo}/releases/latest",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def repos_get_release_by_tag(
        owner: str,
        repo: str,
        tag: str,
    ) -> str:
        """GET /repos/{owner}/{repo}/releases/tags/{tag} - Get a release by tag name"""
        # HTTP GET /repos/{owner}/{repo}/releases/tags/{tag}
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        path_params["tag"] = str(tag)
        try:
            return await backend.request(
                "GET",
                "/repos/{owner}/{repo}/releases/tags/{tag}",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def secret_scanning_list_alerts_for_repo(
        owner: str,
        repo: str,
        state: str | None = None,
        secret_type: str | None = None,
        resolution: str | None = None,
        assignee: str | None = None,
        sort: str | None = None,
        direction: str | None = None,
        page: int | None = None,
        per_page: int | None = None,
        before: str | None = None,
        after: str | None = None,
        validity: str | None = None,
        is_publicly_leaked: bool | None = None,
        is_multi_repo: bool | None = None,
        hide_secret: bool | None = None,
    ) -> str:
        """GET /repos/{owner}/{repo}/secret-scanning/alerts - List secret scanning alerts for a repository"""
        # HTTP GET /repos/{owner}/{repo}/secret-scanning/alerts
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        if state is not None:
            query_params["state"] = str(state)
        if secret_type is not None:
            query_params["secret_type"] = str(secret_type)
        if resolution is not None:
            query_params["resolution"] = str(resolution)
        if assignee is not None:
            query_params["assignee"] = str(assignee)
        if sort is not None:
            query_params["sort"] = str(sort)
        if direction is not None:
            query_params["direction"] = str(direction)
        if page is not None:
            query_params["page"] = str(page)
        if per_page is not None:
            query_params["per_page"] = str(per_page)
        if before is not None:
            query_params["before"] = str(before)
        if after is not None:
            query_params["after"] = str(after)
        if validity is not None:
            query_params["validity"] = str(validity)
        if is_publicly_leaked is not None:
            query_params["is_publicly_leaked"] = str(is_publicly_leaked)
        if is_multi_repo is not None:
            query_params["is_multi_repo"] = str(is_multi_repo)
        if hide_secret is not None:
            query_params["hide_secret"] = str(hide_secret)
        try:
            return await backend.request(
                "GET",
                "/repos/{owner}/{repo}/secret-scanning/alerts",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def secret_scanning_get_alert(
        owner: str,
        repo: str,
        alert_number: int,
        hide_secret: bool | None = None,
    ) -> str:
        """GET /repos/{owner}/{repo}/secret-scanning/alerts/{alert_number} - Get a secret scanning alert"""
        # HTTP GET /repos/{owner}/{repo}/secret-scanning/alerts/{alert_number}
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        path_params["alert_number"] = str(alert_number)
        if hide_secret is not None:
            query_params["hide_secret"] = str(hide_secret)
        try:
            return await backend.request(
                "GET",
                "/repos/{owner}/{repo}/secret-scanning/alerts/{alert_number}",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def security_advisories_list_repository_advisories(
        owner: str,
        repo: str,
        direction: str | None = None,
        sort: str | None = None,
        before: str | None = None,
        after: str | None = None,
        per_page: int | None = None,
        state: str | None = None,
    ) -> str:
        """GET /repos/{owner}/{repo}/security-advisories - List repository security advisories"""
        # HTTP GET /repos/{owner}/{repo}/security-advisories
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        if direction is not None:
            query_params["direction"] = str(direction)
        if sort is not None:
            query_params["sort"] = str(sort)
        if before is not None:
            query_params["before"] = str(before)
        if after is not None:
            query_params["after"] = str(after)
        if per_page is not None:
            query_params["per_page"] = str(per_page)
        if state is not None:
            query_params["state"] = str(state)
        try:
            return await backend.request(
                "GET",
                "/repos/{owner}/{repo}/security-advisories",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def activity_set_repo_subscription(
        owner: str,
        repo: str,
        subscribed: bool | None = None,
        ignored: bool | None = None,
    ) -> str:
        """PUT /repos/{owner}/{repo}/subscription - Set a repository subscription"""
        # HTTP PUT /repos/{owner}/{repo}/subscription
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        if subscribed is not None:
            query_params["subscribed"] = str(subscribed)
        if ignored is not None:
            query_params["ignored"] = str(ignored)
        try:
            return await backend.request(
                "PUT",
                "/repos/{owner}/{repo}/subscription",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def repos_list_tags(
        owner: str,
        repo: str,
        per_page: int | None = None,
        page: int | None = None,
    ) -> str:
        """GET /repos/{owner}/{repo}/tags - List repository tags"""
        # HTTP GET /repos/{owner}/{repo}/tags
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        if per_page is not None:
            query_params["per_page"] = str(per_page)
        if page is not None:
            query_params["page"] = str(page)
        try:
            return await backend.request(
                "GET",
                "/repos/{owner}/{repo}/tags",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def search_code(
        q: str,
        sort: str | None = None,
        order: str | None = None,
        per_page: int | None = None,
        page: int | None = None,
    ) -> str:
        """GET /search/code - Search code"""
        # HTTP GET /search/code
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        if q is not None:
            query_params["q"] = str(q)
        if sort is not None:
            query_params["sort"] = str(sort)
        if order is not None:
            query_params["order"] = str(order)
        if per_page is not None:
            query_params["per_page"] = str(per_page)
        if page is not None:
            query_params["page"] = str(page)
        try:
            return await backend.request(
                "GET",
                "/search/code",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def search_issues_and_pull_requests(
        q: str,
        sort: str | None = None,
        order: str | None = None,
        per_page: int | None = None,
        page: int | None = None,
        advanced_search: str | None = None,
    ) -> str:
        """GET /search/issues - Search issues and pull requests"""
        # HTTP GET /search/issues
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        if q is not None:
            query_params["q"] = str(q)
        if sort is not None:
            query_params["sort"] = str(sort)
        if order is not None:
            query_params["order"] = str(order)
        if per_page is not None:
            query_params["per_page"] = str(per_page)
        if page is not None:
            query_params["page"] = str(page)
        if advanced_search is not None:
            query_params["advanced_search"] = str(advanced_search)
        try:
            return await backend.request(
                "GET",
                "/search/issues",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def search_repos(
        q: str,
        sort: str | None = None,
        order: str | None = None,
        per_page: int | None = None,
        page: int | None = None,
    ) -> str:
        """GET /search/repositories - Search repositories"""
        # HTTP GET /search/repositories
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        if q is not None:
            query_params["q"] = str(q)
        if sort is not None:
            query_params["sort"] = str(sort)
        if order is not None:
            query_params["order"] = str(order)
        if per_page is not None:
            query_params["per_page"] = str(per_page)
        if page is not None:
            query_params["page"] = str(page)
        try:
            return await backend.request(
                "GET",
                "/search/repositories",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def search_users(
        q: str,
        sort: str | None = None,
        order: str | None = None,
        per_page: int | None = None,
        page: int | None = None,
    ) -> str:
        """GET /search/users - Search users"""
        # HTTP GET /search/users
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        if q is not None:
            query_params["q"] = str(q)
        if sort is not None:
            query_params["sort"] = str(sort)
        if order is not None:
            query_params["order"] = str(order)
        if per_page is not None:
            query_params["per_page"] = str(per_page)
        if page is not None:
            query_params["page"] = str(page)
        try:
            return await backend.request(
                "GET",
                "/search/users",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def users_get_authenticated(
    ) -> str:
        """GET /user - Get the authenticated user"""
        # HTTP GET /user
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        try:
            return await backend.request(
                "GET",
                "/user",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def repos_create_for_authenticated_user(
        name: str,
        description: str | None = None,
        homepage: str | None = None,
        private: bool | None = None,
        has_issues: bool | None = None,
        has_projects: bool | None = None,
        has_wiki: bool | None = None,
        has_discussions: bool | None = None,
        team_id: int | None = None,
        auto_init: bool | None = None,
        gitignore_template: str | None = None,
        license_template: str | None = None,
        allow_squash_merge: bool | None = None,
        allow_merge_commit: bool | None = None,
        allow_rebase_merge: bool | None = None,
        allow_auto_merge: bool | None = None,
        delete_branch_on_merge: bool | None = None,
        squash_merge_commit_title: str | None = None,
        squash_merge_commit_message: str | None = None,
        merge_commit_title: str | None = None,
        merge_commit_message: str | None = None,
        has_downloads: bool | None = None,
        is_template: bool | None = None,
    ) -> str:
        """POST /user/repos - Create a repository for the authenticated user"""
        # HTTP POST /user/repos
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        if name is not None:
            query_params["name"] = str(name)
        if description is not None:
            query_params["description"] = str(description)
        if homepage is not None:
            query_params["homepage"] = str(homepage)
        if private is not None:
            query_params["private"] = str(private)
        if has_issues is not None:
            query_params["has_issues"] = str(has_issues)
        if has_projects is not None:
            query_params["has_projects"] = str(has_projects)
        if has_wiki is not None:
            query_params["has_wiki"] = str(has_wiki)
        if has_discussions is not None:
            query_params["has_discussions"] = str(has_discussions)
        if team_id is not None:
            query_params["team_id"] = str(team_id)
        if auto_init is not None:
            query_params["auto_init"] = str(auto_init)
        if gitignore_template is not None:
            query_params["gitignore_template"] = str(gitignore_template)
        if license_template is not None:
            query_params["license_template"] = str(license_template)
        if allow_squash_merge is not None:
            query_params["allow_squash_merge"] = str(allow_squash_merge)
        if allow_merge_commit is not None:
            query_params["allow_merge_commit"] = str(allow_merge_commit)
        if allow_rebase_merge is not None:
            query_params["allow_rebase_merge"] = str(allow_rebase_merge)
        if allow_auto_merge is not None:
            query_params["allow_auto_merge"] = str(allow_auto_merge)
        if delete_branch_on_merge is not None:
            query_params["delete_branch_on_merge"] = str(delete_branch_on_merge)
        if squash_merge_commit_title is not None:
            query_params["squash_merge_commit_title"] = str(squash_merge_commit_title)
        if squash_merge_commit_message is not None:
            query_params["squash_merge_commit_message"] = str(squash_merge_commit_message)
        if merge_commit_title is not None:
            query_params["merge_commit_title"] = str(merge_commit_title)
        if merge_commit_message is not None:
            query_params["merge_commit_message"] = str(merge_commit_message)
        if has_downloads is not None:
            query_params["has_downloads"] = str(has_downloads)
        if is_template is not None:
            query_params["is_template"] = str(is_template)
        try:
            return await backend.request(
                "POST",
                "/user/repos",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def activity_list_repos_starred_by_authenticated_user(
        sort: str | None = None,
        direction: str | None = None,
        per_page: int | None = None,
        page: int | None = None,
    ) -> str:
        """GET /user/starred - List repositories starred by the authenticated user"""
        # HTTP GET /user/starred
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        if sort is not None:
            query_params["sort"] = str(sort)
        if direction is not None:
            query_params["direction"] = str(direction)
        if per_page is not None:
            query_params["per_page"] = str(per_page)
        if page is not None:
            query_params["page"] = str(page)
        try:
            return await backend.request(
                "GET",
                "/user/starred",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def activity_star_repo_for_authenticated_user(
        owner: str,
        repo: str,
    ) -> str:
        """PUT /user/starred/{owner}/{repo} - Star a repository for the authenticated user"""
        # HTTP PUT /user/starred/{owner}/{repo}
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        try:
            return await backend.request(
                "PUT",
                "/user/starred/{owner}/{repo}",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

    @server.tool()
    async def activity_unstar_repo_for_authenticated_user(
        owner: str,
        repo: str,
    ) -> str:
        """DELETE /user/starred/{owner}/{repo} - Unstar a repository for the authenticated user"""
        # HTTP DELETE /user/starred/{owner}/{repo}
        path_params: dict[str, str] = {}
        query_params: dict[str, str] = {}
        request_body: dict | None = None
        path_params["owner"] = str(owner)
        path_params["repo"] = str(repo)
        try:
            return await backend.request(
                "DELETE",
                "/user/starred/{owner}/{repo}",
                params=query_params or None,
                body=request_body,
                path_params=path_params or None,
            )
        except BackendError as exc:
            return json.dumps(exc.to_dict(), indent=2)

