"""Test configuration for ffmpeg MCP server."""

import pytest


@pytest.fixture
def server():
    """Create a test server instance."""
    from mcp_ffmpeg.server import server
    return server
