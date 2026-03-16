"""bunny_cdn_fd tools for yt-dlp."""

import json

from mcp.server.fastmcp import FastMCP


def register_tools(server: FastMCP, backend) -> None:
    """Register bunny_cdn_fd tools with the server."""

    @server.tool()
    async def bunny_cdn_fd_ping_thread(
        stop_event: str,
        url: str,
        headers: str,
        secret: str,
        context_id: str,
    ) -> str:
        """Ping thread"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("bunny_cdn_fd_ping_thread")

    @server.tool()
    async def bunny_cdn_fd_real_download(
        filename: str,
        info_dict: str,
    ) -> str:
        """Real download"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("bunny_cdn_fd_real_download")

