"""Resources for httpstat."""

import json

from mcp.server.fastmcp import FastMCP


def register_resources(server: FastMCP, backend) -> None:
    """Register resources with the server."""

    @server.resource("app://httpstat/status")
    async def httpstat_status() -> str:
        """Current status and version of httpstat"""
        try:
            version = await backend.run_cli(["--version"])
        except Exception:
            version = "unknown"
        return json.dumps({
            "name": "httpstat",
            "version": version.strip(),
            "status": "running",
        }, indent=2)

    @server.resource("app://httpstat/commands")
    async def httpstat_commands() -> str:
        """Available commands and tools in httpstat"""
        tools = server.list_tools()
        commands = []
        for tool in tools:
            commands.append({
                "name": tool.name,
                "description": tool.description or "",
            })
        return json.dumps({"commands": commands}, indent=2)

    @server.resource("docs://httpstat/tool-index")
    async def httpstat_tool_index() -> str:
        """Complete index of all httpstat tools with parameters and usage"""
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
            "server": "httpstat",
            "resource": "docs://httpstat/tool-index",
            "tools": doc_entries,
        }, indent=2)

