"""Data models for httpstat MCP server."""

from dataclasses import dataclass
from typing import Any


@dataclass
class RunHttpstatParams:
    """Parameters for run_httpstat."""
    args: str

