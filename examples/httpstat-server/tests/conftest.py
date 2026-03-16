"""Test configuration for httpstat MCP server."""

import pytest


@pytest.fixture
def server():
    """Create a test server instance."""
    from mcp_httpstat.server import server
    return server
