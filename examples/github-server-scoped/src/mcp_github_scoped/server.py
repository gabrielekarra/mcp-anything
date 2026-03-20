"""MCP server for github-scoped."""

import os

from mcp.server.fastmcp import FastMCP

server = FastMCP("github-scoped")


from mcp_github_scoped.backend import Backend

_backend = Backend()

# Import and register tool modules
from mcp_github_scoped.tools.api import register_tools as register_api_tools
register_api_tools(server, _backend)

# Import and register resources
from mcp_github_scoped.resources import register_resources
register_resources(server, _backend)

# Import and register prompts
from mcp_github_scoped.prompts import register_prompts
register_prompts(server)


def main():
    """Run the MCP server."""
    transport = os.environ.get("MCP_TRANSPORT", "stdio")

    if transport == "http":
        host = os.environ.get("MCP_HOST", "0.0.0.0")
        port = int(os.environ.get("MCP_PORT", "8000"))
        server.settings.host = host
        server.settings.port = port
        server.run(transport="streamable-http")
    else:
        server.run(transport="stdio")


if __name__ == "__main__":
    main()
