"""breakline_status_printer tools for yt-dlp."""

import json

from mcp.server.fastmcp import FastMCP


def register_tools(server: FastMCP, backend) -> None:
    """Register breakline_status_printer tools with the server."""

    @server.tool()
    async def breakline_status_printer_print_at_line(
        text: str,
        pos: str,
    ) -> str:
        """Print at line"""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("breakline_status_printer_print_at_line")

