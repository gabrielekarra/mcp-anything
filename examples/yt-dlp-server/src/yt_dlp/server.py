"""MCP server for yt-dlp."""

import os

from mcp.server.fastmcp import FastMCP

server = FastMCP("yt-dlp")

from yt_dlp.backend import Backend

_backend = Backend()

# Import and register tool modules
from yt_dlp.tools.general import register_tools as register_general_tools
register_general_tools(server, _backend)
from yt_dlp.tools.a_cast_channel_ie import register_tools as register_a_cast_channel_ie_tools
register_a_cast_channel_ie_tools(server, _backend)
from yt_dlp.tools.creation import register_tools as register_creation_tools
register_creation_tools(server, _backend)
from yt_dlp.tools.alura_course_ie import register_tools as register_alura_course_ie_tools
register_alura_course_ie_tools(server, _backend)
from yt_dlp.tools.andere_tijden_ie import register_tools as register_andere_tijden_ie_tools
register_andere_tijden_ie_tools(server, _backend)
from yt_dlp.tools.aria2c_fd import register_tools as register_aria2c_fd_tools
register_aria2c_fd_tools(server, _backend)
from yt_dlp.tools.arte_tv_category_ie import register_tools as register_arte_tv_category_ie_tools
register_arte_tv_category_ie_tools(server, _backend)
from yt_dlp.tools.aws_idp import register_tools as register_aws_idp_tools
register_aws_idp_tools(server, _backend)
from yt_dlp.tools.bandcamp_album_ie import register_tools as register_bandcamp_album_ie_tools
register_bandcamp_album_ie_tools(server, _backend)
from yt_dlp.tools.bbcie import register_tools as register_bbcie_tools
register_bbcie_tools(server, _backend)
from yt_dlp.tools.bbvtv_live_ie import register_tools as register_bbvtv_live_ie_tools
register_bbvtv_live_ie_tools(server, _backend)
from yt_dlp.tools.bili_intl_base_ie import register_tools as register_bili_intl_base_ie_tools
register_bili_intl_base_ie_tools(server, _backend)
from yt_dlp.tools.bilibili_base_ie import register_tools as register_bilibili_base_ie_tools
register_bilibili_base_ie_tools(server, _backend)
from yt_dlp.tools.bilibili_collection_list_ie import register_tools as register_bilibili_collection_list_ie_tools
register_bilibili_collection_list_ie_tools(server, _backend)
from yt_dlp.tools.block import register_tools as register_block_tools
register_block_tools(server, _backend)
from yt_dlp.tools.breakline_status_printer import register_tools as register_breakline_status_printer_tools
register_breakline_status_printer_tools(server, _backend)
from yt_dlp.tools.bunny_cdn_fd import register_tools as register_bunny_cdn_fd_tools
register_bunny_cdn_fd_tools(server, _backend)
from yt_dlp.tools.cache import register_tools as register_cache_tools
register_cache_tools(server, _backend)
from yt_dlp.tools.callin_ie import register_tools as register_callin_ie_tools
register_callin_ie_tools(server, _backend)

# Import and register resources
from yt_dlp.resources import register_resources
register_resources(server, _backend)

# Import and register prompts
from yt_dlp.prompts import register_prompts
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
