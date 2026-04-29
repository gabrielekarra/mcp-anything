"""Tests for Phase 4: SkillBundlePhase."""

import asyncio
import json
from pathlib import Path

import pytest

from mcp_anything.config import CLIOptions
from mcp_anything.models.design import ComposedTool, ServerDesign, ToolGroup, ToolSpec
from mcp_anything.models.domain import DomainModel, UseCase
from mcp_anything.models.manifest import GenerationManifest
from mcp_anything.pipeline.context import PipelineContext
from mcp_anything.pipeline.skill_bundle import (
    SkillBundlePhase,
    _SKILL_BUNDLE_SECTIONS,
    _build_quick_queries,
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
