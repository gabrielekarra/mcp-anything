"""Tests for Phase 1: DomainModelingPhase."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from mcp_anything.config import CLIOptions
from mcp_anything.models.domain import DomainBrief, DomainModel, UseCase
from mcp_anything.models.manifest import GenerationManifest
from mcp_anything.pipeline.context import PipelineContext
from mcp_anything.pipeline.domain_modeling import (
    DomainModelingPhase,
    _deterministic_domain_model,
)
from rich.console import Console


@pytest.fixture
def sample_brief() -> DomainBrief:
    return DomainBrief(
        server_name="task-manager",
        domain_description="Manages tasks and projects for teams.",
        use_cases=[
            "List all open tasks assigned to a user",
            "Create a task in a project",
            "Update task status to done",
        ],
        glossary={"Task": "A unit of work", "Project": "A container for tasks"},
        data_source_path="",
        data_source_kind="other",
        backend_target="fastmcp",
    )


@pytest.fixture
def brief_yaml_file(tmp_path, sample_brief) -> Path:
    p = tmp_path / "brief.yaml"
    data = {
        "server_name": sample_brief.server_name,
        "domain_description": sample_brief.domain_description,
        "use_cases": sample_brief.use_cases,
        "glossary": sample_brief.glossary,
        "backend_target": "fastmcp",
    }
    p.write_text(yaml.dump(data))
    return p


@pytest.fixture
def ctx(tmp_path, sample_brief) -> PipelineContext:
    opts = CLIOptions(
        codebase_path=tmp_path,
        output_dir=tmp_path / "output",
        name="task-manager",
        no_llm=True,
        domain_brief=sample_brief.model_dump(),
    )
    manifest = GenerationManifest(
        pipeline_mode="domain",
        codebase_path=str(tmp_path),
        output_dir=str(tmp_path / "output"),
        server_name="task-manager",
    )
    return PipelineContext(opts, manifest, Console(quiet=True))


def test_deterministic_domain_model(sample_brief):
    model = _deterministic_domain_model(sample_brief)
    assert model.server_name == "task-manager"
    assert len(model.use_cases) == 3
    assert model.use_cases[0].id == "uc-01"
    assert len(model.glossary) == 2
    assert not model.approved


def test_domain_model_roundtrip(sample_brief):
    model = _deterministic_domain_model(sample_brief)
    data = model.model_dump_json()
    restored = DomainModel.model_validate_json(data)
    assert restored.server_name == model.server_name
    assert len(restored.use_cases) == len(model.use_cases)


def test_phase_execute_no_llm(ctx, tmp_path):
    phase = DomainModelingPhase()
    errors = phase.validate_preconditions(ctx)
    assert errors == []

    import asyncio
    asyncio.run(phase.execute(ctx))

    output = tmp_path / "output" / "domain_model.json"
    assert output.exists()
    model = DomainModel.model_validate_json(output.read_text())
    assert model.server_name == "task-manager"
    assert len(model.use_cases) == 3


def test_phase_requires_brief():
    opts = CLIOptions(
        codebase_path=Path("."),
        no_llm=True,
    )
    manifest = GenerationManifest(
        pipeline_mode="domain",
        codebase_path=".",
        output_dir=".",
        server_name="test",
    )
    ctx = PipelineContext(opts, manifest, Console(quiet=True))
    phase = DomainModelingPhase()
    errors = phase.validate_preconditions(ctx)
    assert len(errors) == 1
    assert "brief" in errors[0].lower()


def test_phase_loads_brief_from_yaml(tmp_path, brief_yaml_file):
    opts = CLIOptions(
        codebase_path=tmp_path,
        output_dir=tmp_path / "output",
        name="task-manager",
        no_llm=True,
        brief_file=brief_yaml_file,
    )
    manifest = GenerationManifest(
        pipeline_mode="domain",
        codebase_path=str(tmp_path),
        output_dir=str(tmp_path / "output"),
        server_name="task-manager",
    )
    ctx = PipelineContext(opts, manifest, Console(quiet=True))
    phase = DomainModelingPhase()

    import asyncio
    asyncio.run(phase.execute(ctx))

    model = DomainModel.model_validate_json(
        (tmp_path / "output" / "domain_model.json").read_text()
    )
    assert model.server_name == "task-manager"


def test_manifest_updated_after_phase(ctx, tmp_path):
    phase = DomainModelingPhase()
    import asyncio
    asyncio.run(phase.execute(ctx))

    assert ctx.manifest.domain_model is not None
    model = DomainModel.model_validate(ctx.manifest.domain_model)
    assert model.server_name == "task-manager"
