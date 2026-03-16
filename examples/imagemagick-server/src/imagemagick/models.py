"""Data models for imagemagick MCP server."""

from dataclasses import dataclass
from typing import Any


@dataclass
class AllocateRefParams:
    """Parameters for allocate_ref."""
    addr: str
    deallocator: str

@dataclass
class BaseImageAdaptiveBlurParams:
    """Parameters for base_image_adaptive_blur."""
    radius: str | None = None
    sigma: str | None = None
    channel: str | None = None

@dataclass
class BaseImageAdaptiveResizeParams:
    """Parameters for base_image_adaptive_resize."""
    columns: str | None = None
    rows: str | None = None

@dataclass
class BaseImageAdaptiveSharpenParams:
    """Parameters for base_image_adaptive_sharpen."""
    radius: str | None = None
    sigma: str | None = None
    channel: str | None = None

@dataclass
class BaseImageAdaptiveThresholdParams:
    """Parameters for base_image_adaptive_threshold."""
    width: str
    height: str
    offset: str | None = None

@dataclass
class BaseImageAffineParams:
    """Parameters for base_image_affine."""
    sx: str | None = None
    rx: str | None = None
    ry: str | None = None
    sy: str | None = None
    tx: str | None = None
    ty: str | None = None

@dataclass
class BaseImageAnnotateParams:
    """Parameters for base_image_annotate."""
    text: str
    drawing_wand: str
    left: str | None = None
    baseline: str | None = None
    angle: str | None = None

@dataclass
class BaseImageAutoThresholdParams:
    """Parameters for base_image_auto_threshold."""
    method: str | None = None

@dataclass
class BaseImageBilateralBlurParams:
    """Parameters for base_image_bilateral_blur."""
    width: str | None = None
    height: str | None = None
    intensity: str | None = None
    spatial: str | None = None

@dataclass
class BaseImageBlackThresholdParams:
    """Parameters for base_image_black_threshold."""
    threshold: str

@dataclass
class BaseImageBlueShiftParams:
    """Parameters for base_image_blue_shift."""
    factor: str | None = None

@dataclass
class BaseImageBlurParams:
    """Parameters for base_image_blur."""
    radius: str | None = None
    sigma: str | None = None
    channel: str | None = None

@dataclass
class BaseImageBorderParams:
    """Parameters for base_image_border."""
    color: str
    width: str
    height: str
    compose: str | None = None

@dataclass
class BaseImageBrightnessContrastParams:
    """Parameters for base_image_brightness_contrast."""
    brightness: str | None = None
    contrast: str | None = None
    channel: str | None = None

@dataclass
class BaseImageCannyParams:
    """Parameters for base_image_canny."""
    radius: str | None = None
    sigma: str | None = None
    lower_percent: str | None = None
    upper_percent: str | None = None

@dataclass
class BaseImageCaptionParams:
    """Parameters for base_image_caption."""
    text: str
    left: str | None = None
    top: str | None = None
    width: str | None = None
    height: str | None = None
    font: str | None = None
    gravity: str | None = None

@dataclass
class BaseImageCdlParams:
    """Parameters for base_image_cdl."""
    ccc: str

@dataclass
class BaseImageCharcoalParams:
    """Parameters for base_image_charcoal."""
    radius: str
    sigma: str

@dataclass
class BaseImageChopParams:
    """Parameters for base_image_chop."""
    width: str | None = None
    height: str | None = None
    x: str | None = None
    y: str | None = None
    gravity: str | None = None

@dataclass
class BaseImageClaheParams:
    """Parameters for base_image_clahe."""
    width: str
    height: str
    number_bins: str
    clip_limit: str

@dataclass
class BaseImageClampParams:
    """Parameters for base_image_clamp."""
    channel: str | None = None

@dataclass
class BaseImageClutParams:
    """Parameters for base_image_clut."""
    image: str
    method: str | None = None
    channel: str | None = None

@dataclass
class BaseImageColorDecisionListParams:
    """Parameters for base_image_color_decision_list."""
    ccc: str

@dataclass
class BaseImageColorMapParams:
    """Parameters for base_image_color_map."""
    index: str
    color: str | None = None

@dataclass
class BaseImageColorMatrixParams:
    """Parameters for base_image_color_matrix."""
    matrix: str

@dataclass
class BaseImageColorThresholdParams:
    """Parameters for base_image_color_threshold."""
    start: str | None = None
    stop: str | None = None

@dataclass
class BaseImageColorizeParams:
    """Parameters for base_image_colorize."""
    color: str | None = None
    alpha: str | None = None

@dataclass
class BaseImageCombineParams:
    """Parameters for base_image_combine."""
    channel: str | None = None
    colorspace: str | None = None

@dataclass
class BaseImageCompareParams:
    """Parameters for base_image_compare."""
    image: str
    metric: str | None = None
    highlight: str | None = None
    lowlight: str | None = None

@dataclass
class BaseImageComplexParams:
    """Parameters for base_image_complex."""
    operator: str | None = None
    snr: str | None = None

@dataclass
class BaseImageCompositeParams:
    """Parameters for base_image_composite."""
    image: str
    left: str | None = None
    top: str | None = None
    operator: str | None = None
    arguments: str | None = None
    gravity: str | None = None

@dataclass
class BaseImageCompositeChannelParams:
    """Parameters for base_image_composite_channel."""
    channel: str
    image: str
    operator: str
    left: str | None = None
    top: str | None = None
    arguments: str | None = None
    gravity: str | None = None

@dataclass
class BaseImageConcatParams:
    """Parameters for base_image_concat."""
    stacked: str | None = None

