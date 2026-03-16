"""block tools for yt-dlp."""

import json

from mcp.server.fastmcp import FastMCP


def register_tools(server: FastMCP, backend) -> None:
    """Register block tools with the server."""

    @server.tool()
    async def block_parse(
        parser: str,
    ) -> str:
        """Parse"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("block_parse")

    @server.tool()
    async def block_write_into(
        stream: str,
    ) -> str:
        """Write into"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("block_write_into")

