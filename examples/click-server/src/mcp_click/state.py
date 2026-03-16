"""Shared state management for click MCP server."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ServerState:
    """Tracks server state across tool invocations."""

    connected: bool = False
    last_error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def set_error(self, error: str) -> None:
        self.last_error = error

    def clear_error(self) -> None:
        self.last_error = None


# Global state instance
state = ServerState()
