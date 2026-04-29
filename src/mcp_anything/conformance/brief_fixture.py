"""Synthetic reference domain brief used as the canonical conformance input.

This brief describes a generic task-management API (projects, tasks, members, comments).
It is intentionally simple and stable — do not change without bumping the fixture version.
The fixture version gates which pre-recorded phase outputs are valid.
"""

FIXTURE_VERSION = "1.0.0"

# The canonical reference brief. Used by:
#   - tests/test_conformance_*.py
#   - mcp-anything validate --conformance-ref
REFERENCE_BRIEF: dict = {
    "server_name": "task-manager",
    "domain_description": (
        "A task-management platform where teams create projects, assign tasks, "
        "track progress, and collaborate via comments."
    ),
    "use_cases": [
        "List all open tasks assigned to a given user across all projects",
        "Create a new task inside a project, assigning it to a member",
        "Update the status of a task (open → in_progress → done → archived)",
        "Add a comment to a task and notify the assignee",
        "Get a full project summary: name, task counts by status, active members",
        "Bulk-close all tasks in a project that have been open for more than N days",
        "Reassign all tasks from one member to another when a member leaves",
    ],
    "glossary": {
        "Project": "A named container for tasks belonging to a team",
        "Task": "A unit of work within a project; has a status, assignee, and due date",
        "Member": "A user who belongs to one or more projects",
        "Comment": "A threaded text note attached to a task",
        "Status": "Lifecycle state of a task: open, in_progress, done, archived",
    },
    "data_source_path": "",  # populated at test time with the OpenAPI fixture path
    "data_source_kind": "openapi",
    "auth_method": "bearer",
    "backend_target": "fastmcp",
    "eval_threshold": 0.80,
}

# Minimal OpenAPI 3.0 spec matching the reference brief.
# Stored inline so tests never need filesystem access.
REFERENCE_OPENAPI_SPEC: dict = {
    "openapi": "3.0.0",
    "info": {"title": "Task Manager API", "version": "1.0.0"},
    "paths": {
        "/projects": {
            "get": {"operationId": "list_projects", "summary": "List all projects", "responses": {"200": {"description": "OK"}}},
            "post": {"operationId": "create_project", "summary": "Create a project", "responses": {"201": {"description": "Created"}}},
        },
        "/projects/{project_id}": {
            "get": {"operationId": "get_project", "summary": "Get project details", "responses": {"200": {"description": "OK"}}},
            "put": {"operationId": "update_project", "summary": "Update a project", "responses": {"200": {"description": "OK"}}},
            "delete": {"operationId": "delete_project", "summary": "Delete a project", "responses": {"204": {"description": "No content"}}},
        },
        "/projects/{project_id}/tasks": {
            "get": {"operationId": "list_tasks", "summary": "List tasks in a project", "responses": {"200": {"description": "OK"}}},
            "post": {"operationId": "create_task", "summary": "Create a task", "responses": {"201": {"description": "Created"}}},
        },
        "/projects/{project_id}/tasks/{task_id}": {
            "get": {"operationId": "get_task", "summary": "Get task details", "responses": {"200": {"description": "OK"}}},
            "put": {"operationId": "update_task", "summary": "Update a task", "responses": {"200": {"description": "OK"}}},
            "delete": {"operationId": "delete_task", "summary": "Delete a task", "responses": {"204": {"description": "No content"}}},
        },
        "/projects/{project_id}/tasks/{task_id}/comments": {
            "get": {"operationId": "list_comments", "summary": "List comments on a task", "responses": {"200": {"description": "OK"}}},
            "post": {"operationId": "create_comment", "summary": "Add a comment to a task", "responses": {"201": {"description": "Created"}}},
        },
        "/projects/{project_id}/members": {
            "get": {"operationId": "list_members", "summary": "List project members", "responses": {"200": {"description": "OK"}}},
            "post": {"operationId": "add_member", "summary": "Add a member to a project", "responses": {"201": {"description": "Created"}}},
            "delete": {"operationId": "remove_member", "summary": "Remove a member from a project", "responses": {"204": {"description": "No content"}}},
        },
    },
}
