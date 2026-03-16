"""Protocol compliance tests for ffmpeg MCP server."""

import pytest


class TestMCPCompliance:
    """Verify MCP protocol compliance."""

    def test_server_creation(self, server):
        """Server should be created successfully."""
        assert server is not None
        assert server.name == "ffmpeg"
