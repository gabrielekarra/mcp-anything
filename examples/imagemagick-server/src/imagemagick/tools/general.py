"""general tools for imagemagick."""

import json

from mcp.server.fastmcp import FastMCP


def register_tools(server: FastMCP, backend) -> None:
    """Register general tools with the server."""

    @server.tool()
    async def allocate_ref(
        addr: str,
        deallocator: str,
    ) -> str:
        """Allocate ref"""
        # Direct Python call: resource.allocate_ref
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from resource import allocate_ref
        result = allocate_ref(
            addr=addr,
            deallocator=deallocator,
        )
        return str(result)

