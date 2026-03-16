"""MCP server for click."""

import os

from mcp.server.fastmcp import FastMCP

server = FastMCP("click")

from mcp_click.backend import Backend

_backend = Backend()

# Import and register tool modules
from mcp_click.tools.general import register_tools as register_general_tools
register_general_tools(server, _backend)
from mcp_click.tools.creation import register_tools as register_creation_tools
register_creation_tools(server, _backend)
from mcp_click.tools.argument import register_tools as register_argument_tools
register_argument_tools(server, _backend)
from mcp_click.tools.bash_complete import register_tools as register_bash_complete_tools
register_bash_complete_tools(server, _backend)
from mcp_click.tools.bool_param_type import register_tools as register_bool_param_type_tools
register_bool_param_type_tools(server, _backend)
from mcp_click.tools.bytes_io_copy import register_tools as register_bytes_io_copy_tools
register_bytes_io_copy_tools(server, _backend)
from mcp_click.tools.choice import register_tools as register_choice_tools
register_choice_tools(server, _backend)
from mcp_click.tools.cli_runner import register_tools as register_cli_runner_tools
register_cli_runner_tools(server, _backend)
from mcp_click.tools.click_exception import register_tools as register_click_exception_tools
register_click_exception_tools(server, _backend)
from mcp_click.tools.command import register_tools as register_command_tools
register_command_tools(server, _backend)
from mcp_click.tools.command_collection import register_tools as register_command_collection_tools
register_command_collection_tools(server, _backend)
from mcp_click.tools.composite_param_type import register_tools as register_composite_param_type_tools
register_composite_param_type_tools(server, _backend)
from mcp_click.tools.console_stream import register_tools as register_console_stream_tools
register_console_stream_tools(server, _backend)
from mcp_click.tools.context import register_tools as register_context_tools
register_context_tools(server, _backend)
from mcp_click.tools.conversion import register_tools as register_conversion_tools
register_conversion_tools(server, _backend)
from mcp_click.tools.date_time import register_tools as register_date_time_tools
register_date_time_tools(server, _backend)
from mcp_click.tools.echoing_stdin import register_tools as register_echoing_stdin_tools
register_echoing_stdin_tools(server, _backend)
from mcp_click.tools.editor import register_tools as register_editor_tools
register_editor_tools(server, _backend)
from mcp_click.tools.file import register_tools as register_file_tools
register_file_tools(server, _backend)
from mcp_click.tools.fish_complete import register_tools as register_fish_complete_tools
register_fish_complete_tools(server, _backend)
from mcp_click.tools.func_param_type import register_tools as register_func_param_type_tools
register_func_param_type_tools(server, _backend)
from mcp_click.tools.query import register_tools as register_query_tools
register_query_tools(server, _backend)
from mcp_click.tools.group import register_tools as register_group_tools
register_group_tools(server, _backend)
from mcp_click.tools.help_formatter import register_tools as register_help_formatter_tools
register_help_formatter_tools(server, _backend)
from mcp_click.tools.lazy_file import register_tools as register_lazy_file_tools
register_lazy_file_tools(server, _backend)
from mcp_click.tools.no_args_is_help_error import register_tools as register_no_args_is_help_error_tools
register_no_args_is_help_error_tools(server, _backend)
from mcp_click.tools.option import register_tools as register_option_tools
register_option_tools(server, _backend)
from mcp_click.tools.param_type import register_tools as register_param_type_tools
register_param_type_tools(server, _backend)
from mcp_click.tools.parameter import register_tools as register_parameter_tools
register_parameter_tools(server, _backend)
from mcp_click.tools.path import register_tools as register_path_tools
register_path_tools(server, _backend)
from mcp_click.tools.progress_bar import register_tools as register_progress_bar_tools
register_progress_bar_tools(server, _backend)
from mcp_click.tools.result import register_tools as register_result_tools
register_result_tools(server, _backend)
from mcp_click.tools.shell_complete import register_tools as register_shell_complete_tools
register_shell_complete_tools(server, _backend)

# Import and register resources
from mcp_click.resources import register_resources
register_resources(server, _backend)

# Import and register prompts
from mcp_click.prompts import register_prompts
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
