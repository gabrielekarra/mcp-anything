"""Resources for click."""

import json

from mcp.server.fastmcp import FastMCP


def register_resources(server: FastMCP, backend) -> None:
    """Register resources with the server."""

    @server.resource("app://click/status")
    async def click_status() -> str:
        """Current status and version of click"""
        try:
            version = await backend.run_cli(["--version"])
        except Exception:
            version = "unknown"
        return json.dumps({
            "name": "click",
            "version": version.strip(),
            "status": "running",
        }, indent=2)

    @server.resource("app://click/commands")
    async def click_commands() -> str:
        """Available commands and tools in click"""
        tools = server.list_tools()
        commands = []
        for tool in tools:
            commands.append({
                "name": tool.name,
                "description": tool.description or "",
            })
        return json.dumps({"commands": commands}, indent=2)

    @server.resource("app://click/config")
    async def click_config() -> str:
        """Current configuration of click"""
        try:
            config_output = await backend.run_cli(["--help"])
        except Exception:
            config_output = "Could not retrieve configuration"
        return json.dumps({
            "help": config_output,
            "codebase_path": str(backend.codebase_path),
        }, indent=2)

    @server.resource("docs://click/tool-index")
    async def click_tool_index() -> str:
        """Complete index of all click tools with parameters and usage"""
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
            "server": "click",
            "resource": "docs://click/tool-index",
            "tools": doc_entries,
        }, indent=2)

    @server.resource("docs://click/argument")
    async def click_argument_docs() -> str:
        """Documentation for click argument capabilities"""
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
            "server": "click",
            "resource": "docs://click/argument",
            "tools": doc_entries,
        }, indent=2)

    @server.resource("docs://click/bash_complete")
    async def click_bash_complete_docs() -> str:
        """Documentation for click bash_complete capabilities"""
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
            "server": "click",
            "resource": "docs://click/bash_complete",
            "tools": doc_entries,
        }, indent=2)

    @server.resource("docs://click/bool_param_type")
    async def click_bool_param_type_docs() -> str:
        """Documentation for click bool_param_type capabilities"""
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
            "server": "click",
            "resource": "docs://click/bool_param_type",
            "tools": doc_entries,
        }, indent=2)

    @server.resource("docs://click/bytes_io_copy")
    async def click_bytes_io_copy_docs() -> str:
        """Documentation for click bytes_io_copy capabilities"""
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
            "server": "click",
            "resource": "docs://click/bytes_io_copy",
            "tools": doc_entries,
        }, indent=2)

    @server.resource("docs://click/choice")
    async def click_choice_docs() -> str:
        """Documentation for click choice capabilities"""
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
            "server": "click",
            "resource": "docs://click/choice",
            "tools": doc_entries,
        }, indent=2)

