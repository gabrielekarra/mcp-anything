"""alura_course_ie tools for yt-dlp."""

import json

from mcp.server.fastmcp import FastMCP


def register_tools(server: FastMCP, backend) -> None:
    """Register alura_course_ie tools with the server."""

    @server.tool()
    async def alura_course_ie_suitable(
        url: str,
    ) -> str:
        """Suitable"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("alura_course_ie_suitable")

