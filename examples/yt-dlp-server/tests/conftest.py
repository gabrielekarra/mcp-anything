"""Test configuration for yt-dlp MCP server."""

import pytest


@pytest.fixture
def server():
    """Create a test server instance."""
    from yt_dlp.server import server
    return server
