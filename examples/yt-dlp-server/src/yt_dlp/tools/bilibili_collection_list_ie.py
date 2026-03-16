"""bilibili_collection_list_ie tools for yt-dlp."""

import json

from mcp.server.fastmcp import FastMCP


def register_tools(server: FastMCP, backend) -> None:
    """Register bilibili_collection_list_ie tools with the server."""

    @server.tool()
    async def bilibili_collection_list_ie_suitable(
        url: str,
    ) -> str:
        """Suitable"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("bilibili_collection_list_ie_suitable")

