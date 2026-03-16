"""Test configuration for click MCP server."""

import pytest


@pytest.fixture
def server():
    """Create a test server instance."""
    from mcp_click.server import server
    return server
