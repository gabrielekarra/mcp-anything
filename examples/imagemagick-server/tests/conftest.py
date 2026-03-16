"""Test configuration for imagemagick MCP server."""

import pytest


@pytest.fixture
def server():
    """Create a test server instance."""
    from imagemagick.server import server
    return server
