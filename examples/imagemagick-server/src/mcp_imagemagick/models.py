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

@dataclass
class BaseImageContrastParams:
    """Parameters for base_image_contrast."""
    sharpen: str | None = None

@dataclass
class BaseImageContrastStretchParams:
    """Parameters for base_image_contrast_stretch."""
    black_point: str | None = None
    white_point: str | None = None
    channel: str | None = None

@dataclass
class BaseImageConvexHullParams:
    """Parameters for base_image_convex_hull."""
    background: str | None = None

@dataclass
class BaseImageCycleColorMapParams:
    """Parameters for base_image_cycle_color_map."""
    offset: str | None = None

@dataclass
class BaseImageDecipherParams:
    """Parameters for base_image_decipher."""
    passphrase: str

@dataclass
class BaseImageDeskewParams:
    """Parameters for base_image_deskew."""
    threshold: str

@dataclass
class BaseImageDistortParams:
    """Parameters for base_image_distort."""
    method: str
    arguments: str
    best_fit: str | None = None
    filter: str | None = None

@dataclass
class BaseImageEdgeParams:
    """Parameters for base_image_edge."""
    radius: str | None = None

@dataclass
class BaseImageEmbossParams:
    """Parameters for base_image_emboss."""
    radius: str | None = None
    sigma: str | None = None

@dataclass
class BaseImageEncipherParams:
    """Parameters for base_image_encipher."""
    passphrase: str

@dataclass
class BaseImageEqualizeParams:
    """Parameters for base_image_equalize."""
    channel: str | None = None

@dataclass
class BaseImageEvaluateParams:
    """Parameters for base_image_evaluate."""
    operator: str | None = None
    value: str | None = None
    channel: str | None = None

@dataclass
class BaseImageEvaluateImagesParams:
    """Parameters for base_image_evaluate_images."""
    operator: str | None = None

@dataclass
class BaseImageExportPixelsParams:
    """Parameters for base_image_export_pixels."""
    x: str | None = None
    y: str | None = None
    width: str | None = None
    height: str | None = None
    channel_map: str | None = None
    storage: str | None = None

@dataclass
class BaseImageExtentParams:
    """Parameters for base_image_extent."""
    width: str | None = None
    height: str | None = None
    x: str | None = None
    y: str | None = None
    gravity: str | None = None

@dataclass
class BaseImageFftParams:
    """Parameters for base_image_fft."""
    magnitude: str | None = None

@dataclass
class BaseImageFloodfillParams:
    """Parameters for base_image_floodfill."""
    fill: str | None = None
    fuzz: str | None = None
    bordercolor: str | None = None
    x: str | None = None
    y: str | None = None
    invert: str | None = None
    channel: str | None = None

@dataclass
class BaseImageForwardFourierTransformParams:
    """Parameters for base_image_forward_fourier_transform."""
    magnitude: str | None = None

@dataclass
class BaseImageFrameParams:
    """Parameters for base_image_frame."""
    matte: str | None = None
    width: str | None = None
    height: str | None = None
    inner_bevel: str | None = None
    outer_bevel: str | None = None
    compose: str | None = None

@dataclass
class BaseImageFunctionParams:
    """Parameters for base_image_function."""
    function: str
    arguments: str
    channel: str | None = None

@dataclass
class BaseImageFxParams:
    """Parameters for base_image_fx."""
    expression: str
    channel: str | None = None

@dataclass
class BaseImageGammaParams:
    """Parameters for base_image_gamma."""
    adjustment_value: str | None = None
    channel: str | None = None

@dataclass
class BaseImageGaussianBlurParams:
    """Parameters for base_image_gaussian_blur."""
    radius: str | None = None
    sigma: str | None = None
    channel: str | None = None

@dataclass
class BaseImageGetImageDistortionParams:
    """Parameters for base_image_get_image_distortion."""
    image: str
    metric: str | None = None

@dataclass
class BaseImageHaldClutParams:
    """Parameters for base_image_hald_clut."""
    image: str
    channel: str | None = None

@dataclass
class BaseImageHoughLinesParams:
    """Parameters for base_image_hough_lines."""
    width: str
    height: str | None = None
    threshold: str | None = None

@dataclass
class BaseImageIftParams:
    """Parameters for base_image_ift."""
    phase: str
    magnitude: str | None = None

@dataclass
class BaseImageImplodeParams:
    """Parameters for base_image_implode."""
    amount: str | None = None
    method: str | None = None

@dataclass
class BaseImageImportPixelsParams:
    """Parameters for base_image_import_pixels."""
    x: str | None = None
    y: str | None = None
    width: str | None = None
    height: str | None = None
    channel_map: str | None = None
    storage: str | None = None
    data: str | None = None

@dataclass
class BaseImageInverseFourierTransformParams:
    """Parameters for base_image_inverse_fourier_transform."""
    phase: str
    magnitude: str | None = None

@dataclass
class BaseImageIteratorSetParams:
    """Parameters for base_image_iterator_set."""
    index: str

@dataclass
class BaseImageKmeansParams:
    """Parameters for base_image_kmeans."""
    number_colors: str | None = None
    max_iterations: str | None = None
    tolerance: str | None = None

@dataclass
class BaseImageKurtosisChannelParams:
    """Parameters for base_image_kurtosis_channel."""
    channel: str | None = None

@dataclass
class BaseImageKuwaharaParams:
    """Parameters for base_image_kuwahara."""
    radius: str | None = None
    sigma: str | None = None

@dataclass
class BaseImageLabelParams:
    """Parameters for base_image_label."""
    text: str
    left: str | None = None
    top: str | None = None
    font: str | None = None
    gravity: str | None = None
    background_color: str | None = None

@dataclass
class BaseImageLevelParams:
    """Parameters for base_image_level."""
    black: str | None = None
    white: str | None = None
    gamma: str | None = None
    channel: str | None = None

@dataclass
class BaseImageLevelColorsParams:
    """Parameters for base_image_level_colors."""
    black_color: str
    white_color: str
    channel: str | None = None

@dataclass
class BaseImageLevelizeParams:
    """Parameters for base_image_levelize."""
    black: str | None = None
    white: str | None = None
    gamma: str | None = None
    channel: str | None = None

@dataclass
class BaseImageLevelizeColorsParams:
    """Parameters for base_image_levelize_colors."""
    black_color: str
    white_color: str
    channel: str | None = None

@dataclass
class BaseImageLinearStretchParams:
    """Parameters for base_image_linear_stretch."""
    black_point: str | None = None
    white_point: str | None = None

@dataclass
class BaseImageLiquidRescaleParams:
    """Parameters for base_image_liquid_rescale."""
    width: str
    height: str
    delta_x: str | None = None
    rigidity: str | None = None

@dataclass
class BaseImageLocalContrastParams:
    """Parameters for base_image_local_contrast."""
    radius: str | None = None
    strength: str | None = None

@dataclass
class BaseImageMeanChannelParams:
    """Parameters for base_image_mean_channel."""
    channel: str | None = None

@dataclass
class BaseImageMeanShiftParams:
    """Parameters for base_image_mean_shift."""
    width: str
    height: str
    color_distance: str | None = None

@dataclass
class BaseImageMergeLayersParams:
    """Parameters for base_image_merge_layers."""
    method: str

@dataclass
class BaseImageMinimumBoundingBoxParams:
    """Parameters for base_image_minimum_bounding_box."""
    orientation: str | None = None

@dataclass
class BaseImageModeParams:
    """Parameters for base_image_mode."""
    width: str
    height: str | None = None

@dataclass
class BaseImageModulateParams:
    """Parameters for base_image_modulate."""
    brightness: str | None = None
    saturation: str | None = None
    hue: str | None = None

@dataclass
class BaseImageMorphologyParams:
    """Parameters for base_image_morphology."""
    method: str | None = None
    kernel: str | None = None
    iterations: str | None = None
    channel: str | None = None

@dataclass
class BaseImageMotionBlurParams:
    """Parameters for base_image_motion_blur."""
    radius: str | None = None
    sigma: str | None = None
    angle: str | None = None
    channel: str | None = None

@dataclass
class BaseImageNegateParams:
    """Parameters for base_image_negate."""
    grayscale: str | None = None
    channel: str | None = None

@dataclass
class BaseImageNoiseParams:
    """Parameters for base_image_noise."""
    noise_type: str | None = None
    attenuate: str | None = None
    channel: str | None = None

@dataclass
class BaseImageNormalizeParams:
    """Parameters for base_image_normalize."""
    channel: str | None = None

@dataclass
class BaseImageOilPaintParams:
    """Parameters for base_image_oil_paint."""
    radius: str | None = None
    sigma: str | None = None

@dataclass
class BaseImageOpaquePaintParams:
    """Parameters for base_image_opaque_paint."""
    target: str | None = None
    fill: str | None = None
    fuzz: str | None = None
    invert: str | None = None
    channel: str | None = None

@dataclass
class BaseImageOrderedDitherParams:
    """Parameters for base_image_ordered_dither."""
    threshold_map: str | None = None
    channel: str | None = None

@dataclass
class BaseImageParseMetaGeometryParams:
    """Parameters for base_image_parse_meta_geometry."""
    geometry: str

@dataclass
class BaseImagePercentEscapeParams:
    """Parameters for base_image_percent_escape."""
    string_format: str

@dataclass
class BaseImagePolaroidParams:
    """Parameters for base_image_polaroid."""
    angle: str | None = None
    caption: str | None = None
    font: str | None = None
    method: str | None = None

@dataclass
class BaseImagePolynomialParams:
    """Parameters for base_image_polynomial."""
    arguments: str

@dataclass
class BaseImagePosterizeParams:
    """Parameters for base_image_posterize."""
    levels: str | None = None
    dither: str | None = None

@dataclass
class BaseImageQuantizeParams:
    """Parameters for base_image_quantize."""
    number_colors: str
    colorspace_type: str | None = None
    treedepth: str | None = None
    dither: str | None = None
    measure_error: str | None = None

@dataclass
class BaseImageRandomThresholdParams:
    """Parameters for base_image_random_threshold."""
    low: str | None = None
    high: str | None = None
    channel: str | None = None

@dataclass
class BaseImageRangeChannelParams:
    """Parameters for base_image_range_channel."""
    channel: str | None = None

@dataclass
class BaseImageRangeThresholdParams:
    """Parameters for base_image_range_threshold."""
    low_black: str | None = None
    low_white: str | None = None
    high_white: str | None = None
    high_black: str | None = None

@dataclass
class BaseImageReadMaskParams:
    """Parameters for base_image_read_mask."""
    clip_mask: str | None = None

@dataclass
class BaseImageRegionParams:
    """Parameters for base_image_region."""
    width: str | None = None
    height: str | None = None
    x: str | None = None
    y: str | None = None
    gravity: str | None = None

@dataclass
class BaseImageRemapParams:
    """Parameters for base_image_remap."""
    affinity: str | None = None
    method: str | None = None

@dataclass
class BaseImageResampleParams:
    """Parameters for base_image_resample."""
    x_res: str | None = None
    y_res: str | None = None
    filter: str | None = None
    blur: str | None = None

@dataclass
class BaseImageResizeParams:
    """Parameters for base_image_resize."""
    width: str | None = None
    height: str | None = None
    filter: str | None = None
    blur: str | None = None

@dataclass
class BaseImageRollParams:
    """Parameters for base_image_roll."""
    x: str | None = None
    y: str | None = None

@dataclass
class BaseImageRotateParams:
    """Parameters for base_image_rotate."""
    degree: str
    background: str | None = None
    reset_coords: str | None = None

@dataclass
class BaseImageRotationalBlurParams:
    """Parameters for base_image_rotational_blur."""
    angle: str | None = None
    channel: str | None = None

@dataclass
class BaseImageSampleParams:
    """Parameters for base_image_sample."""
    width: str | None = None
    height: str | None = None

@dataclass
class BaseImageScaleParams:
    """Parameters for base_image_scale."""
    columns: str | None = None
    rows: str | None = None

@dataclass
class BaseImageSelectiveBlurParams:
    """Parameters for base_image_selective_blur."""
    radius: str | None = None
    sigma: str | None = None
    threshold: str | None = None
    channel: str | None = None

@dataclass
class BaseImageSepiaToneParams:
    """Parameters for base_image_sepia_tone."""
    threshold: str | None = None

@dataclass
class BaseImageShadeParams:
    """Parameters for base_image_shade."""
    gray: str | None = None
    azimuth: str | None = None
    elevation: str | None = None

@dataclass
class BaseImageShadowParams:
    """Parameters for base_image_shadow."""
    alpha: str | None = None
    sigma: str | None = None
    x: str | None = None
    y: str | None = None

@dataclass
class BaseImageSharpenParams:
    """Parameters for base_image_sharpen."""
    radius: str | None = None
    sigma: str | None = None
    channel: str | None = None

@dataclass
class BaseImageShaveParams:
    """Parameters for base_image_shave."""
    columns: str | None = None
    rows: str | None = None

@dataclass
class BaseImageShearParams:
    """Parameters for base_image_shear."""
    background: str | None = None
    x: str | None = None
    y: str | None = None

@dataclass
class BaseImageSigmoidalContrastParams:
    """Parameters for base_image_sigmoidal_contrast."""
    sharpen: str | None = None
    strength: str | None = None
    midpoint: str | None = None
    channel: str | None = None

@dataclass
class BaseImageSimilarityParams:
    """Parameters for base_image_similarity."""
    reference: str
    threshold: str | None = None
    metric: str | None = None

@dataclass
class BaseImageSketchParams:
    """Parameters for base_image_sketch."""
    radius: str | None = None
    sigma: str | None = None
    angle: str | None = None

@dataclass
class BaseImageSmushParams:
    """Parameters for base_image_smush."""
    stacked: str | None = None
    offset: str | None = None

@dataclass
class BaseImageSolarizeParams:
    """Parameters for base_image_solarize."""
    threshold: str | None = None
    channel: str | None = None

@dataclass
class BaseImageSpliceParams:
    """Parameters for base_image_splice."""
    width: str | None = None
    height: str | None = None
    x: str | None = None
    y: str | None = None
    gravity: str | None = None

@dataclass
class BaseImageSpreadParams:
    """Parameters for base_image_spread."""
    radius: str | None = None
    method: str | None = None

@dataclass
class BaseImageStatisticParams:
    """Parameters for base_image_statistic."""
    stat: str | None = None
    width: str | None = None
    height: str | None = None
    channel: str | None = None

@dataclass
class BaseImageSteganoParams:
    """Parameters for base_image_stegano."""
    watermark: str
    offset: str | None = None

