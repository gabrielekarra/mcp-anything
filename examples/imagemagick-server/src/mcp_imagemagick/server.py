"""MCP server for imagemagick."""

import os

from mcp.server.fastmcp import FastMCP

server = FastMCP("imagemagick")

from mcp_imagemagick.backend import Backend

_backend = Backend()

# Import and register tool modules
from mcp_imagemagick.tools.general import register_tools as register_general_tools
register_general_tools(server, _backend)
from mcp_imagemagick.tools.base_image import register_tools as register_base_image_tools
register_base_image_tools(server, _backend)

# Import and register resources
from mcp_imagemagick.resources import register_resources
register_resources(server, _backend)

# Import and register prompts
from mcp_imagemagick.prompts import register_prompts
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
