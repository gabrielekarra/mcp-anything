"""Tests for Phase 4: SkillBundlePhase."""

import asyncio
import json
from pathlib import Path

import pytest

from mcp_anything.config import CLIOptions
from mcp_anything.models.design import ComposedTool, ServerDesign, ToolGroup, ToolImpl, ToolSpec
from mcp_anything.models.domain import DomainModel, UseCase
from mcp_anything.models.manifest import GenerationManifest
from mcp_anything.pipeline.context import PipelineContext
from mcp_anything.pipeline.skill_bundle import (
    SkillBundlePhase,
    _SKILL_BUNDLE_SECTIONS,
    _best_matching_tools,
    _build_anti_patterns,
    _build_gotchas,
    _build_quick_queries,
    _build_recipe_workflows,
    _build_skill_fallback,
)
from rich.console import Console


@pytest.fixture
def domain_model() -> DomainModel:
    return DomainModel(
        server_name="task-manager",
        domain_description="Manages tasks and projects.",
        use_cases=[
            UseCase(id="uc-01", description="List all open tasks", actor="agent", expected_outcome="Task list"),
            UseCase(id="uc-02", description="Create a new task", actor="agent", expected_outcome="Task object"),
        ],
        domain_entities=["Task", "Project"],
        approved=True,
    )


@pytest.fixture
def design() -> ServerDesign:
    from mcp_anything.models.analysis import ParameterSpec
    return ServerDesign(
        server_name="task-manager",
        server_description="Manages tasks and projects for teams.",
        tools=[
            ToolSpec(name="list_tasks", description="Returns open tasks for a project."),
            ToolSpec(name="create_task", description="Creates a new task in a project."),
        ],
        composed_tools=[
            ComposedTool(
                name="complete_workflow",
                description="Creates a task and immediately assigns it.",
                steps=["create_task", "update_task"],
                trigger_pattern="When the user wants to create and assign in one step.",
            )
        ],
    )


@pytest.fixture
def ctx(tmp_path, domain_model, design) -> PipelineContext:
    opts = CLIOptions(
        codebase_path=tmp_path,
        output_dir=tmp_path / "output",
        name="task-manager",
        no_llm=True,
    )
    manifest = GenerationManifest(
        pipeline_mode="domain",
        codebase_path=str(tmp_path),
        output_dir=str(tmp_path / "output"),
        server_name="task-manager",
        domain_model=domain_model.model_dump(),
        tool_spec=design.model_dump(),
        skill_bundle=None,
    )
    # Satisfy skill_bundle phase precondition: skill_bundle must be set
    # We'll set it after domain+tool pass (tested separately); here just allow it
    manifest.skill_bundle = {}  # empty but truthy placeholder for precondition
    # Actually validation_harness requires skill_bundle truthy but skill_bundle phase
    # itself doesn't; let's clear it to test the phase itself
    manifest.skill_bundle = None
    return PipelineContext(opts, manifest, Console(quiet=True))


def test_skill_md_all_sections(domain_model, design):
    content = _build_skill_fallback(domain_model, design)
    for section in _SKILL_BUNDLE_SECTIONS:
        assert section in content, f"Missing section: {section}"


def test_quick_queries_one_per_use_case(domain_model, design):
    qq = _build_quick_queries(domain_model, design)
    assert len(qq) == len(domain_model.use_cases)
    for entry in qq:
        assert "id" in entry
        assert "brief_item_id" in entry
        assert "prompt" in entry
        assert "expected_tool" in entry
        assert "notes" in entry


def test_quick_queries_expected_tool_is_valid(domain_model, design):
    qq = _build_quick_queries(domain_model, design)
    tool_names = {t.name for t in design.tools}
    for entry in qq:
        assert entry["expected_tool"] in tool_names


def test_phase_writes_skill_md(ctx, tmp_path):
    # Precondition: need domain_model and tool_spec set (ctx fixture has them)
    phase = SkillBundlePhase()
    asyncio.run(phase.execute(ctx))

    skill_path = tmp_path / "output" / "SKILL.md"
    assert skill_path.exists()
    content = skill_path.read_text()
    for section in _SKILL_BUNDLE_SECTIONS:
        assert section in content


def test_phase_writes_quick_queries(ctx, tmp_path):
    phase = SkillBundlePhase()
    asyncio.run(phase.execute(ctx))

    qq_path = tmp_path / "output" / "quick_queries.json"
    assert qq_path.exists()
    data = json.loads(qq_path.read_text())
    assert isinstance(data, list)
    assert len(data) == 2  # one per use-case


def test_phase_requires_domain_and_tool_spec():
    opts = CLIOptions(codebase_path=Path("."), no_llm=True)
    manifest = GenerationManifest(
        pipeline_mode="domain", codebase_path=".", output_dir=".", server_name="test"
    )
    ctx = PipelineContext(opts, manifest, Console(quiet=True))
    phase = SkillBundlePhase()
    errors = phase.validate_preconditions(ctx)
    assert len(errors) == 2  # no domain_model, no tool_spec


# ---------------------------------------------------------------------------
# Bug: the --no-llm fallback always picked "the first tool" for a recipe/quick-query
# regardless of relevance, and always mentioned HTTP status codes / manage_* CRUD
# tools even when the server has neither. Deterministic output must still be
# truthful: no match should mean no suggestion, not a wrong one.
# ---------------------------------------------------------------------------

def _unrelated_design() -> ServerDesign:
    from mcp_anything.models.analysis import ParameterSpec
    return ServerDesign(
        server_name="weather",
        server_description="Weather lookups.",
        tools=[
            ToolSpec(name="get_forecast", description="Returns the 5-day forecast for a city."),
            ToolSpec(name="get_alerts", description="Returns active severe weather alerts."),
        ],
    )


def _unrelated_domain_model() -> DomainModel:
    return DomainModel(
        server_name="weather",
        domain_description="Weather data.",
        use_cases=[
            UseCase(
                id="uc-01",
                description="Reconcile quarterly invoices against ledger entries",
                actor="agent",
                expected_outcome="Reconciled ledger",
            ),
        ],
        approved=True,
    )


def test_best_matching_tools_empty_when_no_overlap():
    design = _unrelated_design()
    assert _best_matching_tools("Reconcile quarterly invoices", design.tools) == []


def test_best_matching_tools_uses_description_not_just_name():
    design = _unrelated_design()
    # "severe" and "alerts" only appear in get_alerts' description, not its name.
    matches = _best_matching_tools("Warn me about severe conditions with alerts", design.tools)
    assert [t.name for t in matches] == ["get_alerts"]


def test_quick_queries_expected_tool_is_null_when_no_match():
    qq = _build_quick_queries(_unrelated_domain_model(), _unrelated_design())
    assert len(qq) == 1
    assert qq[0]["expected_tool"] is None


def test_recipe_workflows_omits_use_case_with_no_matching_tool():
    body = _build_recipe_workflows(_unrelated_domain_model(), _unrelated_design())
    assert "get_forecast" not in body
    assert "get_alerts" not in body


def test_recipe_workflows_includes_use_case_with_matching_tool(domain_model, design):
    body = _build_recipe_workflows(domain_model, design)
    assert "list_tasks" in body
    assert "create_task" in body


def test_gotchas_omit_http_status_line_without_http_tools():
    body = _build_gotchas(_unrelated_design())
    assert "HTTP" not in body
    assert "status code" not in body


def test_gotchas_include_http_status_line_with_http_tools():
    design = ServerDesign(
        server_name="api",
        tools=[
            ToolSpec(
                name="list_items",
                description="List items.",
                impl=ToolImpl(strategy="http_call", http_method="GET", http_path="/items"),
            )
        ],
    )
    body = _build_gotchas(design)
    assert "status code" in body


def test_anti_patterns_omit_crud_line_without_manage_tools():
    body = _build_anti_patterns(_unrelated_design())
    assert "manage_" not in body


def test_anti_patterns_include_crud_line_with_manage_tools():
    design = ServerDesign(
        server_name="tasks",
        tools=[ToolSpec(name="manage_task", description="CRUD for tasks.")],
    )
    body = _build_anti_patterns(design)
    assert "manage_*" in body


def test_skill_fallback_all_sections_present_even_with_no_matches():
    content = _build_skill_fallback(_unrelated_domain_model(), _unrelated_design())
    for section in _SKILL_BUNDLE_SECTIONS:
        assert section in content
