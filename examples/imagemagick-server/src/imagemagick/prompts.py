"""Server-delivered MCP prompts (skills) for imagemagick."""

from mcp.server.fastmcp import FastMCP


def register_prompts(server: FastMCP) -> None:
    """Register prompts with the server."""

    @server.prompt("use_imagemagick")
    async def use_imagemagick_prompt() -> str:
        """Guide for using imagemagick tools effectively"""
        return """You have access to the imagemagick MCP server with these tools:

- allocate_ref: Allocate ref
- base_image_adaptive_blur: Adaptively blurs the image by decreasing Gaussian as the operator
- base_image_adaptive_resize: Adaptively resize image by applying Mesh interpolation.
- base_image_adaptive_sharpen: Adaptively sharpens the image by sharpening more intensely near
- base_image_adaptive_threshold: Applies threshold for each pixel based on neighboring pixel values.
- base_image_affine: Transforms an image by applying an affine matrix.
- base_image_alpha_channel: (:class:`bool`) Get state of image alpha channel.
- base_image_animation: (:class:`bool`) Whether the image is animation or not.
- base_image_annotate: Draws text on an image. This method differs from :meth:`caption()`
- base_image_antialias: (:class:`bool`) If vectors & fonts will use anti-aliasing.
- base_image_auto_gamma: Adjust the gamma level of an image.
- base_image_auto_level: Scale the minimum and maximum values to a full quantum range.
- base_image_auto_orient: Adjusts an image so that its orientation is suitable
- base_image_auto_threshold: Automatically performs threshold method to reduce grayscale data
- base_image_background_color: (:class:`wand.color.Color`) The image background color.
- base_image_bilateral_blur: Noise-reducing Gaussian distrbution filter. Preserves edges by
- base_image_black_threshold: Forces all pixels above a given color as black. Leaves pixels
- base_image_blue_primary: (:class:`tuple`) The chromatic blue primary point for the image.
- base_image_blue_shift: Mutes colors of the image by shifting blue values.
- base_image_blur: Blurs the image.  Convolve the image with a gaussian operator

Use the appropriate tool based on the user's request. Always check required parameters before calling a tool."""

    @server.prompt("debug_imagemagick")
    async def debug_imagemagick_prompt(error_message: str) -> str:
        """Diagnose issues with imagemagick operations"""
        return """The user encountered an error while using imagemagick.

Error: {{error_message}}

Available tools: allocate_ref, base_image_adaptive_blur, base_image_adaptive_resize, base_image_adaptive_sharpen, base_image_adaptive_threshold, base_image_affine, base_image_alpha_channel, base_image_animation, base_image_annotate, base_image_antialias, base_image_auto_gamma, base_image_auto_level, base_image_auto_orient, base_image_auto_threshold, base_image_background_color

Diagnose the issue and suggest which tool to use to resolve it."""

