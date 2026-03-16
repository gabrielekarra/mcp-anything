"""Server-delivered MCP prompts (skills) for httpstat."""

from mcp.server.fastmcp import FastMCP


def register_prompts(server: FastMCP) -> None:
    """Register prompts with the server."""

    @server.prompt("use_httpstat")
    async def use_httpstat_prompt() -> str:
        """Guide for using httpstat tools effectively"""
        return """You have access to the httpstat MCP server with these tools:

- print_help: Print help

Use the appropriate tool based on the user's request. Always check required parameters before calling a tool."""

    @server.prompt("debug_httpstat")
    async def debug_httpstat_prompt(error_message: str) -> str:
        """Diagnose issues with httpstat operations"""
        return """The user encountered an error while using httpstat.

Error: {{error_message}}

Available tools: print_help

Diagnose the issue and suggest which tool to use to resolve it."""

