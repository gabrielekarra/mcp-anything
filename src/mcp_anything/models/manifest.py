"""Pipeline manifest for tracking generation state."""

import json
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, Field

from mcp_anything.models.analysis import AnalysisResult
from mcp_anything.models.design import ServerDesign


class GenerationManifest(BaseModel):
    """Persistent state for the generation pipeline."""

    version: str = "0.2.0"
    pipeline_mode: Literal["legacy", "domain"] = "legacy"
    codebase_path: str = ""
    output_dir: str = ""
    server_name: str = ""
    completed_phases: list[str] = Field(default_factory=list)
    # Legacy pipeline fields (pipeline_mode == "legacy")
    analysis: Optional[AnalysisResult] = None
    design: Optional[ServerDesign] = None
    # Domain pipeline fields (pipeline_mode == "domain")
    domain_model: Optional[dict] = None   # serialized DomainModel
    tool_spec: Optional[dict] = None       # serialized ServerDesign (from ToolDesignPhase)
    skill_bundle: Optional[dict] = None    # serialized SkillBundle
    eval_cases: Optional[list] = None      # list of serialized EvalCase
    contract_check_results: Optional[list] = None  # serialized ContractCheckResult from emit phase
    generated_files: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    extra_data: Optional[dict] = None

    def save(self, path: Path) -> None:
        path.write_text(self.model_dump_json(indent=2))

    @classmethod
    def load(cls, path: Path) -> "GenerationManifest":
        raw = json.loads(path.read_text())
        return cls.model_validate(cls._migrate(raw))

    @staticmethod
    def _migrate(raw: dict) -> dict:
        """Migrate v0.1.x manifests to v0.2.0 shape."""
        v = raw.get("version", "0.1.0")
        if v.startswith("0.1"):
            raw["version"] = "0.2.0"
            raw.setdefault("pipeline_mode", "legacy")
            raw.setdefault("domain_model", None)
            raw.setdefault("tool_spec", None)
            raw.setdefault("skill_bundle", None)
            raw.setdefault("eval_cases", None)
            raw.setdefault("contract_check_results", None)
        return raw

    def phase_completed(self, phase: str) -> bool:
        return phase in self.completed_phases

    def mark_phase_completed(self, phase: str) -> None:
        if phase not in self.completed_phases:
            self.completed_phases.append(phase)
