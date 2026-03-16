"""arte_tv_category_ie tools for yt-dlp."""

import json

from mcp.server.fastmcp import FastMCP


def register_tools(server: FastMCP, backend) -> None:
    """Register arte_tv_category_ie tools with the server."""

    @server.tool()
    async def arte_tv_category_ie_suitable(
        url: str,
    ) -> str:
        """Suitable"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("arte_tv_category_ie_suitable")

