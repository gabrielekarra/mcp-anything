"""Pipeline manifest for tracking generation state."""

import json
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from mcp_anything.models.analysis import AnalysisResult
from mcp_anything.models.design import ServerDesign


class GenerationManifest(BaseModel):
    """Persistent state for the generation pipeline."""

    version: str = "0.1.3"
    codebase_path: str = ""
    output_dir: str = ""
    server_name: str = ""
    completed_phases: list[str] = Field(default_factory=list)
    analysis: Optional[AnalysisResult] = None
    design: Optional[ServerDesign] = None
    generated_files: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    extra_data: Optional[dict] = None

    def save(self, path: Path) -> None:
        path.write_text(self.model_dump_json(indent=2))

    @classmethod
    def load(cls, path: Path) -> "GenerationManifest":
        return cls.model_validate_json(path.read_text())

    def phase_completed(self, phase: str) -> bool:
        return phase in self.completed_phases

    def mark_phase_completed(self, phase: str) -> None:
        if phase not in self.completed_phases:
            self.completed_phases.append(phase)
