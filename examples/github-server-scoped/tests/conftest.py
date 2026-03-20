"""Test configuration for github-scoped MCP server."""

import pytest


@pytest.fixture
def server_module():
    """Import the generated server module."""
    from mcp_github_scoped import server as server_module
    return server_module


@pytest.fixture
def server():
    """Create a test server instance."""
    from mcp_github_scoped.server import server
    return server


@pytest.fixture
def backend(server_module):
    """Expose the generated backend instance when present."""
    return getattr(server_module, "_backend", None)
