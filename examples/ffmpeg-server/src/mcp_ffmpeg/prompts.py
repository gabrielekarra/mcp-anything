"""Server-delivered MCP prompts (skills) for ffmpeg."""

from mcp.server.fastmcp import FastMCP


def register_prompts(server: FastMCP) -> None:
    """Register prompts with the server."""

    @server.prompt("use_ffmpeg")
    async def use_ffmpeg_prompt() -> str:
        """Guide for using ffmpeg tools effectively"""
        return """You have access to the ffmpeg MCP server with these tools:

- ffmpeg_getting_help: Getting help options for ffmpeg
- ffmpeg_print_help_information_capabilities: Print help / information / capabilities options for ffmpeg
- ffmpeg_global_options_affect_whole_program_instead_of_just_one_file: Global options (affect whole program instead of just one file) options for ffmpeg
- ffmpeg_advanced_global_options: Advanced global options options for ffmpeg
- ffmpeg_per_file_main_options: Per-file main options options for ffmpeg
- ffmpeg_advanced_per_file_options: Advanced per-file options options for ffmpeg
- ffmpeg_video_options: Video options options for ffmpeg
- ffmpeg_advanced_video_options: Advanced Video options options for ffmpeg
- ffmpeg_audio_options: Audio options options for ffmpeg
- ffmpeg_advanced_audio_options: Advanced Audio options options for ffmpeg
- ffmpeg_subtitle_options: Subtitle options options for ffmpeg
- ffmpeg_avcodeccontext_avoptions: AVCodecContext AVOptions options for ffmpeg
- ffmpeg_apng_encoder_avoptions: APNG encoder AVOptions options for ffmpeg
- ffmpeg_gif_encoder_avoptions: GIF encoder AVOptions options for ffmpeg
- ffmpeg_hap_encoder_avoptions: Hap encoder AVOptions options for ffmpeg
- ffmpeg_png_encoder_avoptions: PNG encoder AVOptions options for ffmpeg
- ffmpeg_prores_encoder_avoptions: ProRes encoder AVOptions options for ffmpeg
- ffmpeg_proresaw_encoder_avoptions: ProResAw encoder AVOptions options for ffmpeg
- ffmpeg_prores_encoder_avoptions: ProRes encoder AVOptions options for ffmpeg
- ffmpeg_roq_avoptions: RoQ AVOptions options for ffmpeg

Use the appropriate tool based on the user's request. Always check required parameters before calling a tool."""

    @server.prompt("debug_ffmpeg")
    async def debug_ffmpeg_prompt(error_message: str) -> str:
        """Diagnose issues with ffmpeg operations"""
        return """The user encountered an error while using ffmpeg.

Error: {{error_message}}

Available tools: ffmpeg_getting_help, ffmpeg_print_help_information_capabilities, ffmpeg_global_options_affect_whole_program_instead_of_just_one_file, ffmpeg_advanced_global_options, ffmpeg_per_file_main_options, ffmpeg_advanced_per_file_options, ffmpeg_video_options, ffmpeg_advanced_video_options, ffmpeg_audio_options, ffmpeg_advanced_audio_options, ffmpeg_subtitle_options, ffmpeg_avcodeccontext_avoptions, ffmpeg_apng_encoder_avoptions, ffmpeg_gif_encoder_avoptions, ffmpeg_hap_encoder_avoptions

Diagnose the issue and suggest which tool to use to resolve it."""

