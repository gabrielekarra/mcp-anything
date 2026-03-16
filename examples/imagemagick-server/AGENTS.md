# imagemagick MCP Server

MCP server for imagemagick (with 50 capabilities)

## Available Tools

### allocate_ref

Allocate ref

Parameters:
- `addr` (string): 
- `deallocator` (string): 
### base_image_adaptive_blur

Adaptively blurs the image by decreasing Gaussian as the operator

Parameters:
- `radius` (string, optional): size of gaussian aperture. (default: 0.0)
- `sigma` (string, optional): Standard deviation of the gaussian filter. (default: 0.0)
- `channel` (string, optional): Apply the blur effect on a specific channel.
### base_image_adaptive_resize

Adaptively resize image by applying Mesh interpolation.

Parameters:
- `columns` (string, optional): width of resized image.
- `rows` (string, optional): height of resized image.
### base_image_adaptive_sharpen

Adaptively sharpens the image by sharpening more intensely near

Parameters:
- `radius` (string, optional): size of gaussian aperture. (default: 0.0)
- `sigma` (string, optional): Standard deviation of the gaussian filter. (default: 0.0)
- `channel` (string, optional): Apply the sharpen effect on a specific channel.
### base_image_adaptive_threshold

Applies threshold for each pixel based on neighboring pixel values.

Parameters:
- `width` (string): size of neighboring pixels on the X-axis.
- `height` (string): size of neighboring pixels on the Y-axis.
- `offset` (string, optional): normalized number between `0.0` and (default: 0.0)
### base_image_affine

Transforms an image by applying an affine matrix.

Parameters:
- `sx` (string, optional): Horizontal scale/shear. Default value `1.0` (default: 1)
- `rx` (string, optional): Horizontal rotation. Default value `0.0` (default: 0)
- `ry` (string, optional): Vertical rotation. Default value `0.0` (default: 0)
- `sy` (string, optional): Vertical scale/shear. Default value `1.0` (default: 1)
- `tx` (string, optional): Horizontal translation. Default value `0.0` (default: 0)
- `ty` (string, optional): Vertical translation. Default value `0.0` (default: 0)
### base_image_alpha_channel

(:class:`bool`) Get state of image alpha channel.

### base_image_animation

(:class:`bool`) Whether the image is animation or not.

### base_image_annotate

Draws text on an image. This method differs from :meth:`caption()`

Parameters:
- `text` (string): String to annotate on image.
- `drawing_wand` (string): Font configuration & style context.
- `left` (string, optional): X-axis offset of the text baseline. (default: 0)
- `baseline` (string, optional): Y-axis offset of the bottom of the text. (default: 0)
- `angle` (string, optional): Degree rotation to draw text at. (default: 0)
### base_image_antialias

(:class:`bool`) If vectors & fonts will use anti-aliasing.

### base_image_auto_gamma

Adjust the gamma level of an image.

### base_image_auto_level

Scale the minimum and maximum values to a full quantum range.

### base_image_auto_orient

Adjusts an image so that its orientation is suitable

### base_image_auto_threshold

Automatically performs threshold method to reduce grayscale data

Parameters:
- `method` (string, optional): Which threshold method to apply. (default: kapur)
### base_image_background_color

(:class:`wand.color.Color`) The image background color.

### base_image_bilateral_blur

Noise-reducing Gaussian distrbution filter. Preserves edges by

Parameters:
- `width` (string, optional): The neighboring pixel area width. (default: 1.0)
- `height` (string, optional): The neighboring pixel area height. Default the given
- `intensity` (string, optional): Influence the distance between colors values.
- `spatial` (string, optional): Influence the coordinate distance weights.
### base_image_black_threshold

Forces all pixels above a given color as black. Leaves pixels

Parameters:
- `threshold` (string): Color to be referenced as a threshold.
### base_image_blue_primary

(:class:`tuple`) The chromatic blue primary point for the image.

### base_image_blue_shift

Mutes colors of the image by shifting blue values.

Parameters:
- `factor` (string, optional): Amount to adjust values. (default: 1.5)
### base_image_blur

Blurs the image.  Convolve the image with a gaussian operator

Parameters:
- `radius` (string, optional): the radius of the, in pixels, (default: 0.0)
- `sigma` (string, optional): the standard deviation of the, in pixels. Default value (default: 0.0)
- `channel` (string, optional): Optional color channel to apply blur. See
### base_image_border

Surrounds the image with a border.

Parameters:
- `color` (string): 
- `width` (string): the border width
- `height` (string): the border height
- `compose` (string, optional): Use composite operator when applying frame. Only used (default: copy)
### base_image_border_color

(:class:`wand.color.Color`) The image border color. Used for

### base_image_brightness_contrast

Converts ``brightness`` & ``contrast`` parameters into a slope &

Parameters:
- `brightness` (string, optional): between ``-100.0`` and ``100.0``. Default is ``0.0`` (default: 0.0)
- `contrast` (string, optional): between ``-100.0`` and ``100.0``. Default is ``0.0`` (default: 0.0)
- `channel` (string, optional): Isolate a single color channel to apply contrast.
### base_image_canny

Detect edges by leveraging a multi-stage Canny algorithm.

Parameters:
- `radius` (string, optional): Size of gaussian filter. (default: 0.0)
- `sigma` (string, optional): Standard deviation of gaussian filter. (default: 1.0)
- `lower_percent` (string, optional): Normalized lower threshold. Values between (default: 0.1)
- `upper_percent` (string, optional): Normalized upper threshold. Values between (default: 0.3)
### base_image_caption

Writes a caption ``text`` into the position.

Parameters:
- `text` (string): text to write
- `left` (string, optional): x offset in pixels (default: 0)
- `top` (string, optional): y offset in pixels (default: 0)
- `width` (string, optional): width of caption in pixels.
- `height` (string, optional): height of caption in pixels.
- `font` (string, optional): font to use.  default is :attr:`font` of the image
- `gravity` (string, optional): text placement gravity.
### base_image_cdl

Alias for :meth:`color_decision_list`.

Parameters:
- `ccc` (string): 
### base_image_charcoal

Transform an image into a simulated charcoal drawing.

Parameters:
- `radius` (string): The size of the Gaussian operator.
- `sigma` (string): The standard deviation of the Gaussian.
### base_image_chop

Removes a region of an image, and reduces the image size

Parameters:
- `width` (string, optional): Size of region.
- `height` (string, optional): Size of region.
- `x` (string, optional): Offset on the X-axis.
- `y` (string, optional): Offset on the Y-axis.
- `gravity` (string, optional): Helper to auto-calculate offset.
### base_image_clahe

Contrast limited adaptive histogram equalization.

Parameters:
- `width` (string): Tile division width.
- `height` (string): Tile division height.
- `number_bins` (string): Histogram bins.
- `clip_limit` (string): contrast limit.
### base_image_clamp

Restrict color values between 0 and quantum range. This is useful

Parameters:
- `channel` (string, optional): Optional color channel.
### base_image_clone

Clones the image. It is equivalent to call :class:`Image` with

### base_image_clut

Replace color values by referencing another image as a Color

Parameters:
- `image` (string): Color Look Up Table image.
- `method` (string, optional): Pixel Interpolate method. Only available with (default: undefined)
- `channel` (string, optional): Optional color channel to target. See
### base_image_coalesce

Rebuilds image sequence with each frame size the same as first

### base_image_color_decision_list

Applies color correction from a Color Correction Collection (CCC)

Parameters:
- `ccc` (string): A XML string of the CCC contents.
### base_image_color_map

Get & Set a color at a palette index. If ``color`` is given,

Parameters:
- `index` (string): The color position of the image palette.
- `color` (string, optional): Optional color to _set_ at the given index.
### base_image_color_matrix

Adjust color values by applying a matrix transform per pixel.

Parameters:
- `matrix` (string): 2D List of doubles.
### base_image_color_threshold

Forces all pixels in color range to white, and all other pixels to

Parameters:
- `start` (string, optional): Color to begin color range.
- `stop` (string, optional): Color to end color range.
### base_image_colorize

Blends a given fill color over the image. The amount of blend is

Parameters:
- `color` (string, optional): Color to paint image with.
- `alpha` (string, optional): Defines how to blend color.
### base_image_colors

(:class:`numbers.Integral`) Count of unique colors used within the

### base_image_colorspace

(:class:`str`) The image colorspace.

### base_image_combine

Creates an image where each color channel is assigned by a grayscale

Parameters:
- `channel` (string, optional): Determines the colorchannel ordering of the (default: rgb_channels)
- `colorspace` (string, optional): Determines the colorchannel ordering of the (default: rgb)
### base_image_compare

Compares an image with another, and returns a reconstructed

Parameters:
- `image` (string): The reference image
- `metric` (string, optional): The metric type to use for comparing. See (default: undefined)
- `highlight` (string, optional): Set the color of the delta pixels in the resulting
- `lowlight` (string, optional): Set the color of the similar pixels in the resulting
### base_image_complex

Performs `complex`_ mathematics against two images in a sequence,

Parameters:
- `operator` (string, optional): Define which mathematic operator to perform. See (default: undefined)
- `snr` (string, optional): Optional ``SNR`` parameter for ``'divide'`` operator.
### base_image_compose

(:class:`str`) The type of image compose.

### base_image_composite

Places the supplied ``image`` over the current image, with the top

Parameters:
- `image` (string): the image placed over the current image
- `left` (string, optional): the x-coordinate where `image` will be placed
- `top` (string, optional): the y-coordinate where `image` will be placed
- `operator` (string, optional): the operator that affects how the composite (default: over)
- `arguments` (string, optional): Additional numbers given as a geometry string, or
- `gravity` (string, optional): Calculate the ``top`` & ``left`` values based on
### base_image_composite_channel

Composite two images using the particular ``channel``.

Parameters:
- `channel` (string): the channel type.  available values can be found
- `image` (string): the composited source image.
- `operator` (string): the operator that affects how the composite
- `left` (string, optional): the column offset of the composited source image
- `top` (string, optional): the row offset of the composited source image
- `arguments` (string, optional): Additional numbers given as a geometry string, or
- `gravity` (string, optional): Calculate the ``top`` & ``left`` values based on
### base_image_compression

(:class:`str`) The type of image compression.

### base_image_compression_quality

(:class:`numbers.Integral`) Compression quality of this image.

### base_image_concat

Concatenates images in stack into a single image. Left-to-right

Parameters:
- `stacked` (string, optional): stack images in a column, or in a row (default) (default: False)
### base_image_connected_components

Evaluates binary image, and groups connected pixels into objects.


## Available Resources

- `app://imagemagick/status` — Current status and version of imagemagick
- `app://imagemagick/commands` — Available commands and tools in imagemagick
- `docs://imagemagick/tool-index` — Complete index of all imagemagick tools with parameters and usage
- `docs://imagemagick/base_image` — Documentation for imagemagick base_image capabilities

## Available Prompts

- `use_imagemagick` — Guide for using imagemagick tools effectively
- `debug_imagemagick` — Diagnose issues with imagemagick operations

## Usage

This server runs over stdio. Add it to your MCP client config:

```json
{
  "mcpServers": {
    "imagemagick": {
      "command": "mcp-imagemagick"
    }
  }
}
```
