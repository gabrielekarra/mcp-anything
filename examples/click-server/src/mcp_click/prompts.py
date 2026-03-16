"""Server-delivered MCP prompts (skills) for click."""

from mcp.server.fastmcp import FastMCP


def register_prompts(server: FastMCP) -> None:
    """Register prompts with the server."""

    @server.prompt("use_click")
    async def use_click_prompt() -> str:
        """Guide for using click tools effectively"""
        return """You have access to the click MCP server with these tools:

- add_completion_class: Register a :class:`ShellComplete` subclass under the given name.
- argument_add_to_parser: Add to parser
- argument_get_error_hint: Get error hint
- argument_get_usage_pieces: Get usage pieces
- argument_human_readable_name: Human readable name
- argument_make_metavar: Make metavar
- augment_usage_errors: Context manager that attaches extra information to exceptions.
- bash_complete_format_completion: Format completion
- batch: Batch
- bool_param_type_convert: Convert
- bool_param_type_str_to_bool: Convert a string to a boolean value.
- bytes_io_copy_write: Write
- choice_convert: For a given value from the parser, normalize it and find its
- choice_get_invalid_choice_message: Get the error message when the given choice is invalid.
- choice_get_metavar: Get metavar
- choice_get_missing_message: Message shown when no choice is passed.
- choice_normalize_choice: Normalize a choice value, used to map a passed string to a choice.
- choice_shell_complete: Complete choices that start with the incomplete value.
- choice_to_info_dict: To info dict
- clear: Clears the terminal screen.  This will have the effect of clearing

Use the appropriate tool based on the user's request. Always check required parameters before calling a tool."""

    @server.prompt("debug_click")
    async def debug_click_prompt(error_message: str) -> str:
        """Diagnose issues with click operations"""
        return """The user encountered an error while using click.

Error: {{error_message}}

Available tools: add_completion_class, argument_add_to_parser, argument_get_error_hint, argument_get_usage_pieces, argument_human_readable_name, argument_make_metavar, augment_usage_errors, bash_complete_format_completion, batch, bool_param_type_convert, bool_param_type_str_to_bool, bytes_io_copy_write, choice_convert, choice_get_invalid_choice_message, choice_get_metavar

Diagnose the issue and suggest which tool to use to resolve it."""

