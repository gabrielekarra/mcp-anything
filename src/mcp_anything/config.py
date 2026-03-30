"""CLI configuration model."""

from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class CLIOptions(BaseModel):
    """Options parsed from CLI arguments."""

    codebase_path: Path
    output_dir: Optional[Path] = None
    name: Optional[str] = None
    backend: Optional[str] = None
    phases: Optional[list[str]] = None
    resume: bool = False
    description: bool = False  # apply description overrides from descriptions.yaml
    no_llm: bool = False
    no_install: bool = False
    verbose: bool = False
    transport: str = "stdio"  # "stdio" or "http"
    target: str = "fastmcp"  # "fastmcp" or "mcp-use"
    source_url: Optional[str] = None  # URL if fetched from remote
    include: Optional[list[str]] = None  # glob patterns to include capabilities
    exclude: Optional[list[str]] = None  # glob patterns to exclude capabilities
    scope_file: Optional[Path] = None  # path to scope.yaml for capability curation
    review: bool = False  # pause after ANALYZE to write scope.yaml for editing

    def resolved_name(self) -> str:
        """Server name derived from codebase directory or override."""
        if self.name:
            return self.name
        return self.codebase_path.resolve().name.lower().replace(" ", "-")

    def resolved_output_dir(self) -> Path:
        """Output directory, defaulting to ./mcp-<name>-server."""
        if self.output_dir:
            return self.output_dir
        return Path(f"./mcp-{self.resolved_name()}-server")
