"""creation tools for yt-dlp."""

import json

from mcp.server.fastmcp import FastMCP


def register_tools(server: FastMCP, backend) -> None:
    """Register creation tools with the server."""

    @server.tool()
    async def add_accept_encoding_header(
        headers: str,
        supported_encodings: str,
    ) -> str:
        """Add accept encoding header"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("add_accept_encoding_header")

