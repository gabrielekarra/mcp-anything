"""Tests for CONTRACT.md structural items (C-01..C-08, C-17..C-21, C-27..C-28).

These run without a live server; they check generated file structure and
tool shape against the contract checklist.
"""

import json
from pathlib import Path

import pytest

from mcp_anything.emit.base import EmitPhase
from mcp_anything.models.design import (
    ComposedTool,
    ParameterSpec,
    ServerDesign,
    ToolGroup,
    ToolImpl,
    ToolSpec,
)
from mcp_anything.models.validation import ConformanceReport


# Minimal EmitPhase subclass for direct contract checking
class _PhaseUnderTest(EmitPhase):
    name = "_test"
    backend_target = "fastmcp"

    def execute(self, ctx): pass


_phase = _PhaseUnderTest()


def _make_design(**kwargs) -> ServerDesign:
    defaults = dict(
        server_name="test",
        tools=[
            ToolSpec(
                name="list_tasks",
                description="Returns all tasks assigned to a user across projects.",
                parameters=[
                    ParameterSpec(name="user_id", type="string", required=True),
                    ParameterSpec(name="verbose", type="boolean", required=False),
                ],
            )
        ],
        tool_groups=[],
        composed_tools=[],
        discovery_endpoint=True,
        enable_telemetry=True,
    )
    defaults.update(kwargs)
    return ServerDesign(**defaults)


def _check(checks, id_: str) -> bool | None:
    for c in checks:
        if c.id == id_:
            return c.passed
    return None


# ── C-04 ──────────────────────────────────────────────────────────────────────

def test_c04_tool_has_name_description_params():
    design = _make_design()
    checks = _phase._check_tool_shapes(design)
    assert _check(checks, "C-04") is True


def test_c04_fails_empty_name():
    design = _make_design(tools=[
        ToolSpec(name="", description="Does something.", parameters=[])
    ])
    checks = _phase._check_tool_shapes(design)
    assert _check(checks, "C-04") is False


# ── C-05 ──────────────────────────────────────────────────────────────────────

def test_c05_agent_consumer_voice():
    design = _make_design()
    checks = _phase._check_tool_shapes(design)
    assert _check(checks, "C-05") is True


def test_c05_fails_wraps_prefix():
    design = _make_design(tools=[
        ToolSpec(
            name="list_tasks",
            description="Wraps the GET /tasks endpoint to return tasks.",
        )
    ])
    checks = _phase._check_tool_shapes(design)
    assert _check(checks, "C-05") is False


def test_c05_fails_short_description():
    design = _make_design(tools=[
        ToolSpec(name="list_tasks", description="List tasks")
    ])
    checks = _phase._check_tool_shapes(design)
    assert _check(checks, "C-05") is False


# ── C-06 ──────────────────────────────────────────────────────────────────────

def test_c06_passes_with_groups():
    design = _make_design(
        tool_groups=[ToolGroup(name="manage_task", operations=["create","read","update","delete","list"])]
    )
    checks = _phase._check_tool_shapes(design)
    assert _check(checks, "C-06") is True


def test_c06_warns_many_tools_no_groups():
    tools = [
        ToolSpec(name=f"tool_{i}", description="Returns something useful for the agent.", parameters=[])
        for i in range(7)
    ]
    design = _make_design(tools=tools, tool_groups=[])
    checks = _phase._check_tool_shapes(design)
    assert _check(checks, "C-06") is False


# ── C-07 ──────────────────────────────────────────────────────────────────────

def test_c07_passes_when_no_groups():
    design = _make_design(tool_groups=[])
    checks = _phase._check_tool_shapes(design)
    assert _check(checks, "C-07") is True


def test_c07_fails_group_tool_missing_operation():
    design = _make_design(
        tools=[
            ToolSpec(
                name="manage_task",
                description="Creates, updates, deletes, and lists tasks.",
                parameters=[
                    ParameterSpec(name="project_id", type="string", required=True)
                    # missing 'operation' param
                ],
            )
        ],
        tool_groups=[ToolGroup(name="manage_task", operations=["create","update","delete","list"])],
    )
    checks = _phase._check_tool_shapes(design)
    assert _check(checks, "C-07") is False


def test_c07_passes_group_tool_with_operation():
    design = _make_design(
        tools=[
            ToolSpec(
                name="manage_task",
                description="Creates, updates, deletes, and lists tasks in a project.",
                parameters=[
                    ParameterSpec(name="operation", type="string", required=True,
                                  description="One of: create, update, delete, list"),
                    ParameterSpec(name="project_id", type="string", required=True),
                ],
            )
        ],
        tool_groups=[ToolGroup(name="manage_task", operations=["create","update","delete","list"])],
    )
    checks = _phase._check_tool_shapes(design)
    assert _check(checks, "C-07") is True


# ── C-17 infrastructure ───────────────────────────────────────────────────────

def test_c17_dockerfile_present(tmp_path):
    (tmp_path / "Dockerfile").write_text("FROM python:3.12-slim\n")
    checks = _phase._check_infrastructure(tmp_path)
    assert _check(checks, "C-17") is True


def test_c17_dockerfile_missing(tmp_path):
    checks = _phase._check_infrastructure(tmp_path)
    assert _check(checks, "C-17") is False


# ── C-21 / C-23: checked by ValidationHarnessPhase._collect_contract_checks ──
# C-21 and C-23 are emitted by skill_bundle (Phase 4), after the emit phase,
# so they are checked in ValidationHarnessPhase, not _check_infrastructure.

from mcp_anything.pipeline.validation_harness import ValidationHarnessPhase

_harness = ValidationHarnessPhase()


class _FakeManifest:
    contract_check_results = None


class _FakeCtx:
    manifest = _FakeManifest()


def test_c21_skill_md_present(tmp_path):
    (tmp_path / "SKILL.md").write_text("# Test\n")
    checks = _harness._collect_contract_checks(_FakeCtx(), tmp_path)
    assert _check(checks, "C-21") is True


def test_c21_skill_md_missing(tmp_path):
    checks = _harness._collect_contract_checks(_FakeCtx(), tmp_path)
    assert _check(checks, "C-21") is False


# ── C-23 quick queries ────────────────────────────────────────────────────────

def test_c23_quick_queries_present(tmp_path):
    (tmp_path / "quick_queries.json").write_text("[]")
    checks = _harness._collect_contract_checks(_FakeCtx(), tmp_path)
    assert _check(checks, "C-23") is True


def test_c23_quick_queries_missing(tmp_path):
    checks = _harness._collect_contract_checks(_FakeCtx(), tmp_path)
    assert _check(checks, "C-23") is False
