"""aws_idp tools for yt-dlp."""

import json

from mcp.server.fastmcp import FastMCP


def register_tools(server: FastMCP, backend) -> None:
    """Register aws_idp tools with the server."""

    @server.tool()
    async def aws_idp_authenticate(
        username: str,
        password: str,
    ) -> str:
        """Authenticate with a username and password."""
        # Stub — implementation not yet generated
        return await backend.run_subcommand("aws_idp_authenticate")

