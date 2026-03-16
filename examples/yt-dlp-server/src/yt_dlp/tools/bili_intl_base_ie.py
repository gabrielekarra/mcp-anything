"""bili_intl_base_ie tools for yt-dlp."""

import json

from mcp.server.fastmcp import FastMCP


def register_tools(server: FastMCP, backend) -> None:
    """Register bili_intl_base_ie tools with the server."""

    @server.tool()
    async def bili_intl_base_ie_json2srt(
        json: str,
    ) -> str:
        """Json2srt"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("bili_intl_base_ie_json2srt")

