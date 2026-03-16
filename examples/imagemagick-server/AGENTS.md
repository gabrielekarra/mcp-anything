# imagemagick MCP Server

MCP server for imagemagick (with 200 capabilities)

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

### base_image_contrast

Enhances the difference between lighter & darker values of the

Parameters:
- `sharpen` (string, optional): Increase, or decrease, contrast. Default is ``True`` (default: True)
### base_image_contrast_stretch

Enhance contrast of image by adjusting the span of the available

Parameters:
- `black_point` (string, optional): black point between 0.0 and 1.0.  default is 0.0 (default: 0.0)
- `white_point` (string, optional): white point between 0.0 and 1.0.
- `channel` (string, optional): optional color channel to apply contrast stretch
### base_image_convex_hull

Find the smallest convex polygon, and returns a list of points.

Parameters:
- `background` (string, optional): Define which color value to evaluate as the
### base_image_cycle_color_map

Shift the image color-map by a given offset.

Parameters:
- `offset` (string, optional): number of steps to rotate index by. (default: 1)
### base_image_decipher

Decrypt ciphered pixels into original values.

Parameters:
- `passphrase` (string): the secret passphrase to decrypt with.
### base_image_deconstruct

Iterates over internal image stack, and adjust each frame size to

### base_image_delay

(:class:`numbers.Integral`) The number of ticks between frames.

### base_image_depth

(:class:`numbers.Integral`) The depth of this image.

### base_image_deskew

Attempts to remove skew artifacts common with most

Parameters:
- `threshold` (string): 
### base_image_despeckle

Applies filter to reduce noise in image.

### base_image_dispose

(:class:`str`) Controls how the image data is

### base_image_distort

Distorts an image using various distorting methods.

Parameters:
- `method` (string): Distortion method name from :const:`DISTORTION_METHODS`
- `arguments` (string): List of distorting float arguments
- `best_fit` (string, optional): Attempt to resize resulting image fit distortion. (default: False)
- `filter` (string, optional): Optional resampling filter used when calculating
### base_image_edge

Applies convolution filter to detect edges.

Parameters:
- `radius` (string, optional): aperture of detection filter. (default: 0.0)
### base_image_emboss

Applies convolution filter against Gaussians filter.

Parameters:
- `radius` (string, optional): filter aperture size. (default: 0.0)
- `sigma` (string, optional): standard deviation. (default: 0.0)
### base_image_encipher

Encrypt plain pixels into ciphered values.

Parameters:
- `passphrase` (string): the secret passphrase to encrypt with.
### base_image_enhance

Applies digital filter to reduce noise.

### base_image_equalize

Equalizes the image histogram

Parameters:
- `channel` (string, optional): Optional channel. See :const:`CHANNELS`.
### base_image_evaluate

Apply arithmetic, relational, or logical expression to an image.

Parameters:
- `operator` (string, optional): Type of operation to calculate
- `value` (string, optional): Number to calculate with ``operator`` (default: 0.0)
- `channel` (string, optional): Optional channel to apply operation on.
### base_image_evaluate_images

Create a new image by applying arithmetic operation between all

Parameters:
- `operator` (string, optional): Type of operation to calculate.
### base_image_export_pixels

Export pixel data from a raster image to

Parameters:
- `x` (string, optional): horizontal starting coordinate of raster. (default: 0)
- `y` (string, optional): vertical starting coordinate of raster. (default: 0)
- `width` (string, optional): horizontal length of raster.
- `height` (string, optional): vertical length of raster.
- `channel_map` (string, optional): a string listing the channel data (default: RGBA)
- `storage` (string, optional): what data type each value should (default: char)
### base_image_extent

Adjust the canvas size of the image. Use ``x`` & ``y`` to offset

Parameters:
- `width` (string, optional): the target width of the extended image.
- `height` (string, optional): the target height of the extended image.
- `x` (string, optional): the x-axis offset of the extended image.
- `y` (string, optional): the :attr:`y` offset of the extended image.
- `gravity` (string, optional): position of the item extent when not using ``x`` &
### base_image_fft

Alias for :meth:`forward_fourier_transform`.

Parameters:
- `magnitude` (string, optional):  (default: True)
### base_image_flip

Creates a vertical mirror image by reflecting the pixels around

### base_image_floodfill

Changes pixel value to ``fill`` color at (``x``, ``y``) coordinate,

Parameters:
- `fill` (string, optional): New target color value. (default: none)
- `fuzz` (string, optional): Fill threashold. Values between `0.0` and `1.0`. Default (default: 0.1)
- `bordercolor` (string, optional): Optional color to use as a border. Default
- `x` (string, optional): Starting point X coordinate. Default ``0``. (default: 0)
- `y` (string, optional): Starting point Y coordinate. Default ``0``. (default: 0)
- `invert` (string, optional): Only paint none-matching pixels. Default ``False``. (default: False)
- `channel` (string, optional): Optional channel mask. Default ``'default_channels'``. (default: default_channels)
### base_image_flop

Creates a horizontal mirror image by reflecting the pixels around

### base_image_font

(:class:`wand.font.Font`) The current font options.

### base_image_font_antialias

.. deprecated:: 0.5.0

### base_image_font_color

Font color

### base_image_font_path

(:class:`str`) The path of the current font.

### base_image_font_size

(:class:`numbers.Real`) The font size.  It also can be set.

### base_image_format

(:class:`str`) The image format.

### base_image_forward_fourier_transform

Performs a discrete Fourier transform. The image stack is replaced

Parameters:
- `magnitude` (string, optional): If ``True``, generate magnitude & phase, else (default: True)
### base_image_frame

Creates a bordered frame around image.

Parameters:
- `matte` (string, optional): color of the frame
- `width` (string, optional): total size of frame on x-axis (default: 1)
- `height` (string, optional): total size of frame on y-axis (default: 1)
- `inner_bevel` (string, optional): inset shadow length (default: 0)
- `outer_bevel` (string, optional): outset highlight length (default: 0)
- `compose` (string, optional): Optional composite operator. Default ``'over'``, and (default: over)
### base_image_function

Apply an arithmetic, relational, or logical expression to an image.

Parameters:
- `function` (string): a string listed in :const:`FUNCTION_TYPES`
- `arguments` (string): a sequence of doubles to apply against ``function``
- `channel` (string, optional): optional :const:`CHANNELS`, defaults all
### base_image_fuzz

(:class:`numbers.Real`) The normalized real number between ``0.0``

### base_image_fx

Manipulate each pixel of an image by given expression.

Parameters:
- `expression` (string): The entire FX expression to apply
- `channel` (string, optional): Optional channel to target.
### base_image_gamma

Gamma correct image.

Parameters:
- `adjustment_value` (string, optional): value to adjust gamma level. Default `1.0` (default: 1.0)
- `channel` (string, optional): optional channel to apply gamma correction
### base_image_gaussian_blur

Blurs the image.  We convolve the image with a gaussian operator

Parameters:
- `radius` (string, optional): the radius of the, in pixels, (default: 0.0)
- `sigma` (string, optional): the standard deviation of the, in pixels (default: 0.0)
- `channel` (string, optional): Optional color channel to target. See
### base_image_get_image_distortion

Compares two images, and return the specified distortion metric.

Parameters:
- `image` (string): Image to reference.
- `metric` (string, optional): Compare disortion metric to use. See (default: undefined)
### base_image_gravity

(:class:`str`) The text placement gravity used when

### base_image_green_primary

(:class:`tuple`) The chromatic green primary point for the image.

### base_image_hald_clut

Replace color values by referencing a Higher And Lower Dimension

Parameters:
- `image` (string): The HALD color matrix.
- `channel` (string, optional): Optional color channel to target. See
### base_image_height

(:class:`numbers.Integral`) The height of this image.

### base_image_histogram

(:class:`HistogramDict`) The mapping that represents the histogram.

### base_image_hough_lines

Identify lines within an image. Use :meth:`canny` to reduce image

Parameters:
- `width` (string): Local maxima of neighboring pixels.
- `height` (string, optional): Local maxima of neighboring pixels.
- `threshold` (string, optional): Line count to limit. Default to 40. (default: 40)
### base_image_ift

Alias for :meth:`inverse_fourier_transform`.

Parameters:
- `phase` (string): 
- `magnitude` (string, optional):  (default: True)
### base_image_implode

Creates a "imploding" effect by pulling pixels towards the center

Parameters:
- `amount` (string, optional): Normalized degree of effect between `0.0` & `1.0`. (default: 0.0)
- `method` (string, optional): Which interpolate method to apply to effected pixels. (default: undefined)
### base_image_import_pixels

Import pixel data from a byte-string to

Parameters:
- `x` (string, optional): horizontal starting coordinate of raster. (default: 0)
- `y` (string, optional): vertical starting coordinate of raster. (default: 0)
- `width` (string, optional): horizontal length of raster.
- `height` (string, optional): vertical length of raster.
- `channel_map` (string, optional): a string listing the channel data (default: RGB)
- `storage` (string, optional): what data type each value should (default: char)
- `data` (string, optional): 
### base_image_interlace_scheme

(:class:`str`) The interlace used by the image.

### base_image_interpolate_method

(:class:`str`) The interpolation method of the image.

### base_image_inverse_fourier_transform

Applies the inverse of a discrete Fourier transform. The image stack

Parameters:
- `phase` (string): Second part (image) of the transform. Either the phase,
- `magnitude` (string, optional): If ``True``, accept magnitude & phase input, else (default: True)
### base_image_iterator_first

Sets the internal image-stack iterator to the first image.

### base_image_iterator_get

Returns the position of the internal image-stack index.

### base_image_iterator_last

Sets the internal image-stack iterator to the last image.

### base_image_iterator_length

Get the count of images in the image-stack.

### base_image_iterator_next

Steps the image-stack index forward by one

### base_image_iterator_previous

Steps the image-stack index back by one.

### base_image_iterator_reset

Reset internal image-stack iterator. Useful for iterating over the

### base_image_iterator_set

Sets the index of the internal image-stack.

Parameters:
- `index` (string): 
### base_image_kmeans

Reduces the number of colors in an image by applying the K-means

Parameters:
- `number_colors` (string, optional): the target number of colors to use as seeds.
- `max_iterations` (string, optional): maximum number of iterations needed until (default: 100)
- `tolerance` (string, optional): maximum tolerance between distrotion iterations. (default: 0.01)
### base_image_kurtosis

(:class:`numbers.Real`) The kurtosis of the image.

### base_image_kurtosis_channel

Calculates the kurtosis and skewness of the image.

Parameters:
- `channel` (string, optional): Select which color channel to evaluate. See (default: default_channels)
### base_image_kuwahara

Edge preserving noise reduction filter.

Parameters:
- `radius` (string, optional): Size of the filter aperture. (default: 1.0)
- `sigma` (string, optional): Standard deviation of Gaussian filter.
### base_image_label

Writes a label ``text`` into the position on top of the existing

Parameters:
- `text` (string): text to write.
- `left` (string, optional): x offset in pixels.
- `top` (string, optional): y offset in pixels.
- `font` (string, optional): font to use.  default is :attr:`font` of the image.
- `gravity` (string, optional): text placement gravity.
- `background_color` (string, optional):  (default: transparent)
### base_image_length_of_bytes

(:class:`numbers.Integral`) The original size, in bytes,

### base_image_level

Adjusts the levels of an image by scaling the colors falling

Parameters:
- `black` (string, optional): Black point, as a percentage of the system's quantum (default: 0.0)
- `white` (string, optional): White point, as a percentage of the system's quantum
- `gamma` (string, optional): Optional gamma adjustment. Values > 1.0 lighten the (default: 1.0)
- `channel` (string, optional): The channel type. Available values can be found
### base_image_level_colors

Maps given colors to "black" & "white" values.

Parameters:
- `black_color` (string): linearly map given color as "black" point.
- `white_color` (string): linearly map given color as "white" point.
- `channel` (string, optional): target a specific color-channel to levelize.
### base_image_levelize

Reverse of :meth:`level()`, this method compresses the range of

Parameters:
- `black` (string, optional): Black point, as a percentage of the system's quantum (default: 0.0)
- `white` (string, optional): White point, as a percentage of the system's quantum
- `gamma` (string, optional): Optional gamma adjustment. Values > 1.0 lighten the (default: 1.0)
- `channel` (string, optional): The channel type. Available values can be found
### base_image_levelize_colors

Reverse of :meth:`level_colors()`, and creates a de-contrasting

Parameters:
- `black_color` (string): tint map given color as "black" point.
- `white_color` (string): tint map given color as "white" point.
- `channel` (string, optional): target a specific color-channel to levelize.
### base_image_linear_stretch

Enhance saturation intensity of an image.

Parameters:
- `black_point` (string, optional): Black point between 0.0 and 1.0. Default 0.0 (default: 0.0)
- `white_point` (string, optional): White point between 0.0 and 1.0. Default 1.0 (default: 1.0)
### base_image_liquid_rescale

Rescales the image with `seam carving`_, also known as

Parameters:
- `width` (string): the width in the scaled image
- `height` (string): the height in the scaled image
- `delta_x` (string, optional): maximum seam transversal step. (default: 1)
- `rigidity` (string, optional): introduce a bias for non-straight seams. (default: 0)
### base_image_local_contrast

Increase light-dark transitions within image.

Parameters:
- `radius` (string, optional): The size of the Gaussian operator. Default value is (default: 10)
- `strength` (string, optional): Percentage of blur mask to apply. Values can be (default: 12.5)
### base_image_loop

(:class:`numbers.Integral`) Number of frame iterations.

### base_image_magnify

Quickly double an image in size. This is a convenience method.

### base_image_matte_color

(:class:`wand.color.Color`) The color value of the matte channel.

### base_image_maxima

(:class:`numbers.Real`) The maximum quantum value within the image.

### base_image_mean

(:class:`numbers.Real`) The mean of the image, and have a value

### base_image_mean_channel

Calculates the mean and standard deviation of the image.

Parameters:
- `channel` (string, optional): Select which color channel to evaluate. See (default: default_channels)
### base_image_mean_shift

Recalculates pixel value by comparing neighboring pixels within a

Parameters:
- `width` (string): Size of the neighborhood window in pixels.
- `height` (string): Size of the neighborhood window in pixels.
- `color_distance` (string, optional): Include pixel values within this color distance. (default: 0.1)
### base_image_merge_layers

Composes all the image layers from the current given image onward

Parameters:
- `method` (string): the method of selecting the size of the initial canvas.
### base_image_minima

(:class:`numbers.Real`) The minimum quantum value within the image.

### base_image_minimum_bounding_box

Find the minimum bounding box within the image. Use

Parameters:
- `orientation` (string, optional): sets the image orientation. Values can be
### base_image_mode

Replace each pixel with the mathematical mode of the neighboring

Parameters:
- `width` (string): Number of neighboring pixels to include in mode.
- `height` (string, optional): Optional height of neighboring pixels, defaults to the
### base_image_modulate

Changes the brightness, saturation and hue of an image.

Parameters:
- `brightness` (string, optional): percentage of brightness (default: 100.0)
- `saturation` (string, optional): percentage of saturation (default: 100.0)
- `hue` (string, optional): percentage of hue rotation (default: 100.0)
### base_image_morphology

Manipulate pixels based on the shape of neighboring pixels.

Parameters:
- `method` (string, optional): effect function to apply. See
- `kernel` (string, optional): shape to evaluate surrounding pixels. See
- `iterations` (string, optional): Number of times a morphology method should be (default: 1)
- `channel` (string, optional): Optional color channel to target. See
### base_image_motion_blur

Apply a Gaussian blur along an ``angle`` direction. This

Parameters:
- `radius` (string, optional): Aperture size of the Gaussian operator. (default: 0.0)
- `sigma` (string, optional): Standard deviation of the Gaussian operator. (default: 0.0)
- `angle` (string, optional): Apply the effect along this angle. (default: 0.0)
- `channel` (string, optional): 
### base_image_negate

Negate the colors in the reference image.

Parameters:
- `grayscale` (string, optional): if set, only negate grayscale pixels in the image. (default: False)
- `channel` (string, optional): the channel type.  available values can be found
### base_image_noise

Adds noise to image.

Parameters:
- `noise_type` (string, optional): type of noise to apply. See :const:`NOISE_TYPES`. (default: uniform)
- `attenuate` (string, optional): rate of distribution. Only available in (default: 1.0)
- `channel` (string, optional): Optionally target a color channel to apply noise to.
### base_image_normalize

Normalize color channels.

Parameters:
- `channel` (string, optional): the channel type.  available values can be found
### base_image_oil_paint

Simulates an oil painting by replace each pixel with most frequent

Parameters:
- `radius` (string, optional): The size of the surrounding neighbors. (default: 0.0)
- `sigma` (string, optional): The standard deviation used by the Gaussian operator. (default: 0.0)
### base_image_opaque_paint

Replace any color that matches ``target`` with ``fill``. Use

Parameters:
- `target` (string, optional): The color to match.
- `fill` (string, optional): The color to paint with.
- `fuzz` (string, optional): Normalized real number between `0.0` and (default: 0.0)
- `invert` (string, optional): Replace all colors that do not match target. (default: False)
- `channel` (string, optional): Optional color channel to target. See
### base_image_optimize_layers

Attempts to crop each frame to the smallest image without altering

### base_image_optimize_transparency

Iterates over frames, and sets transparent values for each

### base_image_ordered_dither

Executes a ordered-based dither operations based on predetermined

Parameters:
- `threshold_map` (string, optional): Name of threshold dither to use, followed by (default: threshold)
- `channel` (string, optional): Optional argument to apply dither to specific color
### base_image_orientation

(:class:`str`) The image orientation.  It's a string from

### base_image_page

The dimensions and offset of this Wand's page as a 4-tuple:

### base_image_page_height

(:class:`numbers.Integral`) The height of the page for this wand.

### base_image_page_width

(:class:`numbers.Integral`) The width of the page for this wand.

### base_image_page_x

(:class:`numbers.Integral`) The X-offset of the page for this wand.

### base_image_page_y

(:class:`numbers.Integral`) The Y-offset of the page for this wand.

### base_image_parse_meta_geometry

Helper method to translate geometry format, and calculate

Parameters:
- `geometry` (string): user string following ImageMagick's geometry format.
### base_image_percent_escape

Convenience method that expands ImageMagick's `Percent Escape`_

Parameters:
- `string_format` (string): The precent escaped string to be translated.
### base_image_polaroid

Creates a special effect simulating a Polaroid photo.

Parameters:
- `angle` (string, optional): applies a shadow effect along this angle. (default: 0.0)
- `caption` (string, optional): Writes a message at the bottom of the photo's border.
- `font` (string, optional): Specify font style.
- `method` (string, optional): Interpolation method. ImageMagick-7 only. (default: undefined)
### base_image_polynomial

Replace image with the sum of all images in a sequence by

Parameters:
- `arguments` (string): A list of real numbers where at least two numbers
### base_image_posterize

Reduce color levels per channel.

Parameters:
- `levels` (string, optional): Number of levels per channel.
- `dither` (string, optional): Dither method to apply. (default: no)
### base_image_quantize

`quantize` analyzes the colors within a sequence of images and

Parameters:
- `number_colors` (string): The target number of colors to reduce the image.
- `colorspace_type` (string, optional): Available value can be found (default: undefined)
- `treedepth` (string, optional): A value between ``0`` & ``8`` where ``0`` will (default: 0)
- `dither` (string, optional): Perform dither operation between neighboring pixel (default: False)
- `measure_error` (string, optional): Include total quantization error of all pixels (default: False)
### base_image_quantum_range

(`:class:`numbers.Integral`) The maximum value of a color

### base_image_random_threshold

Performs a random dither to force a pixel into a binary black &

Parameters:
- `low` (string, optional): bottom threshold. Any pixel value below the given value (default: 0.0)
- `high` (string, optional): top threshold. Any pixel value above the given value (default: 1.0)
- `channel` (string, optional): Optional argument to apply dither to specific color
### base_image_range_channel

Calculate the minimum and maximum of quantum values in image.

Parameters:
- `channel` (string, optional): Select which color channel to evaluate. See (default: default_channels)
### base_image_range_threshold

Applies soft & hard thresholding.

Parameters:
- `low_black` (string, optional): Define the minimum threshold value. (default: 0.0)
- `low_white` (string, optional): Define the minimum threshold value.
- `high_white` (string, optional): Define the maximum threshold value.
- `high_black` (string, optional): Define the maximum threshold value.
### base_image_read_mask

Sets the read mask where the gray values of the clip mask

Parameters:
- `clip_mask` (string, optional): Image to reference as blend mask.
### base_image_red_primary

(:class:`tuple`) The chromatic red primary point for the image.

### base_image_region

Extract an area of the image. This is the same as :meth:`crop`,

Parameters:
- `width` (string, optional): Area size on the X-axis. Default value is
- `height` (string, optional): Area size on the  Y-axis.Default value is
- `x` (string, optional): X-axis offset. This number can be negative. Default value is
- `y` (string, optional): Y-axis offset. This number can be negative. Default value is
- `gravity` (string, optional): 
### base_image_remap

Rebuild image palette with closest color from given affinity image.

Parameters:
- `affinity` (string, optional): reference image.
- `method` (string, optional): dither method. See :const:`DITHER_METHODS`. (default: no)
### base_image_rendering_intent

(:class:`str`) PNG rendering intent. See

### base_image_resample

Adjust the number of pixels in an image so that when displayed at

Parameters:
- `x_res` (string, optional): the X resolution (density) in the scaled image. default
- `y_res` (string, optional): the Y resolution (density) in the scaled image. default
- `filter` (string, optional): a filter type to use for resizing. choose one in (default: undefined)
- `blur` (string, optional): the blur factor where > 1 is blurry, < 1 is sharp. (default: 1)
### base_image_reset_coords

Reset the coordinate frame of the image so to the upper-left corner

### base_image_reset_sequence

Abstract method prototype.

### base_image_resize

Resizes the image.

Parameters:
- `width` (string, optional): the width in the scaled image. default is the original
- `height` (string, optional): the height in the scaled image. default is the original
- `filter` (string, optional): a filter type to use for resizing. choose one in (default: undefined)
- `blur` (string, optional): the blur factor where > 1 is blurry, < 1 is sharp. (default: 1)
### base_image_resolution

(:class:`tuple`) Resolution of this image.

### base_image_roll

Shifts all pixels over by an X/Y offset.

Parameters:
- `x` (string, optional): Number of columns to roll over. Negative value will roll (default: 0)
- `y` (string, optional): Number of rows to roll over. Negative value will roll (default: 0)
### base_image_rotate

Rotates the image right.  It takes a ``background`` color

Parameters:
- `degree` (string): a degree to rotate. multiples of 360 affect nothing
- `background` (string, optional): an optional background color.
- `reset_coords` (string, optional): optional flag. If set, after the rotation, the (default: True)
### base_image_rotational_blur

Blur an image in a radius around the center of an image.

Parameters:
- `angle` (string, optional): Degrees of rotation to blur with. (default: 0.0)
- `channel` (string, optional): Optional channel to apply the effect against. See
### base_image_sample

Resizes the image by sampling the pixels.  It's basically quicker

Parameters:
- `width` (string, optional): the width in the scaled image. default is the original
- `height` (string, optional): the height in the scaled image. default is the original
### base_image_sampling_factors

(:class:`tuple`) Factors used in sampling data streams.

### base_image_scale

Increase image size by scaling each pixel value by given ``columns``

Parameters:
- `columns` (string, optional): The number of columns, in pixels, to scale the image (default: 1)
- `rows` (string, optional): The number of rows, in pixels, to scale the image (default: 1)
### base_image_scene

(:class:`numbers.Integral`) The scene number of the current frame

### base_image_seed

(:class:`numbers.Integral`) The seed for random number generator.

### base_image_selective_blur

Blur an image within a given threshold.

Parameters:
- `radius` (string, optional): Size of gaussian aperture. (default: 0.0)
- `sigma` (string, optional): Standard deviation of gaussian operator. (default: 0.0)
- `threshold` (string, optional): Only pixels within contrast threshold are effected. (default: 0.0)
- `channel` (string, optional): Optional color channel to target. See
### base_image_sepia_tone

Creates a Sepia Tone special effect similar to a darkroom chemical

Parameters:
- `threshold` (string, optional): The extent of the toning. Value can be between ``0`` (default: 0.8)
### base_image_shade

Creates a 3D effect by simulating a light from an

Parameters:
- `gray` (string, optional): Isolate the effect on pixel intensity. (default: False)
- `azimuth` (string, optional): Angle from x-axis. (default: 0.0)
- `elevation` (string, optional): Amount of pixels from the z-axis. (default: 0.0)
### base_image_shadow

Generates an image shadow.

Parameters:
- `alpha` (string, optional): Ratio of transparency. (default: 0.0)
- `sigma` (string, optional): Standard deviation of the gaussian filter. (default: 0.0)
- `x` (string, optional): x-offset. (default: 0)
- `y` (string, optional): y-offset. (default: 0)
### base_image_sharpen

Applies a gaussian effect to enhance the sharpness of an

Parameters:
- `radius` (string, optional): size of gaussian aperture. (default: 0.0)
- `sigma` (string, optional): Standard deviation of the gaussian filter. (default: 0.0)
- `channel` (string, optional): Optional color channel to target. See
### base_image_shave

Remove pixels from the edges.

Parameters:
- `columns` (string, optional): amount to shave off both sides of the x-axis. (default: 0)
- `rows` (string, optional): amount to shave off both sides of the y-axis. (default: 0)
### base_image_shear

Shears the image to create a parallelogram, and fill the space

Parameters:
- `background` (string, optional): Color to fill the void created by shearing the (default: WHITE)
- `x` (string, optional): Slide the image along the X-axis. (default: 0.0)
- `y` (string, optional): Slide the image along the Y-axis. (default: 0.0)
### base_image_sigmoidal_contrast

Modifies the contrast of the image by applying non-linear sigmoidal

Parameters:
- `sharpen` (string, optional): Increase the contrast when ``True`` (default), else (default: True)
- `strength` (string, optional): How much to adjust the contrast. Where a value of (default: 0.0)
- `midpoint` (string, optional): Normalized value between `0.0` & :attr:`quantum_range` (default: 0.0)
- `channel` (string, optional): Optional color channel to target. See
### base_image_signature

(:class:`str`) The SHA-256 message digest for the image pixel

### base_image_similarity

Scan image for best matching ``reference`` image, and

Parameters:
- `reference` (string): Image to search for.
- `threshold` (string, optional): Stop scanning if reference similarity is (default: 0.0)
- `metric` (string, optional): specify which comparison algorithm to use. See (default: undefined)
### base_image_size

(:class:`tuple`) The pair of (:attr:`width`, :attr:`height`).

### base_image_sketch

Simulates a pencil sketch effect. For best results, ``radius``

Parameters:
- `radius` (string, optional): size of Gaussian aperture. (default: 0.0)
- `sigma` (string, optional): standard deviation of the Gaussian operator. (default: 0.0)
- `angle` (string, optional): direction of blur. (default: 0.0)
### base_image_skewness

(:class:`numbers.Real`) The skewness of the image.

### base_image_smush

Appends all images together. Similar behavior to :meth:`concat`,

Parameters:
- `stacked` (string, optional): If True, will join top-to-bottom. If False, join images (default: False)
- `offset` (string, optional): Minimum space (in pixels) between each join. (default: 0)
### base_image_solarize

Simulates extreme overexposure.

Parameters:
- `threshold` (string, optional): between ``0.0`` and :attr:`quantum_range`. (default: 0.0)
- `channel` (string, optional): Optional color channel to target. See
### base_image_splice

Partitions image by splicing a ``width`` x ``height`` rectangle at

Parameters:
- `width` (string, optional): number of pixel columns.
- `height` (string, optional): number of pixel rows.
- `x` (string, optional): offset on the X-axis.
- `y` (string, optional): offset on the Y-axis.
- `gravity` (string, optional): 
### base_image_spread

Randomly displace pixels within a defined radius.

Parameters:
- `radius` (string, optional): Distance a pixel can be displaced from source. Default (default: 0.0)
- `method` (string, optional): Interpolation method. Only available with ImageMagick-7. (default: undefined)
### base_image_standard_deviation

(:class:`numbers.Real`) The standard deviation of the image.

### base_image_statistic

Replace each pixel with the statistic results from neighboring pixel

Parameters:
- `stat` (string, optional): The type of statistic to calculate. See (default: undefined)
- `width` (string, optional): The size of neighboring pixels on the X-axis.
- `height` (string, optional): The size of neighboring pixels on the Y-axis.
- `channel` (string, optional): Optional color channel to target. See
### base_image_stegano

Hide a digital watermark of an image within the image.

Parameters:
- `watermark` (string): Image to hide within image.
- `offset` (string, optional): Start embedding image after a number of pixels. (default: 0)
### base_image_strip

Strips an image of all profiles and comments.

### base_image_stroke_color

Stroke color


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
