"""cache tools for yt-dlp."""

import json

from mcp.server.fastmcp import FastMCP


def register_tools(server: FastMCP, backend) -> None:
    """Register cache tools with the server."""

    @server.tool()
    async def cache_enabled(
    ) -> str:
        """Enabled"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("cache_enabled")

    @server.tool()
    async def cache_load(
        section: str,
        key: str,
        dtype: str | None = "json",
        default: str | None = None,
        min_ver: str | None = None,
    ) -> str:
        """Load"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("cache_load")

    @server.tool()
    async def cache_store(
        section: str,
        key: str,
        data: str,
        dtype: str | None = "json",
    ) -> str:
        """Store"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("cache_store")

