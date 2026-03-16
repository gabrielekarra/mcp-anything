"""bandcamp_album_ie tools for yt-dlp."""

import json

from mcp.server.fastmcp import FastMCP


def register_tools(server: FastMCP, backend) -> None:
    """Register bandcamp_album_ie tools with the server."""

    @server.tool()
    async def bandcamp_album_ie_suitable(
        url: str,
    ) -> str:
        """Suitable"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("bandcamp_album_ie_suitable")

