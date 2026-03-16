"""callin_ie tools for yt-dlp."""

import json

from mcp.server.fastmcp import FastMCP


def register_tools(server: FastMCP, backend) -> None:
    """Register callin_ie tools with the server."""

    @server.tool()
    async def callin_ie_try_get_user_name(
        d: str,
    ) -> str:
        """Try get user name"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("callin_ie_try_get_user_name")

