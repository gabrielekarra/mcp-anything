"""MCP server for httpstat."""

import os

from mcp.server.fastmcp import FastMCP

server = FastMCP("httpstat")

from mcp_httpstat.backend import Backend

_backend = Backend()

# Import and register tool modules
from mcp_httpstat.tools.general import register_tools as register_general_tools
register_general_tools(server, _backend)

# Import and register resources
from mcp_httpstat.resources import register_resources
register_resources(server, _backend)

# Import and register prompts
from mcp_httpstat.prompts import register_prompts
register_prompts(server)



def main():
    """Run the MCP server."""
    transport = os.environ.get("MCP_TRANSPORT", "stdio")

    if transport == "http":
        host = os.environ.get("MCP_HOST", "0.0.0.0")
        port = int(os.environ.get("MCP_PORT", "8000"))
        server.run(transport="sse", host=host, port=port)
    else:
        server.run(transport="stdio")


if __name__ == "__main__":
    main()
