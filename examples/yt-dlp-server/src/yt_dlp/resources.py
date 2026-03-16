"""Resources for yt-dlp."""

import json

from mcp.server.fastmcp import FastMCP


def register_resources(server: FastMCP, backend) -> None:
    """Register resources with the server."""

    @server.resource("app://yt-dlp/status")
    async def yt_dlp_status() -> str:
        """Current status and version of yt-dlp"""
        return json.dumps({
            "name": "yt-dlp",
            "status": "running",
        }, indent=2)

    @server.resource("app://yt-dlp/commands")
    async def yt_dlp_commands() -> str:
        """Available commands and tools in yt-dlp"""
        tools = server.list_tools()
        commands = []
        for tool in tools:
            commands.append({
                "name": tool.name,
                "description": tool.description or "",
            })
        return json.dumps({"commands": commands}, indent=2)

    @server.resource("docs://yt-dlp/tool-index")
    async def yt_dlp_tool_index() -> str:
        """Complete index of all yt-dlp tools with parameters and usage"""
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
            "server": "yt-dlp",
            "resource": "docs://yt-dlp/tool-index",
            "tools": doc_entries,
        }, indent=2)

    @server.resource("docs://yt-dlp/a_cast_channel_ie")
    async def yt_dlp_a_cast_channel_ie_docs() -> str:
        """Documentation for yt-dlp a_cast_channel_ie capabilities"""
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
            "server": "yt-dlp",
            "resource": "docs://yt-dlp/a_cast_channel_ie",
            "tools": doc_entries,
        }, indent=2)

    @server.resource("docs://yt-dlp/alura_course_ie")
    async def yt_dlp_alura_course_ie_docs() -> str:
        """Documentation for yt-dlp alura_course_ie capabilities"""
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
            "server": "yt-dlp",
            "resource": "docs://yt-dlp/alura_course_ie",
            "tools": doc_entries,
        }, indent=2)

    @server.resource("docs://yt-dlp/andere_tijden_ie")
    async def yt_dlp_andere_tijden_ie_docs() -> str:
        """Documentation for yt-dlp andere_tijden_ie capabilities"""
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
            "server": "yt-dlp",
            "resource": "docs://yt-dlp/andere_tijden_ie",
            "tools": doc_entries,
        }, indent=2)

    @server.resource("docs://yt-dlp/aria2c_fd")
    async def yt_dlp_aria2c_fd_docs() -> str:
        """Documentation for yt-dlp aria2c_fd capabilities"""
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
            "server": "yt-dlp",
            "resource": "docs://yt-dlp/aria2c_fd",
            "tools": doc_entries,
        }, indent=2)

    @server.resource("docs://yt-dlp/arte_tv_category_ie")
    async def yt_dlp_arte_tv_category_ie_docs() -> str:
        """Documentation for yt-dlp arte_tv_category_ie capabilities"""
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
            "server": "yt-dlp",
            "resource": "docs://yt-dlp/arte_tv_category_ie",
            "tools": doc_entries,
        }, indent=2)

