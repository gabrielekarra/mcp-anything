"""bilibili_base_ie tools for yt-dlp."""

import json

from mcp.server.fastmcp import FastMCP


def register_tools(server: FastMCP, backend) -> None:
    """Register bilibili_base_ie tools with the server."""

    @server.tool()
    async def bilibili_base_ie_extract_formats(
        play_info: str,
    ) -> str:
        """Extract formats"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("bilibili_base_ie_extract_formats")

    @server.tool()
    async def bilibili_base_ie_is_logged_in(
    ) -> str:
        """Is logged in"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("bilibili_base_ie_is_logged_in")

    @server.tool()
    async def bilibili_base_ie_json2srt(
        json_data: str,
    ) -> str:
        """Json2srt"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("bilibili_base_ie_json2srt")

