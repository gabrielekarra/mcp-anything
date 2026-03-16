"""base_image tools for imagemagick."""

import json

from mcp.server.fastmcp import FastMCP


def register_tools(server: FastMCP, backend) -> None:
    """Register base_image tools with the server."""

    @server.tool()
    async def base_image_adaptive_blur(
        radius: str | None = "0.0",
        sigma: str | None = "0.0",
        channel: str | None = None,
    ) -> str:
        """Adaptively blurs the image by decreasing Gaussian as the operator"""
        # Direct Python call: image.adaptive_blur
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import adaptive_blur
        result = adaptive_blur(
            **({"radius": radius} if radius is not None else {}),
            **({"sigma": sigma} if sigma is not None else {}),
            **({"channel": channel} if channel is not None else {}),
        )
        return str(result)

    @server.tool()
    async def base_image_adaptive_resize(
        columns: str | None = None,
        rows: str | None = None,
    ) -> str:
        """Adaptively resize image by applying Mesh interpolation."""
        # Direct Python call: image.adaptive_resize
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import adaptive_resize
        result = adaptive_resize(
            **({"columns": columns} if columns is not None else {}),
            **({"rows": rows} if rows is not None else {}),
        )
        return str(result)

    @server.tool()
    async def base_image_adaptive_sharpen(
        radius: str | None = "0.0",
        sigma: str | None = "0.0",
        channel: str | None = None,
    ) -> str:
        """Adaptively sharpens the image by sharpening more intensely near"""
        # Direct Python call: image.adaptive_sharpen
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import adaptive_sharpen
        result = adaptive_sharpen(
            **({"radius": radius} if radius is not None else {}),
            **({"sigma": sigma} if sigma is not None else {}),
            **({"channel": channel} if channel is not None else {}),
        )
        return str(result)

    @server.tool()
    async def base_image_adaptive_threshold(
        width: str,
        height: str,
        offset: str | None = "0.0",
    ) -> str:
        """Applies threshold for each pixel based on neighboring pixel values."""
        # Direct Python call: image.adaptive_threshold
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import adaptive_threshold
        result = adaptive_threshold(
            width=width,
            height=height,
            **({"offset": offset} if offset is not None else {}),
        )
        return str(result)

    @server.tool()
    async def base_image_affine(
        sx: str | None = "1",
        rx: str | None = "0",
        ry: str | None = "0",
        sy: str | None = "1",
        tx: str | None = "0",
        ty: str | None = "0",
    ) -> str:
        """Transforms an image by applying an affine matrix."""
        # Direct Python call: image.affine
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import affine
        result = affine(
            **({"sx": sx} if sx is not None else {}),
            **({"rx": rx} if rx is not None else {}),
            **({"ry": ry} if ry is not None else {}),
            **({"sy": sy} if sy is not None else {}),
            **({"tx": tx} if tx is not None else {}),
            **({"ty": ty} if ty is not None else {}),
        )
        return str(result)

    @server.tool()
    async def base_image_alpha_channel(
    ) -> str:
        """(:class:`bool`) Get state of image alpha channel."""
        # Direct Python call: image.alpha_channel
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import alpha_channel
        result = alpha_channel(
        )
        return str(result)

    @server.tool()
    async def base_image_animation(
    ) -> str:
        """(:class:`bool`) Whether the image is animation or not."""
        # Direct Python call: image.animation
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import animation
        result = animation(
        )
        return str(result)

    @server.tool()
    async def base_image_annotate(
        text: str,
        drawing_wand: str,
        left: str | None = "0",
        baseline: str | None = "0",
        angle: str | None = "0",
    ) -> str:
        """Draws text on an image. This method differs from :meth:`caption()`"""
        # Direct Python call: image.annotate
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import annotate
        result = annotate(
            text=text,
            drawing_wand=drawing_wand,
            **({"left": left} if left is not None else {}),
            **({"baseline": baseline} if baseline is not None else {}),
            **({"angle": angle} if angle is not None else {}),
        )
        return str(result)

    @server.tool()
    async def base_image_antialias(
    ) -> str:
        """(:class:`bool`) If vectors & fonts will use anti-aliasing."""
        # Direct Python call: image.antialias
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import antialias
        result = antialias(
        )
        return str(result)

    @server.tool()
    async def base_image_auto_gamma(
    ) -> str:
        """Adjust the gamma level of an image."""
        # Direct Python call: image.auto_gamma
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import auto_gamma
        result = auto_gamma(
        )
        return str(result)

    @server.tool()
    async def base_image_auto_level(
    ) -> str:
        """Scale the minimum and maximum values to a full quantum range."""
        # Direct Python call: image.auto_level
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import auto_level
        result = auto_level(
        )
        return str(result)

    @server.tool()
    async def base_image_auto_orient(
    ) -> str:
        """Adjusts an image so that its orientation is suitable"""
        # Direct Python call: image.auto_orient
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import auto_orient
        result = auto_orient(
        )
        return str(result)

    @server.tool()
    async def base_image_auto_threshold(
        method: str | None = "kapur",
    ) -> str:
        """Automatically performs threshold method to reduce grayscale data"""
        # Direct Python call: image.auto_threshold
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import auto_threshold
        result = auto_threshold(
            **({"method": method} if method is not None else {}),
        )
        return str(result)

    @server.tool()
    async def base_image_background_color(
    ) -> str:
        """(:class:`wand.color.Color`) The image background color."""
        # Direct Python call: image.background_color
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import background_color
        result = background_color(
        )
        return str(result)

    @server.tool()
    async def base_image_bilateral_blur(
        width: str | None = "1.0",
        height: str | None = None,
        intensity: str | None = None,
        spatial: str | None = None,
    ) -> str:
        """Noise-reducing Gaussian distrbution filter. Preserves edges by"""
        # Direct Python call: image.bilateral_blur
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import bilateral_blur
        result = bilateral_blur(
            **({"width": width} if width is not None else {}),
            **({"height": height} if height is not None else {}),
            **({"intensity": intensity} if intensity is not None else {}),
            **({"spatial": spatial} if spatial is not None else {}),
        )
        return str(result)

    @server.tool()
    async def base_image_black_threshold(
        threshold: str,
    ) -> str:
        """Forces all pixels above a given color as black. Leaves pixels"""
        # Direct Python call: image.black_threshold
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import black_threshold
        result = black_threshold(
            threshold=threshold,
        )
        return str(result)

    @server.tool()
    async def base_image_blue_primary(
    ) -> str:
        """(:class:`tuple`) The chromatic blue primary point for the image."""
        # Direct Python call: image.blue_primary
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import blue_primary
        result = blue_primary(
        )
        return str(result)

    @server.tool()
    async def base_image_blue_shift(
        factor: str | None = "1.5",
    ) -> str:
        """Mutes colors of the image by shifting blue values."""
        # Direct Python call: image.blue_shift
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import blue_shift
        result = blue_shift(
            **({"factor": factor} if factor is not None else {}),
        )
        return str(result)

    @server.tool()
    async def base_image_blur(
        radius: str | None = "0.0",
        sigma: str | None = "0.0",
        channel: str | None = None,
    ) -> str:
        """Blurs the image.  Convolve the image with a gaussian operator"""
        # Direct Python call: image.blur
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import blur
        result = blur(
            **({"radius": radius} if radius is not None else {}),
            **({"sigma": sigma} if sigma is not None else {}),
            **({"channel": channel} if channel is not None else {}),
        )
        return str(result)

    @server.tool()
    async def base_image_border(
        color: str,
        width: str,
        height: str,
        compose: str | None = "copy",
    ) -> str:
        """Surrounds the image with a border."""
        # Direct Python call: image.border
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import border
        result = border(
            color=color,
            width=width,
            height=height,
            **({"compose": compose} if compose is not None else {}),
        )
        return str(result)

    @server.tool()
    async def base_image_border_color(
    ) -> str:
        """(:class:`wand.color.Color`) The image border color. Used for"""
        # Direct Python call: image.border_color
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import border_color
        result = border_color(
        )
        return str(result)

    @server.tool()
    async def base_image_brightness_contrast(
        brightness: str | None = "0.0",
        contrast: str | None = "0.0",
        channel: str | None = None,
    ) -> str:
        """Converts ``brightness`` & ``contrast`` parameters into a slope &"""
        # Direct Python call: image.brightness_contrast
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import brightness_contrast
        result = brightness_contrast(
            **({"brightness": brightness} if brightness is not None else {}),
            **({"contrast": contrast} if contrast is not None else {}),
            **({"channel": channel} if channel is not None else {}),
        )
        return str(result)

    @server.tool()
    async def base_image_canny(
        radius: str | None = "0.0",
        sigma: str | None = "1.0",
        lower_percent: str | None = "0.1",
        upper_percent: str | None = "0.3",
    ) -> str:
        """Detect edges by leveraging a multi-stage Canny algorithm."""
        # Direct Python call: image.canny
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import canny
        result = canny(
            **({"radius": radius} if radius is not None else {}),
            **({"sigma": sigma} if sigma is not None else {}),
            **({"lower_percent": lower_percent} if lower_percent is not None else {}),
            **({"upper_percent": upper_percent} if upper_percent is not None else {}),
        )
        return str(result)

    @server.tool()
    async def base_image_caption(
        text: str,
        left: str | None = "0",
        top: str | None = "0",
        width: str | None = None,
        height: str | None = None,
        font: str | None = None,
        gravity: str | None = None,
    ) -> str:
        """Writes a caption ``text`` into the position."""
        # Direct Python call: image.caption
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import caption
        result = caption(
            text=text,
            **({"left": left} if left is not None else {}),
            **({"top": top} if top is not None else {}),
            **({"width": width} if width is not None else {}),
            **({"height": height} if height is not None else {}),
            **({"font": font} if font is not None else {}),
            **({"gravity": gravity} if gravity is not None else {}),
        )
        return str(result)

    @server.tool()
    async def base_image_cdl(
        ccc: str,
    ) -> str:
        """Alias for :meth:`color_decision_list`."""
        # Direct Python call: image.cdl
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import cdl
        result = cdl(
            ccc=ccc,
        )
        return str(result)

    @server.tool()
    async def base_image_charcoal(
        radius: str,
        sigma: str,
    ) -> str:
        """Transform an image into a simulated charcoal drawing."""
        # Direct Python call: image.charcoal
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import charcoal
        result = charcoal(
            radius=radius,
            sigma=sigma,
        )
        return str(result)

    @server.tool()
    async def base_image_chop(
        width: str | None = None,
        height: str | None = None,
        x: str | None = None,
        y: str | None = None,
        gravity: str | None = None,
    ) -> str:
        """Removes a region of an image, and reduces the image size"""
        # Direct Python call: image.chop
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import chop
        result = chop(
            **({"width": width} if width is not None else {}),
            **({"height": height} if height is not None else {}),
            **({"x": x} if x is not None else {}),
            **({"y": y} if y is not None else {}),
            **({"gravity": gravity} if gravity is not None else {}),
        )
        return str(result)

    @server.tool()
    async def base_image_clahe(
        width: str,
        height: str,
        number_bins: str,
        clip_limit: str,
    ) -> str:
        """Contrast limited adaptive histogram equalization."""
        # Direct Python call: image.clahe
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import clahe
        result = clahe(
            width=width,
            height=height,
            number_bins=number_bins,
            clip_limit=clip_limit,
        )
        return str(result)

    @server.tool()
    async def base_image_clamp(
        channel: str | None = None,
    ) -> str:
        """Restrict color values between 0 and quantum range. This is useful"""
        # Direct Python call: image.clamp
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import clamp
        result = clamp(
            **({"channel": channel} if channel is not None else {}),
        )
        return str(result)

    @server.tool()
    async def base_image_clone(
    ) -> str:
        """Clones the image. It is equivalent to call :class:`Image` with"""
        # Direct Python call: image.clone
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import clone
        result = clone(
        )
        return str(result)

    @server.tool()
    async def base_image_clut(
        image: str,
        method: str | None = "undefined",
        channel: str | None = None,
    ) -> str:
        """Replace color values by referencing another image as a Color"""
        # Direct Python call: image.clut
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import clut
        result = clut(
            image=image,
            **({"method": method} if method is not None else {}),
            **({"channel": channel} if channel is not None else {}),
        )
        return str(result)

    @server.tool()
    async def base_image_coalesce(
    ) -> str:
        """Rebuilds image sequence with each frame size the same as first"""
        # Direct Python call: image.coalesce
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import coalesce
        result = coalesce(
        )
        return str(result)

    @server.tool()
    async def base_image_color_decision_list(
        ccc: str,
    ) -> str:
        """Applies color correction from a Color Correction Collection (CCC)"""
        # Direct Python call: image.color_decision_list
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import color_decision_list
        result = color_decision_list(
            ccc=ccc,
        )
        return str(result)

    @server.tool()
    async def base_image_color_map(
        index: str,
        color: str | None = None,
    ) -> str:
        """Get & Set a color at a palette index. If ``color`` is given,"""
        # Direct Python call: image.color_map
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import color_map
        result = color_map(
            index=index,
            **({"color": color} if color is not None else {}),
        )
        return str(result)

    @server.tool()
    async def base_image_color_matrix(
        matrix: str,
    ) -> str:
        """Adjust color values by applying a matrix transform per pixel."""
        # Direct Python call: image.color_matrix
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import color_matrix
        result = color_matrix(
            matrix=matrix,
        )
        return str(result)

    @server.tool()
    async def base_image_color_threshold(
        start: str | None = None,
        stop: str | None = None,
    ) -> str:
        """Forces all pixels in color range to white, and all other pixels to"""
        # Direct Python call: image.color_threshold
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import color_threshold
        result = color_threshold(
            **({"start": start} if start is not None else {}),
            **({"stop": stop} if stop is not None else {}),
        )
        return str(result)

    @server.tool()
    async def base_image_colorize(
        color: str | None = None,
        alpha: str | None = None,
    ) -> str:
        """Blends a given fill color over the image. The amount of blend is"""
        # Direct Python call: image.colorize
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import colorize
        result = colorize(
            **({"color": color} if color is not None else {}),
            **({"alpha": alpha} if alpha is not None else {}),
        )
        return str(result)

    @server.tool()
    async def base_image_colors(
    ) -> str:
        """(:class:`numbers.Integral`) Count of unique colors used within the"""
        # Direct Python call: image.colors
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import colors
        result = colors(
        )
        return str(result)

    @server.tool()
    async def base_image_colorspace(
    ) -> str:
        """(:class:`str`) The image colorspace."""
        # Direct Python call: image.colorspace
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import colorspace
        result = colorspace(
        )
        return str(result)

    @server.tool()
    async def base_image_combine(
        channel: str | None = "rgb_channels",
        colorspace: str | None = "rgb",
    ) -> str:
        """Creates an image where each color channel is assigned by a grayscale"""
        # Direct Python call: image.combine
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import combine
        result = combine(
            **({"channel": channel} if channel is not None else {}),
            **({"colorspace": colorspace} if colorspace is not None else {}),
        )
        return str(result)

    @server.tool()
    async def base_image_compare(
        image: str,
        metric: str | None = "undefined",
        highlight: str | None = None,
        lowlight: str | None = None,
    ) -> str:
        """Compares an image with another, and returns a reconstructed"""
        # Direct Python call: image.compare
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import compare
        result = compare(
            image=image,
            **({"metric": metric} if metric is not None else {}),
            **({"highlight": highlight} if highlight is not None else {}),
            **({"lowlight": lowlight} if lowlight is not None else {}),
        )
        return str(result)

    @server.tool()
    async def base_image_complex(
        operator: str | None = "undefined",
        snr: str | None = None,
    ) -> str:
        """Performs `complex`_ mathematics against two images in a sequence,"""
        # Direct Python call: image.complex
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import complex
        result = complex(
            **({"operator": operator} if operator is not None else {}),
            **({"snr": snr} if snr is not None else {}),
        )
        return str(result)

    @server.tool()
    async def base_image_compose(
    ) -> str:
        """(:class:`str`) The type of image compose."""
        # Direct Python call: image.compose
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import compose
        result = compose(
        )
        return str(result)

    @server.tool()
    async def base_image_composite(
        image: str,
        left: str | None = None,
        top: str | None = None,
        operator: str | None = "over",
        arguments: str | None = None,
        gravity: str | None = None,
    ) -> str:
        """Places the supplied ``image`` over the current image, with the top"""
        # Direct Python call: image.composite
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import composite
        result = composite(
            image=image,
            **({"left": left} if left is not None else {}),
            **({"top": top} if top is not None else {}),
            **({"operator": operator} if operator is not None else {}),
            **({"arguments": arguments} if arguments is not None else {}),
            **({"gravity": gravity} if gravity is not None else {}),
        )
        return str(result)

    @server.tool()
    async def base_image_composite_channel(
        channel: str,
        image: str,
        operator: str,
        left: str | None = None,
        top: str | None = None,
        arguments: str | None = None,
        gravity: str | None = None,
    ) -> str:
        """Composite two images using the particular ``channel``."""
        # Direct Python call: image.composite_channel
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import composite_channel
        result = composite_channel(
            channel=channel,
            image=image,
            operator=operator,
            **({"left": left} if left is not None else {}),
            **({"top": top} if top is not None else {}),
            **({"arguments": arguments} if arguments is not None else {}),
            **({"gravity": gravity} if gravity is not None else {}),
        )
        return str(result)

    @server.tool()
    async def base_image_compression(
    ) -> str:
        """(:class:`str`) The type of image compression."""
        # Direct Python call: image.compression
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import compression
        result = compression(
        )
        return str(result)

    @server.tool()
    async def base_image_compression_quality(
    ) -> str:
        """(:class:`numbers.Integral`) Compression quality of this image."""
        # Direct Python call: image.compression_quality
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import compression_quality
        result = compression_quality(
        )
        return str(result)

    @server.tool()
    async def base_image_concat(
        stacked: str | None = "False",
    ) -> str:
        """Concatenates images in stack into a single image. Left-to-right"""
        # Direct Python call: image.concat
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import concat
        result = concat(
            **({"stacked": stacked} if stacked is not None else {}),
        )
        return str(result)

    @server.tool()
    async def base_image_connected_components(
    ) -> str:
        """Evaluates binary image, and groups connected pixels into objects."""
        # Direct Python call: image.connected_components
        import sys
        from pathlib import Path
        codebase = Path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        if str(codebase) not in sys.path:
            sys.path.insert(0, str(codebase))
        from image import connected_components
        result = connected_components(
        )
        return str(result)

