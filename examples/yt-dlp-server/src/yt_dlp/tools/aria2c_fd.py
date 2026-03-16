"""aria2c_fd tools for yt-dlp."""

import json

from mcp.server.fastmcp import FastMCP


def register_tools(server: FastMCP, backend) -> None:
    """Register aria2c_fd tools with the server."""

    @server.tool()
    async def aria2c_fd_aria2c_rpc(
        rpc_port: str,
        rpc_secret: str,
        method: str,
        params: str | None = None,
    ) -> str:
        """Aria2c rpc"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("aria2c_fd_aria2c_rpc")

    @server.tool()
    async def aria2c_fd_supports_manifest(
        manifest: str,
    ) -> str:
        """Supports manifest"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("aria2c_fd_supports_manifest")

