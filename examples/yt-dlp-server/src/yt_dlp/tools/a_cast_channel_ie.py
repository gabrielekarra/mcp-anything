"""a_cast_channel_ie tools for yt-dlp."""

import json

from mcp.server.fastmcp import FastMCP


def register_tools(server: FastMCP, backend) -> None:
    """Register a_cast_channel_ie tools with the server."""

    @server.tool()
    async def a_cast_channel_ie_suitable(
        url: str,
    ) -> str:
        """Suitable"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("a_cast_channel_ie_suitable")

