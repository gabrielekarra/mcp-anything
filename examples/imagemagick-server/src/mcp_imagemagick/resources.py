"""Resources for imagemagick."""

import json

from mcp.server.fastmcp import FastMCP


def register_resources(server: FastMCP, backend) -> None:
    """Register resources with the server."""

    @server.resource("app://imagemagick/status")
    async def imagemagick_status() -> str:
        """Current status and version of imagemagick"""
        return json.dumps({
            "name": "imagemagick",
            "status": "running",
        }, indent=2)

    @server.resource("app://imagemagick/commands")
    async def imagemagick_commands() -> str:
        """Available commands and tools in imagemagick"""
        tools = server.list_tools()
        commands = []
        for tool in tools:
            commands.append({
                "name": tool.name,
                "description": tool.description or "",
            })
        return json.dumps({"commands": commands}, indent=2)

    @server.resource("docs://imagemagick/tool-index")
    async def imagemagick_tool_index() -> str:
        """Complete index of all imagemagick tools with parameters and usage"""
        # Dynamic documentation resource
        tools = server.list_tools()
        doc_entries = []
        for tool in tools:
            entry = {"name": tool.name, "description": tool.description or ""}
            if hasattr(tool, "inputSchema") and tool.inputSchema:
                entry["parameters"] = tool.inputSchema.get("properties", {})
                entry["required"] = tool.inputSchema.get("required", [])
            doc_entries.append(entry)
        return json.dumps({
            "server": "imagemagick",
            "resource": "docs://imagemagick/tool-index",
            "tools": doc_entries,
        }, indent=2)

    @server.resource("docs://imagemagick/base_image")
    async def imagemagick_base_image_docs() -> str:
        """Documentation for imagemagick base_image capabilities"""
        # Dynamic documentation resource
        tools = server.list_tools()
        doc_entries = []
        for tool in tools:
            entry = {"name": tool.name, "description": tool.description or ""}
            if hasattr(tool, "inputSchema") and tool.inputSchema:
                entry["parameters"] = tool.inputSchema.get("properties", {})
                entry["required"] = tool.inputSchema.get("required", [])
            doc_entries.append(entry)
        return json.dumps({
            "server": "imagemagick",
            "resource": "docs://imagemagick/base_image",
            "tools": doc_entries,
        }, indent=2)

