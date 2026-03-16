"""Data models for ffmpeg MCP server."""

from dataclasses import dataclass
from typing import Any


@dataclass
class FfmpegGettingHelpParams:
    """Parameters for ffmpeg_getting_help."""
    h: bool | None = None

@dataclass
class FfmpegPrintHelpInformationCapabilitiesParams:
    """Parameters for ffmpeg_print_help_information_capabilities."""
    L: bool | None = None
    h: str | None = None
    help: str | None = None
    version: bool | None = None
    buildconf: bool | None = None
    formats: bool | None = None
    muxers: bool | None = None
    demuxers: bool | None = None
    devices: bool | None = None
    codecs: bool | None = None
    decoders: bool | None = None
    encoders: bool | None = None
    bsfs: bool | None = None
    protocols: bool | None = None
    filters: bool | None = None
    pix_fmts: bool | None = None
    layouts: bool | None = None
    sample_fmts: bool | None = None
    colors: bool | None = None
    sources: str | None = None
    sinks: str | None = None
    hwaccels: bool | None = None

@dataclass
class FfmpegGlobalOptionsAffectWholeProgramInsteadOfJustOneFileParams:
    """Parameters for ffmpeg_global_options_affect_whole_program_instead_of_just_one_file."""
    loglevel: str | None = None
    v: str | None = None
    report: bool | None = None
    max_alloc: int | None = None
    y: bool | None = None
    n: bool | None = None
    ignore_unknown: bool | None = None
    filter_threads: bool | None = None
    filter_complex_threads: bool | None = None
    stats: bool | None = None
    bits_per_raw_sample: int | None = None
    vol: int | None = None

@dataclass
class FfmpegAdvancedGlobalOptionsParams:
    """Parameters for ffmpeg_advanced_global_options."""
    cpuflags: str | None = None
    hide_banner: str | None = None
    copy_unknown: bool | None = None
    benchmark: bool | None = None
    benchmark_all: bool | None = None
    progress: str | None = None
    stdin: bool | None = None
    timelimit: int | None = None
    dump: bool | None = None
    hex: bool | None = None
    vsync: bool | None = None
    frame_drop_threshold: bool | None = None
    async_: bool | None = None
    adrift_threshold: str | None = None
    copyts: bool | None = None
    start_at_zero: bool | None = None
    copytb: str | None = None
    dts_delta_threshold: str | None = None
    dts_error_threshold: str | None = None
    xerror: str | None = None
    abort_on: str | None = None
    filter_complex: str | None = None
    lavfi: str | None = None
    filter_complex_script: str | None = None
    auto_conversion_filters: bool | None = None
    stats_period: str | None = None
    debug_ts: bool | None = None
    intra: bool | None = None
    sameq: bool | None = None
    same_quant: bool | None = None
    deinterlace: bool | None = None
    psnr: bool | None = None
    vstats: bool | None = None
    vstats_file: str | None = None
    vstats_version: bool | None = None
    qphist: bool | None = None
    vc: str | None = None
    tvstd: str | None = None
    isync: bool | None = None
    sdp_file: str | None = None
    vaapi_device: str | None = None
    qsv_device: str | None = None
    init_hw_device: str | None = None
    filter_hw_device: str | None = None

@dataclass
class FfmpegPerFileMainOptionsParams:
    """Parameters for ffmpeg_per_file_main_options."""
    f: str | None = None
    c: str | None = None
    codec: str | None = None
    pre: str | None = None
    t: str | None = None
    to: str | None = None
    fs: str | None = None
    ss: str | None = None
    sseof: str | None = None
    seek_timestamp: bool | None = None
    timestamp: str | None = None
    target: str | None = None
    apad: bool | None = None
    frames: int | None = None
    filter: str | None = None
    filter_script: str | None = None
    reinit_filter: bool | None = None
    discard: bool | None = None
    disposition: bool | None = None

@dataclass
class FfmpegAdvancedPerFileOptionsParams:
    """Parameters for ffmpeg_advanced_per_file_options."""
    map_chapters: str | None = None
    accurate_seek: bool | None = None
    itsoffset: str | None = None
    itsscale: str | None = None
    dframes: int | None = None
    re: bool | None = None
    shortest: bool | None = None
    bitexact: bool | None = None
    copyinkf: bool | None = None
    copypriorss: bool | None = None
    tag: str | None = None
    q: str | None = None
    qscale: str | None = None
    profile: str | None = None
    attach: str | None = None
    dump_attachment: str | None = None
    thread_queue_size: bool | None = None
    find_stream_info: bool | None = None
    autorotate: bool | None = None
    autoscale: bool | None = None
    muxdelay: str | None = None
    muxpreload: str | None = None
    time_base: str | None = None
    enc_time_base: str | None = None
    bsf: str | None = None
    fpre: str | None = None
    max_muxing_queue_size: str | None = None
    muxing_queue_data_threshold: int | None = None
    dcodec: str | None = None

@dataclass
class FfmpegVideoOptionsParams:
    """Parameters for ffmpeg_video_options."""
    vframes: int | None = None
    r: str | None = None
    fpsmax: str | None = None
    s: str | None = None
    aspect: str | None = None
    bits_per_raw_sample: int | None = None
    vn: bool | None = None
    vcodec: str | None = None
    pass_: str | None = None
    vf: str | None = None
    ab: str | None = None
    b: str | None = None
    dn: bool | None = None

@dataclass
class FfmpegAdvancedVideoOptionsParams:
    """Parameters for ffmpeg_advanced_video_options."""
    pix_fmt: str | None = None
    intra: bool | None = None
    rc_override: str | None = None
    sameq: bool | None = None
    same_quant: bool | None = None
    passlogfile: str | None = None
    deinterlace: bool | None = None
    psnr: bool | None = None
    vstats: bool | None = None
    vstats_file: str | None = None
    vstats_version: bool | None = None
    intra_matrix: str | None = None
    inter_matrix: str | None = None
    chroma_intra_matrix: str | None = None
    top: bool | None = None
    vtag: str | None = None
    qphist: bool | None = None
    force_fps: bool | None = None
    force_key_frames: str | None = None
    hwaccel_device: str | None = None
    hwaccel_output_format: str | None = None
    vc: str | None = None
    tvstd: str | None = None
    vpre: str | None = None

@dataclass
class FfmpegAudioOptionsParams:
    """Parameters for ffmpeg_audio_options."""
    aframes: int | None = None
    aq: str | None = None
    ar: str | None = None
    ac: str | None = None
    an: bool | None = None
    acodec: str | None = None
    vol: int | None = None
    af: str | None = None

@dataclass
class FfmpegAdvancedAudioOptionsParams:
    """Parameters for ffmpeg_advanced_audio_options."""
    atag: str | None = None
    sample_fmt: str | None = None
    channel_layout: str | None = None
    guess_layout_max: bool | None = None
    apre: str | None = None

@dataclass
class FfmpegSubtitleOptionsParams:
    """Parameters for ffmpeg_subtitle_options."""
    s: str | None = None
    sn: bool | None = None
    scodec: str | None = None
    stag: str | None = None
    fix_sub_duration: bool | None = None
    canvas_size: str | None = None
    spre: str | None = None

@dataclass
class FfmpegAvcodeccontextAvoptionsParams:
    """Parameters for ffmpeg_avcodeccontext_avoptions."""
    b: bool | None = None
    ab: bool | None = None
    bt: bool | None = None
    flags: bool | None = None
    flags2: bool | None = None
    export_side_data: bool | None = None
    g: bool | None = None
    ar: bool | None = None
    ac: bool | None = None
    cutoff: bool | None = None
    frame_size: bool | None = None
    qcomp: bool | None = None
    qblur: bool | None = None
    qmin: bool | None = None
    qmax: bool | None = None
    qdiff: bool | None = None
    bf: bool | None = None
    b_qfactor: bool | None = None
    b_strategy: bool | None = None
    ps: bool | None = None
    bug: bool | None = None
    strict: bool | None = None
    b_qoffset: bool | None = None
    err_detect: bool | None = None
    mpeg_quant: bool | None = None
    maxrate: bool | None = None
    minrate: bool | None = None
    bufsize: bool | None = None
    i_qfactor: bool | None = None
    i_qoffset: bool | None = None
    dct: bool | None = None
    lumi_mask: bool | None = None
    tcplx_mask: bool | None = None
    scplx_mask: bool | None = None
    p_mask: bool | None = None
    dark_mask: bool | None = None
    idct: bool | None = None
    ec: bool | None = None
    pred: bool | None = None
    aspect: bool | None = None
    sar: bool | None = None
    debug: bool | None = None
    dia_size: bool | None = None
    last_pred: bool | None = None
    preme: bool | None = None
    pre_dia_size: bool | None = None
    subq: bool | None = None
    me_range: bool | None = None
    global_quality: bool | None = None
    coder: bool | None = None
    context: bool | None = None
    mbd: bool | None = None
    sc_threshold: bool | None = None
    nr: bool | None = None
    threads: bool | None = None
    dc: bool | None = None
    nssew: bool | None = None
    skip_top: bool | None = None
    skip_bottom: bool | None = None
    profile: bool | None = None
    level: bool | None = None
    lowres: bool | None = None
    skip_threshold: bool | None = None
    skip_factor: bool | None = None
    skip_exp: bool | None = None
    skipcmp: bool | None = None
    cmp: bool | None = None
    subcmp: bool | None = None
    mbcmp: bool | None = None
    ildctcmp: bool | None = None
    precmp: bool | None = None
    mblmin: bool | None = None
    mblmax: bool | None = None
    mepc: bool | None = None
    skip_loop_filter: bool | None = None
    skip_idct: bool | None = None
    skip_frame: bool | None = None
    bidir_refine: bool | None = None
    brd_scale: bool | None = None
    keyint_min: bool | None = None
    refs: bool | None = None
    chromaoffset: bool | None = None
    trellis: bool | None = None
    mv0_threshold: bool | None = None
    b_sensitivity: bool | None = None
    channel_layout: bool | None = None
    rc_max_vbv_use: bool | None = None
    rc_min_vbv_use: bool | None = None
    ticks_per_frame: bool | None = None
    color_primaries: bool | None = None
    color_trc: bool | None = None
    colorspace: bool | None = None
    color_range: bool | None = None
    slices: bool | None = None
    thread_type: bool | None = None
    sub_charenc: bool | None = None
    sub_charenc_mode: bool | None = None
    sub_text_format: bool | None = None
    apply_cropping: bool | None = None
    skip_alpha: bool | None = None
    field_order: bool | None = None
    dump_separator: bool | None = None
    codec_whitelist: bool | None = None
    max_pixels: bool | None = None
    max_samples: bool | None = None
    hwaccel_flags: bool | None = None
    extra_hw_frames: bool | None = None
    mpv_flags: bool | None = None
    error_rate: bool | None = None
    qsquish: bool | None = None
    rc_qmod_amp: bool | None = None
    rc_qmod_freq: bool | None = None
    rc_eq: bool | None = None
    rc_init_cplx: bool | None = None
    border_mask: bool | None = None
    lmin: bool | None = None
    lmax: bool | None = None
    ibias: bool | None = None
    pbias: bool | None = None
    motion_est: bool | None = None
    b_strategy: bool | None = None
    b_sensitivity: bool | None = None
    brd_scale: bool | None = None
    skip_threshold: bool | None = None
    skip_factor: bool | None = None
    skip_exp: bool | None = None
    skip_cmp: bool | None = None
    sc_threshold: bool | None = None
    noise_reduction: bool | None = None
    mpeg_quant: bool | None = None
    ps: bool | None = None
    mepc: bool | None = None
    mepre: bool | None = None
    intra_penalty: bool | None = None
    a53cc: bool | None = None
    rc_strategy: bool | None = None
    pred: bool | None = None
    huffman: bool | None = None

@dataclass
class FfmpegApngEncoderAvoptionsParams:
    """Parameters for ffmpeg_apng_encoder_avoptions."""
    dpi: bool | None = None
    dpm: bool | None = None
    pred: bool | None = None
    quality: bool | None = None
    skip_empty_cb: bool | None = None
    max_strips: bool | None = None
    min_strips: bool | None = None
    dither_type: bool | None = None
    nitris_compat: bool | None = None
    ibias: bool | None = None
    profile: bool | None = None
    quant_deadzone: bool | None = None
    compression: bool | None = None
    format: bool | None = None
    gamma: bool | None = None
    slicecrc: bool | None = None
    coder: bool | None = None
    context: bool | None = None
    pred: bool | None = None
    context: bool | None = None
    mpv_flags: bool | None = None
    error_rate: bool | None = None
    qsquish: bool | None = None
    rc_qmod_amp: bool | None = None
    rc_qmod_freq: bool | None = None
    rc_eq: bool | None = None
    rc_init_cplx: bool | None = None
    border_mask: bool | None = None
    lmin: bool | None = None
    lmax: bool | None = None
    ibias: bool | None = None
    pbias: bool | None = None
    motion_est: bool | None = None
    b_strategy: bool | None = None
    b_sensitivity: bool | None = None
    brd_scale: bool | None = None
    skip_threshold: bool | None = None
    skip_factor: bool | None = None
    skip_exp: bool | None = None
    skip_cmp: bool | None = None
    sc_threshold: bool | None = None
    noise_reduction: bool | None = None
    mpeg_quant: bool | None = None
    ps: bool | None = None
    mepc: bool | None = None
    mepre: bool | None = None
    intra_penalty: bool | None = None
    a53cc: bool | None = None
    rc_strategy: bool | None = None

@dataclass
class FfmpegGifEncoderAvoptionsParams:
    """Parameters for ffmpeg_gif_encoder_avoptions."""
    gifflags: bool | None = None
    gifimage: bool | None = None
    global_palette: bool | None = None
    mpv_flags: bool | None = None
    error_rate: bool | None = None
    qsquish: bool | None = None
    rc_qmod_amp: bool | None = None
    rc_qmod_freq: bool | None = None
    rc_eq: bool | None = None
    rc_init_cplx: bool | None = None
    border_mask: bool | None = None
    lmin: bool | None = None
    lmax: bool | None = None
    ibias: bool | None = None
    pbias: bool | None = None
    motion_est: bool | None = None
    b_strategy: bool | None = None
    b_sensitivity: bool | None = None
    brd_scale: bool | None = None
    skip_threshold: bool | None = None
    skip_factor: bool | None = None
    skip_exp: bool | None = None
    skip_cmp: bool | None = None
    sc_threshold: bool | None = None
    noise_reduction: bool | None = None
    mpeg_quant: bool | None = None
    ps: bool | None = None
    mepc: bool | None = None
    mepre: bool | None = None
    intra_penalty: bool | None = None
    a53cc: bool | None = None
    rc_strategy: bool | None = None
    obmc: bool | None = None
    mb_info: bool | None = None
    mpv_flags: bool | None = None
    error_rate: bool | None = None
    qsquish: bool | None = None
    rc_qmod_amp: bool | None = None
    rc_qmod_freq: bool | None = None
    rc_eq: bool | None = None
    rc_init_cplx: bool | None = None
    border_mask: bool | None = None
    lmin: bool | None = None
    lmax: bool | None = None
    ibias: bool | None = None
    pbias: bool | None = None
    motion_est: bool | None = None
    b_strategy: bool | None = None
    b_sensitivity: bool | None = None
    brd_scale: bool | None = None
    skip_threshold: bool | None = None
    skip_factor: bool | None = None
    skip_exp: bool | None = None
    skip_cmp: bool | None = None
    sc_threshold: bool | None = None
    noise_reduction: bool | None = None
    mpeg_quant: bool | None = None
    ps: bool | None = None
    mepc: bool | None = None
    mepre: bool | None = None
    intra_penalty: bool | None = None
    a53cc: bool | None = None
    rc_strategy: bool | None = None
    umv: bool | None = None
    aiv: bool | None = None
    obmc: bool | None = None
    mpv_flags: bool | None = None
    error_rate: bool | None = None
    qsquish: bool | None = None
    rc_qmod_amp: bool | None = None
    rc_qmod_freq: bool | None = None
    rc_eq: bool | None = None
    rc_init_cplx: bool | None = None
    border_mask: bool | None = None
    lmin: bool | None = None
    lmax: bool | None = None
    ibias: bool | None = None
    pbias: bool | None = None
    motion_est: bool | None = None
    b_strategy: bool | None = None
    b_sensitivity: bool | None = None
    brd_scale: bool | None = None
    skip_threshold: bool | None = None
    skip_factor: bool | None = None
    skip_exp: bool | None = None
    skip_cmp: bool | None = None
    sc_threshold: bool | None = None
    noise_reduction: bool | None = None
    mpeg_quant: bool | None = None
    ps: bool | None = None
    mepc: bool | None = None
    mepre: bool | None = None
    intra_penalty: bool | None = None
    a53cc: bool | None = None
    rc_strategy: bool | None = None

@dataclass
class FfmpegHapEncoderAvoptionsParams:
    """Parameters for ffmpeg_hap_encoder_avoptions."""
    format: bool | None = None
    chunks: bool | None = None
    compressor: bool | None = None
    pred: bool | None = None
    format: bool | None = None
    tile_width: bool | None = None
    tile_height: bool | None = None
    pred: bool | None = None
    sop: bool | None = None
    eph: bool | None = None
    prog: bool | None = None
    layer_rates: bool | None = None
    pred: bool | None = None
    pred: bool | None = None
    pred: bool | None = None
    mpv_flags: bool | None = None
    error_rate: bool | None = None
    qsquish: bool | None = None
    rc_qmod_amp: bool | None = None
    rc_qmod_freq: bool | None = None
    rc_eq: bool | None = None
    rc_init_cplx: bool | None = None
    border_mask: bool | None = None
    lmin: bool | None = None
    lmax: bool | None = None
    ibias: bool | None = None
    pbias: bool | None = None
    motion_est: bool | None = None
    b_strategy: bool | None = None
    b_sensitivity: bool | None = None
    brd_scale: bool | None = None
    skip_threshold: bool | None = None
    skip_factor: bool | None = None
    skip_exp: bool | None = None
    skip_cmp: bool | None = None
    sc_threshold: bool | None = None
    noise_reduction: bool | None = None
    mpeg_quant: bool | None = None
    ps: bool | None = None
    mepc: bool | None = None
    mepre: bool | None = None
    intra_penalty: bool | None = None
    a53cc: bool | None = None
    rc_strategy: bool | None = None
    pred: bool | None = None
    huffman: bool | None = None
    gop_timecode: bool | None = None
    scan_offset: bool | None = None
    mpv_flags: bool | None = None
    error_rate: bool | None = None
    qsquish: bool | None = None
    rc_qmod_amp: bool | None = None
    rc_qmod_freq: bool | None = None
    rc_eq: bool | None = None
    rc_init_cplx: bool | None = None
    border_mask: bool | None = None
    lmin: bool | None = None
    lmax: bool | None = None
    ibias: bool | None = None
    pbias: bool | None = None
    motion_est: bool | None = None
    b_strategy: bool | None = None
    b_sensitivity: bool | None = None
    brd_scale: bool | None = None
    skip_threshold: bool | None = None
    skip_factor: bool | None = None
    skip_exp: bool | None = None
    skip_cmp: bool | None = None
    sc_threshold: bool | None = None
    noise_reduction: bool | None = None
    mpeg_quant: bool | None = None
    ps: bool | None = None
    mepc: bool | None = None
    mepre: bool | None = None
    intra_penalty: bool | None = None
    a53cc: bool | None = None
    rc_strategy: bool | None = None
    gop_timecode: bool | None = None
    scan_offset: bool | None = None
    intra_vlc: bool | None = None
    non_linear_quant: bool | None = None
    alternate_scan: bool | None = None
    seq_disp_ext: bool | None = None
    video_format: bool | None = None
    mpv_flags: bool | None = None
    error_rate: bool | None = None
    qsquish: bool | None = None
    rc_qmod_amp: bool | None = None
    rc_qmod_freq: bool | None = None
    rc_eq: bool | None = None
    rc_init_cplx: bool | None = None
    border_mask: bool | None = None
    lmin: bool | None = None
    lmax: bool | None = None
    ibias: bool | None = None
    pbias: bool | None = None
    motion_est: bool | None = None
    b_strategy: bool | None = None
    b_sensitivity: bool | None = None
    brd_scale: bool | None = None
    skip_threshold: bool | None = None
    skip_factor: bool | None = None
    skip_exp: bool | None = None
    skip_cmp: bool | None = None
    sc_threshold: bool | None = None
    noise_reduction: bool | None = None
    mpeg_quant: bool | None = None
    ps: bool | None = None
    mepc: bool | None = None
    mepre: bool | None = None
    intra_penalty: bool | None = None
    a53cc: bool | None = None
    rc_strategy: bool | None = None
    alternate_scan: bool | None = None
    mpv_flags: bool | None = None
    error_rate: bool | None = None
    qsquish: bool | None = None
    rc_qmod_amp: bool | None = None
    rc_qmod_freq: bool | None = None
    rc_eq: bool | None = None
    rc_init_cplx: bool | None = None
    border_mask: bool | None = None
    lmin: bool | None = None
    lmax: bool | None = None
    ibias: bool | None = None
    pbias: bool | None = None
    motion_est: bool | None = None
    b_strategy: bool | None = None
    b_sensitivity: bool | None = None
    brd_scale: bool | None = None
    skip_threshold: bool | None = None
    skip_factor: bool | None = None
    skip_exp: bool | None = None
    skip_cmp: bool | None = None
    sc_threshold: bool | None = None
    noise_reduction: bool | None = None
    mpeg_quant: bool | None = None
    ps: bool | None = None
    mepc: bool | None = None
    mepre: bool | None = None
    intra_penalty: bool | None = None
    a53cc: bool | None = None
    rc_strategy: bool | None = None
    mpv_flags: bool | None = None
    error_rate: bool | None = None
    qsquish: bool | None = None
    rc_qmod_amp: bool | None = None
    rc_qmod_freq: bool | None = None
    rc_eq: bool | None = None
    rc_init_cplx: bool | None = None
    border_mask: bool | None = None
    lmin: bool | None = None
    lmax: bool | None = None
    ibias: bool | None = None
    pbias: bool | None = None
    motion_est: bool | None = None
    b_strategy: bool | None = None
    b_sensitivity: bool | None = None
    brd_scale: bool | None = None
    skip_threshold: bool | None = None
    skip_factor: bool | None = None
    skip_exp: bool | None = None
    skip_cmp: bool | None = None
    sc_threshold: bool | None = None
    noise_reduction: bool | None = None
    mpeg_quant: bool | None = None
    ps: bool | None = None
    mepc: bool | None = None
    mepre: bool | None = None
    intra_penalty: bool | None = None
    a53cc: bool | None = None
    rc_strategy: bool | None = None
    mpv_flags: bool | None = None
    error_rate: bool | None = None
    qsquish: bool | None = None
    rc_qmod_amp: bool | None = None
    rc_qmod_freq: bool | None = None
    rc_eq: bool | None = None
    rc_init_cplx: bool | None = None
    border_mask: bool | None = None
    lmin: bool | None = None
    lmax: bool | None = None
    ibias: bool | None = None
    pbias: bool | None = None
    motion_est: bool | None = None
    b_strategy: bool | None = None
    b_sensitivity: bool | None = None
    brd_scale: bool | None = None
    skip_threshold: bool | None = None
    skip_factor: bool | None = None
    skip_exp: bool | None = None
    skip_cmp: bool | None = None
    sc_threshold: bool | None = None
    noise_reduction: bool | None = None
    mpeg_quant: bool | None = None
    ps: bool | None = None
    mepc: bool | None = None
    mepre: bool | None = None
    intra_penalty: bool | None = None
    a53cc: bool | None = None
    rc_strategy: bool | None = None

@dataclass
class FfmpegPngEncoderAvoptionsParams:
    """Parameters for ffmpeg_png_encoder_avoptions."""
    dpi: bool | None = None
    dpm: bool | None = None
    pred: bool | None = None

@dataclass
class FfmpegProresEncoderAvoptionsParams:
    """Parameters for ffmpeg_prores_encoder_avoptions."""
    vendor: bool | None = None

@dataclass
class FfmpegProresawEncoderAvoptionsParams:
    """Parameters for ffmpeg_proresaw_encoder_avoptions."""
    vendor: bool | None = None

@dataclass
class FfmpegProresEncoderAvoptionsParams:
    """Parameters for ffmpeg_prores_encoder_avoptions."""
    mbs_per_slice: bool | None = None
    profile: bool | None = None
    vendor: bool | None = None
    bits_per_mb: bool | None = None
    quant_mat: bool | None = None
    alpha_bits: bool | None = None

@dataclass
class FfmpegRoqAvoptionsParams:
    """Parameters for ffmpeg_roq_avoptions."""
    quake3_compat: bool | None = None
    mpv_flags: bool | None = None
    error_rate: bool | None = None
    qsquish: bool | None = None
    rc_qmod_amp: bool | None = None
    rc_qmod_freq: bool | None = None
    rc_eq: bool | None = None
    rc_init_cplx: bool | None = None
    border_mask: bool | None = None
    lmin: bool | None = None
    lmax: bool | None = None
    ibias: bool | None = None
    pbias: bool | None = None
    motion_est: bool | None = None
    b_strategy: bool | None = None
    b_sensitivity: bool | None = None
    brd_scale: bool | None = None
    skip_threshold: bool | None = None
    skip_factor: bool | None = None
    skip_exp: bool | None = None
    skip_cmp: bool | None = None
    sc_threshold: bool | None = None
    noise_reduction: bool | None = None
    mpeg_quant: bool | None = None
    ps: bool | None = None
    mepc: bool | None = None
    mepre: bool | None = None
    intra_penalty: bool | None = None
    a53cc: bool | None = None
    rc_strategy: bool | None = None
    mpv_flags: bool | None = None
    error_rate: bool | None = None
    qsquish: bool | None = None
    rc_qmod_amp: bool | None = None
    rc_qmod_freq: bool | None = None
    rc_eq: bool | None = None
    rc_init_cplx: bool | None = None
    border_mask: bool | None = None
    lmin: bool | None = None
    lmax: bool | None = None
    ibias: bool | None = None
    pbias: bool | None = None
    motion_est: bool | None = None
    b_strategy: bool | None = None
    b_sensitivity: bool | None = None
    brd_scale: bool | None = None
    skip_threshold: bool | None = None
    skip_factor: bool | None = None
    skip_exp: bool | None = None
    skip_cmp: bool | None = None
    sc_threshold: bool | None = None
    noise_reduction: bool | None = None
    mpeg_quant: bool | None = None
    ps: bool | None = None
    mepc: bool | None = None
    mepre: bool | None = None
    intra_penalty: bool | None = None
    a53cc: bool | None = None
    rc_strategy: bool | None = None
    rle: bool | None = None
    motion_est: bool | None = None
    memc_only: bool | None = None
    no_bitstream: bool | None = None
    intra_penalty: bool | None = None
    sc_threshold: bool | None = None
    pred: bool | None = None
    rc_eq: bool | None = None
    mpv_flags: bool | None = None
    error_rate: bool | None = None
    qsquish: bool | None = None
    rc_qmod_amp: bool | None = None
    rc_qmod_freq: bool | None = None
    rc_eq: bool | None = None
    rc_init_cplx: bool | None = None
    border_mask: bool | None = None
    lmin: bool | None = None
    lmax: bool | None = None
    ibias: bool | None = None
    pbias: bool | None = None
    motion_est: bool | None = None
    b_strategy: bool | None = None
    b_sensitivity: bool | None = None
    brd_scale: bool | None = None
    skip_threshold: bool | None = None
    skip_factor: bool | None = None
    skip_exp: bool | None = None
    skip_cmp: bool | None = None
    sc_threshold: bool | None = None
    noise_reduction: bool | None = None
    mpeg_quant: bool | None = None
    ps: bool | None = None
    mepc: bool | None = None
    mepre: bool | None = None
    intra_penalty: bool | None = None
    a53cc: bool | None = None
    rc_strategy: bool | None = None
    rle: bool | None = None
    rle: bool | None = None

@dataclass
class FfmpegTiffEncoderAvoptionsParams:
    """Parameters for ffmpeg_tiff_encoder_avoptions."""
    dpi: bool | None = None
    compression_algo: bool | None = None
    pred: bool | None = None
    tolerance: bool | None = None
    slice_width: bool | None = None
    slice_height: bool | None = None
    wavelet_depth: bool | None = None
    wavelet_type: bool | None = None
    qm: bool | None = None
    mpv_flags: bool | None = None
    error_rate: bool | None = None
    qsquish: bool | None = None
    rc_qmod_amp: bool | None = None
    rc_qmod_freq: bool | None = None
    rc_eq: bool | None = None
    rc_init_cplx: bool | None = None
    border_mask: bool | None = None
    lmin: bool | None = None
    lmax: bool | None = None
    ibias: bool | None = None
    pbias: bool | None = None
    motion_est: bool | None = None
    b_strategy: bool | None = None
    b_sensitivity: bool | None = None
    brd_scale: bool | None = None
    skip_threshold: bool | None = None
    skip_factor: bool | None = None
    skip_exp: bool | None = None
    skip_cmp: bool | None = None
    sc_threshold: bool | None = None
    noise_reduction: bool | None = None
    mpeg_quant: bool | None = None
    ps: bool | None = None
    mepc: bool | None = None
    mepre: bool | None = None
    intra_penalty: bool | None = None
    a53cc: bool | None = None
    rc_strategy: bool | None = None
    mpv_flags: bool | None = None
    error_rate: bool | None = None
    qsquish: bool | None = None
    rc_qmod_amp: bool | None = None
    rc_qmod_freq: bool | None = None
    rc_eq: bool | None = None
    rc_init_cplx: bool | None = None
    border_mask: bool | None = None
    lmin: bool | None = None
    lmax: bool | None = None
    ibias: bool | None = None
    pbias: bool | None = None
    motion_est: bool | None = None
    b_strategy: bool | None = None
    b_sensitivity: bool | None = None
    brd_scale: bool | None = None
    skip_threshold: bool | None = None
    skip_factor: bool | None = None
    skip_exp: bool | None = None
    skip_cmp: bool | None = None
    sc_threshold: bool | None = None
    noise_reduction: bool | None = None
    mpeg_quant: bool | None = None
    ps: bool | None = None
    mepc: bool | None = None
    mepre: bool | None = None
    intra_penalty: bool | None = None
    a53cc: bool | None = None
    rc_strategy: bool | None = None

@dataclass
class FfmpegAacEncoderAvoptionsParams:
    """Parameters for ffmpeg_aac_encoder_avoptions."""
    aac_coder: bool | None = None
    aac_ms: bool | None = None
    aac_is: bool | None = None
    aac_pns: bool | None = None
    aac_tns: bool | None = None
    aac_ltp: bool | None = None
    aac_pred: bool | None = None
    aac_pce: bool | None = None
    center_mixlev: bool | None = None
    surround_mixlev: bool | None = None
    mixing_level: bool | None = None
    room_type: bool | None = None
    copyright: bool | None = None
    dialnorm: bool | None = None
    dsur_mode: bool | None = None
    original: bool | None = None
    dmix_mode: bool | None = None
    ltrt_cmixlev: bool | None = None
    ltrt_surmixlev: bool | None = None
    loro_cmixlev: bool | None = None
    loro_surmixlev: bool | None = None
    dsurex_mode: bool | None = None
    dheadphone_mode: bool | None = None
    ad_conv_type: bool | None = None
    channel_coupling: bool | None = None
    cpl_start_band: bool | None = None
    center_mixlev: bool | None = None
    surround_mixlev: bool | None = None
    mixing_level: bool | None = None
    room_type: bool | None = None
    copyright: bool | None = None
    dialnorm: bool | None = None
    dsur_mode: bool | None = None
    original: bool | None = None
    dmix_mode: bool | None = None
    ltrt_cmixlev: bool | None = None
    ltrt_surmixlev: bool | None = None
    loro_cmixlev: bool | None = None
    loro_surmixlev: bool | None = None
    dsurex_mode: bool | None = None
    dheadphone_mode: bool | None = None
    ad_conv_type: bool | None = None
    channel_coupling: bool | None = None
    cpl_start_band: bool | None = None

@dataclass
class FfmpegDcaDtsCoherentAcousticsAvoptionsParams:
    """Parameters for ffmpeg_dca_dts_coherent_acoustics_avoptions."""
    dca_adpcm: bool | None = None
    mixing_level: bool | None = None
    room_type: bool | None = None
    copyright: bool | None = None
    dialnorm: bool | None = None
    dsur_mode: bool | None = None
    original: bool | None = None
    dmix_mode: bool | None = None
    ltrt_cmixlev: bool | None = None
    ltrt_surmixlev: bool | None = None
    loro_cmixlev: bool | None = None
    loro_surmixlev: bool | None = None
    dsurex_mode: bool | None = None
    dheadphone_mode: bool | None = None
    ad_conv_type: bool | None = None
    channel_coupling: bool | None = None
    cpl_start_band: bool | None = None

@dataclass
class FfmpegFlacEncoderAvoptionsParams:
    """Parameters for ffmpeg_flac_encoder_avoptions."""
    lpc_type: bool | None = None
    lpc_passes: bool | None = None
    ch_mode: bool | None = None
    multi_dim_quant: bool | None = None

@dataclass
class FfmpegOpusEncoderAvoptionsParams:
    """Parameters for ffmpeg_opus_encoder_avoptions."""
    opus_delay: bool | None = None
    apply_phase_inv: bool | None = None
    sbc_delay: bool | None = None
    msbc: bool | None = None

@dataclass
class FfmpegWavpackEncoderAvoptionsParams:
    """Parameters for ffmpeg_wavpack_encoder_avoptions."""
    joint_stereo: bool | None = None
    optimize_mono: bool | None = None
    block_size: bool | None = None
    code_size: bool | None = None
    code_size: bool | None = None
    block_size: bool | None = None
    block_size: bool | None = None
    block_size: bool | None = None
    block_size: bool | None = None
    block_size: bool | None = None
    block_size: bool | None = None
    block_size: bool | None = None
    block_size: bool | None = None
    block_size: bool | None = None

@dataclass
class FfmpegVobsubSubtitleEncoderAvoptionsParams:
    """Parameters for ffmpeg_vobsub_subtitle_encoder_avoptions."""
    palette: bool | None = None
    even_rows_fix: bool | None = None

@dataclass
class FfmpegMovTextEnoderAvoptionsParams:
    """Parameters for ffmpeg_mov_text_enoder_avoptions."""
    height: bool | None = None
    crf: bool | None = None
    tiles: bool | None = None
    usage: bool | None = None
    tune: bool | None = None
    mode: bool | None = None
    reservoir: bool | None = None
    joint_stereo: bool | None = None
    abr: bool | None = None
    format: bool | None = None
    profile: bool | None = None
    cinema_mode: bool | None = None
    prog_order: bool | None = None
    numresolution: bool | None = None
    irreversible: bool | None = None
    disto_alloc: bool | None = None
    fixed_quality: bool | None = None
    application: bool | None = None
    frame_duration: bool | None = None
    packet_loss: bool | None = None
    fec: bool | None = None
    vbr: bool | None = None
    mapping_family: bool | None = None
    apply_phase_inv: bool | None = None
    abr: bool | None = None
    cbr_quality: bool | None = None
    vad: bool | None = None
    dtx: bool | None = None
    mode: bool | None = None
    psymodel: bool | None = None
    energy_levels: bool | None = None
    error_protection: bool | None = None
    copyright: bool | None = None
    original: bool | None = None
    verbosity: bool | None = None
    iblock: bool | None = None
    tune: bool | None = None
    deadline: bool | None = None
    crf: bool | None = None
    speed: bool | None = None
    quality: bool | None = None
    vp8flags: bool | None = None
    arnr_max_frames: bool | None = None
    arnr_strength: bool | None = None
    arnr_type: bool | None = None
    rc_lookahead: bool | None = None
    sharpness: bool | None = None
    tune: bool | None = None
    deadline: bool | None = None
    crf: bool | None = None
    lossless: bool | None = None
    level: bool | None = None
    speed: bool | None = None
    quality: bool | None = None
    vp8flags: bool | None = None
    arnr_max_frames: bool | None = None
    arnr_strength: bool | None = None
    arnr_type: bool | None = None
    rc_lookahead: bool | None = None
    sharpness: bool | None = None
    lossless: bool | None = None
    preset: bool | None = None
    cr_threshold: bool | None = None
    cr_size: bool | None = None
    quality: bool | None = None
    lossless: bool | None = None
    preset: bool | None = None
    cr_threshold: bool | None = None
    cr_size: bool | None = None
    quality: bool | None = None
    preset: bool | None = None
    tune: bool | None = None
    profile: bool | None = None
    fastfirstpass: bool | None = None
    level: bool | None = None
    passlogfile: bool | None = None
    wpredp: bool | None = None
    a53cc: bool | None = None
    x264opts: bool | None = None
    crf: bool | None = None
    crf_max: bool | None = None
    qp: bool | None = None
    psy: bool | None = None
    weightb: bool | None = None
    weightp: bool | None = None
    ssim: bool | None = None
    p_8x8dct: bool | None = None
    aud: bool | None = None
    mbtree: bool | None = None
    deblock: bool | None = None
    cplxblur: bool | None = None
    partitions: bool | None = None
    stats: bool | None = None
    me_method: bool | None = None
    coder: bool | None = None
    b_strategy: bool | None = None
    chromaoffset: bool | None = None
    sc_threshold: bool | None = None
    noise_reduction: bool | None = None
    preset: bool | None = None
    tune: bool | None = None
    profile: bool | None = None
    fastfirstpass: bool | None = None
    level: bool | None = None
    passlogfile: bool | None = None
    wpredp: bool | None = None
    a53cc: bool | None = None
    x264opts: bool | None = None
    crf: bool | None = None
    crf_max: bool | None = None
    qp: bool | None = None
    psy: bool | None = None
    weightb: bool | None = None
    weightp: bool | None = None
    ssim: bool | None = None
    p_8x8dct: bool | None = None
    aud: bool | None = None
    mbtree: bool | None = None
    deblock: bool | None = None
    cplxblur: bool | None = None
    partitions: bool | None = None
    stats: bool | None = None
    me_method: bool | None = None
    coder: bool | None = None
    b_strategy: bool | None = None
    chromaoffset: bool | None = None
    sc_threshold: bool | None = None
    noise_reduction: bool | None = None
    crf: bool | None = None
    qp: bool | None = None
    preset: bool | None = None
    tune: bool | None = None
    profile: bool | None = None
    lumi_aq: bool | None = None
    variance_aq: bool | None = None
    ssim: bool | None = None
    ssim_acc: bool | None = None
    gmc: bool | None = None
    me_quality: bool | None = None
    mpeg_quant: bool | None = None
    preset: bool | None = None
    tune: bool | None = None
    profile: bool | None = None
    level: bool | None = None
    rc: bool | None = None
    surfaces: bool | None = None
    cbr: bool | None = None
    p_2pass: bool | None = None
    gpu: bool | None = None
    delay: bool | None = None
    b_adapt: bool | None = None
    spatial_aq: bool | None = None
    temporal_aq: bool | None = None
    zerolatency: bool | None = None
    nonref_p: bool | None = None
    strict_gop: bool | None = None
    cq: bool | None = None
    aud: bool | None = None
    init_qpP: bool | None = None
    init_qpB: bool | None = None
    init_qpI: bool | None = None
    qp: bool | None = None
    weighted_pred: bool | None = None
    coder: bool | None = None
    b_ref_mode: bool | None = None
    a53cc: bool | None = None
    dpb_size: bool | None = None
    multipass: bool | None = None
    ldkfs: bool | None = None
    omx_libname: bool | None = None
    omx_libprefix: bool | None = None
    zerocopy: bool | None = None
    profile: bool | None = None
    async_depth: bool | None = None
    avbr_accuracy: bool | None = None
    avbr_convergence: bool | None = None
    preset: bool | None = None
    rdo: bool | None = None
    max_frame_size: bool | None = None
    max_slice_size: bool | None = None
    bitrate_limit: bool | None = None
    mbbrc: bool | None = None
    extbrc: bool | None = None
    adaptive_i: bool | None = None
    adaptive_b: bool | None = None
    b_strategy: bool | None = None
    forced_idr: bool | None = None
    low_power: bool | None = None
    cavlc: bool | None = None
    idr_interval: bool | None = None
    pic_timing_sei: bool | None = None
    look_ahead: bool | None = None
    look_ahead_depth: bool | None = None
    int_ref_type: bool | None = None
    int_ref_qp_delta: bool | None = None
    profile: bool | None = None
    a53cc: bool | None = None
    aud: bool | None = None
    mfmode: bool | None = None
    repeat_pps: bool | None = None
    low_power: bool | None = None
    idr_interval: bool | None = None
    b_depth: bool | None = None
    rc_mode: bool | None = None
    qp: bool | None = None
    quality: bool | None = None
    coder: bool | None = None
    aud: bool | None = None
    sei: bool | None = None
    profile: bool | None = None
    level: bool | None = None
    preset: bool | None = None
    tune: bool | None = None
    profile: bool | None = None
    level: bool | None = None
    rc: bool | None = None
    surfaces: bool | None = None
    cbr: bool | None = None
    p_2pass: bool | None = None
    gpu: bool | None = None
    delay: bool | None = None
    b_adapt: bool | None = None
    spatial_aq: bool | None = None
    temporal_aq: bool | None = None
    zerolatency: bool | None = None
    nonref_p: bool | None = None
    strict_gop: bool | None = None
    cq: bool | None = None
    aud: bool | None = None
    init_qpP: bool | None = None
    init_qpB: bool | None = None
    init_qpI: bool | None = None
    qp: bool | None = None
    weighted_pred: bool | None = None
    coder: bool | None = None
    b_ref_mode: bool | None = None
    a53cc: bool | None = None
    dpb_size: bool | None = None
    multipass: bool | None = None
    ldkfs: bool | None = None
    preset: bool | None = None
    tune: bool | None = None
    profile: bool | None = None
    level: bool | None = None
    rc: bool | None = None
    surfaces: bool | None = None
    cbr: bool | None = None
    p_2pass: bool | None = None
    gpu: bool | None = None
    delay: bool | None = None
    b_adapt: bool | None = None
    spatial_aq: bool | None = None
    temporal_aq: bool | None = None
    zerolatency: bool | None = None
    nonref_p: bool | None = None
    strict_gop: bool | None = None
    cq: bool | None = None
    aud: bool | None = None
    init_qpP: bool | None = None
    init_qpB: bool | None = None
    init_qpI: bool | None = None
    qp: bool | None = None
    weighted_pred: bool | None = None
    coder: bool | None = None
    b_ref_mode: bool | None = None
    a53cc: bool | None = None
    dpb_size: bool | None = None
    multipass: bool | None = None
    ldkfs: bool | None = None
    preset: bool | None = None
    tune: bool | None = None
    profile: bool | None = None
    level: bool | None = None
    tier: bool | None = None
    rc: bool | None = None
    surfaces: bool | None = None
    cbr: bool | None = None
    p_2pass: bool | None = None
    gpu: bool | None = None
    delay: bool | None = None
    spatial_aq: bool | None = None
    temporal_aq: bool | None = None
    zerolatency: bool | None = None
    nonref_p: bool | None = None
    strict_gop: bool | None = None
    cq: bool | None = None
    aud: bool | None = None
    init_qpP: bool | None = None
    init_qpB: bool | None = None
    init_qpI: bool | None = None
    qp: bool | None = None
    weighted_pred: bool | None = None
    b_ref_mode: bool | None = None
    a53cc: bool | None = None
    s12m_tc: bool | None = None
    dpb_size: bool | None = None
    multipass: bool | None = None
    ldkfs: bool | None = None
    preset: bool | None = None
    tune: bool | None = None
    profile: bool | None = None
    level: bool | None = None
    tier: bool | None = None
    rc: bool | None = None
    surfaces: bool | None = None
    cbr: bool | None = None
    p_2pass: bool | None = None
    gpu: bool | None = None
    delay: bool | None = None
    spatial_aq: bool | None = None
    temporal_aq: bool | None = None
    zerolatency: bool | None = None
    nonref_p: bool | None = None
    strict_gop: bool | None = None
    cq: bool | None = None
    aud: bool | None = None
    init_qpP: bool | None = None
    init_qpB: bool | None = None
    init_qpI: bool | None = None
    qp: bool | None = None
    weighted_pred: bool | None = None
    b_ref_mode: bool | None = None
    a53cc: bool | None = None
    s12m_tc: bool | None = None
    dpb_size: bool | None = None
    multipass: bool | None = None
    ldkfs: bool | None = None
    async_depth: bool | None = None
    avbr_accuracy: bool | None = None
    avbr_convergence: bool | None = None
    preset: bool | None = None
    rdo: bool | None = None
    max_frame_size: bool | None = None
    max_slice_size: bool | None = None
    bitrate_limit: bool | None = None
    mbbrc: bool | None = None
    extbrc: bool | None = None
    adaptive_i: bool | None = None
    adaptive_b: bool | None = None
    b_strategy: bool | None = None
    forced_idr: bool | None = None
    low_power: bool | None = None
    idr_interval: bool | None = None
    load_plugin: bool | None = None
    load_plugins: bool | None = None
    profile: bool | None = None
    gpb: bool | None = None
    tile_cols: bool | None = None
    tile_rows: bool | None = None
    low_power: bool | None = None
    idr_interval: bool | None = None
    b_depth: bool | None = None
    rc_mode: bool | None = None
    qp: bool | None = None
    aud: bool | None = None
    profile: bool | None = None
    tier: bool | None = None
    level: bool | None = None
    sei: bool | None = None
    tiles: bool | None = None
    async_depth: bool | None = None
    low_power: bool | None = None
    idr_interval: bool | None = None
    b_depth: bool | None = None
    jfif: bool | None = None
    huffman: bool | None = None
    async_depth: bool | None = None
    avbr_accuracy: bool | None = None
    avbr_convergence: bool | None = None
    preset: bool | None = None
    rdo: bool | None = None
    max_frame_size: bool | None = None
    max_slice_size: bool | None = None
    bitrate_limit: bool | None = None
    mbbrc: bool | None = None
    extbrc: bool | None = None
    adaptive_i: bool | None = None
    adaptive_b: bool | None = None
    b_strategy: bool | None = None
    forced_idr: bool | None = None
    low_power: bool | None = None
    profile: bool | None = None
    low_power: bool | None = None
    idr_interval: bool | None = None
    b_depth: bool | None = None
    rc_mode: bool | None = None
    profile: bool | None = None
    level: bool | None = None
    omx_libname: bool | None = None
    omx_libprefix: bool | None = None
    zerocopy: bool | None = None
    profile: bool | None = None
    low_power: bool | None = None
    idr_interval: bool | None = None
    b_depth: bool | None = None
    rc_mode: bool | None = None
    low_power: bool | None = None
    idr_interval: bool | None = None
    b_depth: bool | None = None
    rc_mode: bool | None = None
    async_depth: bool | None = None
    avbr_accuracy: bool | None = None
    avbr_convergence: bool | None = None
    preset: bool | None = None
    rdo: bool | None = None
    max_frame_size: bool | None = None
    max_slice_size: bool | None = None
    bitrate_limit: bool | None = None
    mbbrc: bool | None = None
    extbrc: bool | None = None
    adaptive_i: bool | None = None
    adaptive_b: bool | None = None
    b_strategy: bool | None = None
    forced_idr: bool | None = None
    low_power: bool | None = None
    profile: bool | None = None

@dataclass
class FfmpegExrAvoptionsParams:
    """Parameters for ffmpeg_exr_avoptions."""
    layer: bool | None = None
    part: bool | None = None
    gamma: bool | None = None
    apply_trc: bool | None = None

@dataclass
class FfmpegFicDecoderAvoptionsParams:
    """Parameters for ffmpeg_fic_decoder_avoptions."""
    skip_cursor: bool | None = None

@dataclass
class FfmpegFitsDecoderAvoptionsParams:
    """Parameters for ffmpeg_fits_decoder_avoptions."""
    blank_value: bool | None = None
    trans_color: bool | None = None
    enable_er: bool | None = None
    x264_build: bool | None = None
    async_depth: bool | None = None
    gpu_copy: bool | None = None

@dataclass
class FfmpegHevcDecoderAvoptionsParams:
    """Parameters for ffmpeg_hevc_decoder_avoptions."""
    apply_defdispwin: bool | None = None
    async_depth: bool | None = None
    load_plugin: bool | None = None
    load_plugins: bool | None = None
    gpu_copy: bool | None = None
    lowres: bool | None = None

@dataclass
class FfmpegMjpegDecoderAvoptionsParams:
    """Parameters for ffmpeg_mjpeg_decoder_avoptions."""
    extern_huff: bool | None = None
    async_depth: bool | None = None
    gpu_copy: bool | None = None
    lowres: bool | None = None
    skip_cursor: bool | None = None
    top: bool | None = None
    non_pcm_mode: bool | None = None

@dataclass
class FfmpegTiffDecoderAvoptionsParams:
    """Parameters for ffmpeg_tiff_decoder_avoptions."""
    subimage: bool | None = None
    thumbnail: bool | None = None
    page: bool | None = None
    custom_stride: bool | None = None
    async_depth: bool | None = None
    gpu_copy: bool | None = None

@dataclass
class FfmpegAacDecoderAvoptionsParams:
    """Parameters for ffmpeg_aac_decoder_avoptions."""
    dual_mono_mode: bool | None = None
    cons_noisegen: bool | None = None
    drc_scale: bool | None = None
    heavy_compr: bool | None = None
    target_level: bool | None = None
    cons_noisegen: bool | None = None
    drc_scale: bool | None = None
    heavy_compr: bool | None = None
    extra_bits_bug: bool | None = None

@dataclass
class FfmpegApeDecoderAvoptionsParams:
    """Parameters for ffmpeg_ape_decoder_avoptions."""
    max_samples: bool | None = None

@dataclass
class FfmpegDcaDecoderAvoptionsParams:
    """Parameters for ffmpeg_dca_decoder_avoptions."""
    core_only: bool | None = None
    cons_noisegen: bool | None = None
    drc_scale: bool | None = None
    heavy_compr: bool | None = None
    target_level: bool | None = None
    postfilter: bool | None = None

@dataclass
class FfmpegFlacDecoderAvoptionsParams:
    """Parameters for ffmpeg_flac_decoder_avoptions."""
    use_buggy_lpc: bool | None = None
    postfilter: bool | None = None

@dataclass
class FfmpegOpusDecoderAvoptionsParams:
    """Parameters for ffmpeg_opus_decoder_avoptions."""
    apply_phase_inv: bool | None = None

@dataclass
class FfmpegTtaDecoderAvoptionsParams:
    """Parameters for ffmpeg_tta_decoder_avoptions."""
    password: bool | None = None

@dataclass
class FfmpegClosedCaptionDecoderAvoptionsParams:
    """Parameters for ffmpeg_closed_caption_decoder_avoptions."""
    real_time: bool | None = None
    data_field: bool | None = None

@dataclass
class FfmpegDvbSubDecoderAvoptionsParams:
    """Parameters for ffmpeg_dvb_sub_decoder_avoptions."""
    compute_edt: bool | None = None
    compute_clut: bool | None = None
    dvb_substream: bool | None = None
    palette: bool | None = None
    ifo_palette: bool | None = None
    forced_subs_only: bool | None = None

@dataclass
class FfmpegMovTextDecoderAvoptionsParams:
    """Parameters for ffmpeg_mov_text_decoder_avoptions."""
    width: bool | None = None
    height: bool | None = None

@dataclass
class FfmpegPgsSubtitleDecoderAvoptionsParams:
    """Parameters for ffmpeg_pgs_subtitle_decoder_avoptions."""
    forced_subs_only: bool | None = None
    keep_ass_markup: bool | None = None
    keep_ass_markup: bool | None = None
    keep_ass_markup: bool | None = None
    keep_ass_markup: bool | None = None
    keep_ass_markup: bool | None = None
    tilethreads: bool | None = None
    framethreads: bool | None = None
    filmgrain: bool | None = None
    oppoint: bool | None = None
    alllayers: bool | None = None
    lowqual: bool | None = None
    apply_phase_inv: bool | None = None

@dataclass
class FfmpegLibrsvgAvoptionsParams:
    """Parameters for ffmpeg_librsvg_avoptions."""
    width: bool | None = None
    height: bool | None = None
    keep_ar: bool | None = None
    txt_page: bool | None = None
    txt_chop_top: bool | None = None
    txt_format: bool | None = None
    txt_left: bool | None = None
    txt_top: bool | None = None
    txt_chop_spaces: bool | None = None
    txt_duration: bool | None = None
    txt_transparent: bool | None = None
    txt_opacity: bool | None = None
    operating_point: bool | None = None
    deint: bool | None = None
    gpu: bool | None = None
    surfaces: bool | None = None
    crop: bool | None = None
    resize: bool | None = None
    async_depth: bool | None = None
    gpu_copy: bool | None = None
    deint: bool | None = None
    gpu: bool | None = None
    surfaces: bool | None = None
    crop: bool | None = None
    resize: bool | None = None
    deint: bool | None = None
    gpu: bool | None = None
    surfaces: bool | None = None
    crop: bool | None = None
    resize: bool | None = None
    deint: bool | None = None
    gpu: bool | None = None
    surfaces: bool | None = None
    crop: bool | None = None
    resize: bool | None = None
    async_depth: bool | None = None
    gpu_copy: bool | None = None
    deint: bool | None = None
    gpu: bool | None = None
    surfaces: bool | None = None
    crop: bool | None = None
    resize: bool | None = None
    deint: bool | None = None
    gpu: bool | None = None
    surfaces: bool | None = None
    crop: bool | None = None
    resize: bool | None = None
    deint: bool | None = None
    gpu: bool | None = None
    surfaces: bool | None = None
    crop: bool | None = None
    resize: bool | None = None
    deint: bool | None = None
    gpu: bool | None = None
    surfaces: bool | None = None
    crop: bool | None = None
    resize: bool | None = None
    deint: bool | None = None
    gpu: bool | None = None
    surfaces: bool | None = None
    crop: bool | None = None
    resize: bool | None = None
    async_depth: bool | None = None
    gpu_copy: bool | None = None
    deint: bool | None = None
    gpu: bool | None = None
    surfaces: bool | None = None
    crop: bool | None = None
    resize: bool | None = None
    async_depth: bool | None = None
    gpu_copy: bool | None = None

@dataclass
class FfmpegAvformatcontextAvoptionsParams:
    """Parameters for ffmpeg_avformatcontext_avoptions."""
    avioflags: bool | None = None
    probesize: bool | None = None
    formatprobesize: bool | None = None
    packetsize: bool | None = None
    fflags: bool | None = None
    seek2any: bool | None = None
    analyzeduration: bool | None = None
    cryptokey: bool | None = None
    indexmem: bool | None = None
    rtbufsize: bool | None = None
    fdebug: bool | None = None
    max_delay: bool | None = None
    fpsprobesize: bool | None = None
    audio_preload: bool | None = None
    chunk_duration: bool | None = None
    chunk_size: bool | None = None
    f_err_detect: bool | None = None
    err_detect: bool | None = None
    flush_packets: bool | None = None
    output_ts_offset: bool | None = None
    f_strict: bool | None = None
    strict: bool | None = None
    max_ts_probe: bool | None = None
    dump_separator: bool | None = None
    codec_whitelist: bool | None = None
    format_whitelist: bool | None = None
    max_streams: bool | None = None

@dataclass
class FfmpegUrlcontextAvoptionsParams:
    """Parameters for ffmpeg_urlcontext_avoptions."""
    rw_timeout: bool | None = None

@dataclass
class FfmpegAsyncAvoptionsParams:
    """Parameters for ffmpeg_async_avoptions."""
    playlist: bool | None = None
    angle: bool | None = None
    chapter: bool | None = None
    read_ahead_limit: bool | None = None
    key: bool | None = None
    iv: bool | None = None
    decryption_key: bool | None = None
    decryption_iv: bool | None = None
    encryption_key: bool | None = None
    encryption_iv: bool | None = None
    ffrtmphttp_tls: bool | None = None
    truncate: bool | None = None
    blocksize: bool | None = None
    follow: bool | None = None
    seekable: bool | None = None
    timeout: bool | None = None
    seekable: bool | None = None
    chunked_post: bool | None = None
    http_proxy: bool | None = None
    headers: bool | None = None
    content_type: bool | None = None
    user_agent: bool | None = None
    referer: bool | None = None
    post_data: bool | None = None
    cookies: bool | None = None
    icy: bool | None = None
    auth_type: bool | None = None
    send_expect_100: bool | None = None
    location: bool | None = None
    offset: bool | None = None
    end_offset: bool | None = None
    method: bool | None = None
    reconnect: bool | None = None
    reconnect_at_eof: bool | None = None
    listen: bool | None = None
    resource: bool | None = None
    reply_code: bool | None = None
    seekable: bool | None = None
    chunked_post: bool | None = None
    http_proxy: bool | None = None
    headers: bool | None = None
    content_type: bool | None = None
    user_agent: bool | None = None
    referer: bool | None = None
    post_data: bool | None = None
    cookies: bool | None = None
    icy: bool | None = None
    auth_type: bool | None = None
    send_expect_100: bool | None = None
    location: bool | None = None
    offset: bool | None = None
    end_offset: bool | None = None
    method: bool | None = None
    reconnect: bool | None = None
    reconnect_at_eof: bool | None = None
    listen: bool | None = None
    resource: bool | None = None
    reply_code: bool | None = None
    ice_genre: bool | None = None
    ice_name: bool | None = None
    ice_description: bool | None = None
    ice_url: bool | None = None
    ice_public: bool | None = None
    user_agent: bool | None = None
    password: bool | None = None
    content_type: bool | None = None
    legacy_icecast: bool | None = None
    tls: bool | None = None
    blocksize: bool | None = None
    ttl: bool | None = None
    l: bool | None = None
    d: bool | None = None
    rtmp_app: bool | None = None
    rtmp_buffer: bool | None = None
    rtmp_conn: bool | None = None
    rtmp_flashver: bool | None = None
    rtmp_live: bool | None = None
    rtmp_pageurl: bool | None = None
    rtmp_playpath: bool | None = None
    rtmp_subscribe: bool | None = None
    rtmp_swfhash: bool | None = None
    rtmp_swfsize: bool | None = None
    rtmp_swfurl: bool | None = None
    rtmp_swfverify: bool | None = None
    rtmp_tcurl: bool | None = None
    rtmp_listen: bool | None = None
    listen: bool | None = None
    timeout: bool | None = None
    rtmp_app: bool | None = None
    rtmp_buffer: bool | None = None
    rtmp_conn: bool | None = None
    rtmp_flashver: bool | None = None
    rtmp_live: bool | None = None
    rtmp_pageurl: bool | None = None
    rtmp_playpath: bool | None = None
    rtmp_subscribe: bool | None = None
    rtmp_swfhash: bool | None = None
    rtmp_swfsize: bool | None = None
    rtmp_swfurl: bool | None = None
    rtmp_swfverify: bool | None = None
    rtmp_tcurl: bool | None = None
    rtmp_listen: bool | None = None
    listen: bool | None = None
    timeout: bool | None = None
    rtmp_app: bool | None = None
    rtmp_buffer: bool | None = None
    rtmp_conn: bool | None = None
    rtmp_flashver: bool | None = None
    rtmp_live: bool | None = None
    rtmp_pageurl: bool | None = None
    rtmp_playpath: bool | None = None
    rtmp_subscribe: bool | None = None
    rtmp_swfhash: bool | None = None
    rtmp_swfsize: bool | None = None
    rtmp_swfurl: bool | None = None
    rtmp_swfverify: bool | None = None
    rtmp_tcurl: bool | None = None
    rtmp_listen: bool | None = None
    listen: bool | None = None
    timeout: bool | None = None
    rtmp_app: bool | None = None
    rtmp_buffer: bool | None = None
    rtmp_conn: bool | None = None
    rtmp_flashver: bool | None = None
    rtmp_live: bool | None = None
    rtmp_pageurl: bool | None = None
    rtmp_playpath: bool | None = None
    rtmp_subscribe: bool | None = None
    rtmp_swfhash: bool | None = None
    rtmp_swfsize: bool | None = None
    rtmp_swfurl: bool | None = None
    rtmp_swfverify: bool | None = None
    rtmp_tcurl: bool | None = None
    rtmp_listen: bool | None = None
    listen: bool | None = None
    timeout: bool | None = None
    ttl: bool | None = None
    buffer_size: bool | None = None
    rtcp_port: bool | None = None
    local_rtpport: bool | None = None
    local_rtcpport: bool | None = None
    connect: bool | None = None
    write_to_source: bool | None = None
    pkt_size: bool | None = None
    dscp: bool | None = None
    timeout: bool | None = None
    sources: bool | None = None
    block: bool | None = None
    fec: bool | None = None
    listen: bool | None = None
    timeout: bool | None = None
    listen_timeout: bool | None = None
    max_streams: bool | None = None
    srtp_out_suite: bool | None = None
    srtp_out_params: bool | None = None
    srtp_in_suite: bool | None = None
    srtp_in_params: bool | None = None
    start: bool | None = None
    end: bool | None = None
    listen: bool | None = None
    timeout: bool | None = None
    listen_timeout: bool | None = None
    send_buffer_size: bool | None = None
    recv_buffer_size: bool | None = None
    tcp_nodelay: bool | None = None
    tcp_mss: bool | None = None
    ca_file: bool | None = None
    cafile: bool | None = None
    tls_verify: bool | None = None
    cert_file: bool | None = None
    key_file: bool | None = None
    listen: bool | None = None
    verifyhost: bool | None = None
    http_proxy: bool | None = None
    buffer_size: bool | None = None
    bitrate: bool | None = None
    burst_bits: bool | None = None
    localport: bool | None = None
    local_port: bool | None = None
    localaddr: bool | None = None
    udplite_coverage: bool | None = None
    pkt_size: bool | None = None
    reuse: bool | None = None
    reuse_socket: bool | None = None
    broadcast: bool | None = None
    ttl: bool | None = None
    connect: bool | None = None
    fifo_size: bool | None = None
    overrun_nonfatal: bool | None = None
    timeout: bool | None = None
    sources: bool | None = None
    block: bool | None = None
    buffer_size: bool | None = None
    bitrate: bool | None = None
    burst_bits: bool | None = None
    localport: bool | None = None
    local_port: bool | None = None
    localaddr: bool | None = None
    udplite_coverage: bool | None = None
    pkt_size: bool | None = None
    reuse: bool | None = None
    reuse_socket: bool | None = None
    broadcast: bool | None = None
    ttl: bool | None = None
    connect: bool | None = None
    fifo_size: bool | None = None
    overrun_nonfatal: bool | None = None
    timeout: bool | None = None
    sources: bool | None = None
    block: bool | None = None
    listen: bool | None = None
    timeout: bool | None = None
    type: bool | None = None
    pkt_size: bool | None = None
    exchange: bool | None = None
    routing_key: bool | None = None
    delivery_mode: bool | None = None
    timeout: bool | None = None
    listen_timeout: bool | None = None
    send_buffer_size: bool | None = None
    recv_buffer_size: bool | None = None
    pkt_size: bool | None = None
    payload_size: bool | None = None
    maxbw: bool | None = None
    pbkeylen: bool | None = None
    passphrase: bool | None = None
    kmrefreshrate: bool | None = None
    kmpreannounce: bool | None = None
    mss: bool | None = None
    ffs: bool | None = None
    ipttl: bool | None = None
    iptos: bool | None = None
    inputbw: bool | None = None
    oheadbw: bool | None = None
    latency: bool | None = None
    tsbpddelay: bool | None = None
    rcvlatency: bool | None = None
    peerlatency: bool | None = None
    tlpktdrop: bool | None = None
    nakreport: bool | None = None
    connect_timeout: bool | None = None
    mode: bool | None = None
    sndbuf: bool | None = None
    rcvbuf: bool | None = None
    lossmaxttl: bool | None = None
    minversion: bool | None = None
    streamid: bool | None = None
    smoother: bool | None = None
    messageapi: bool | None = None
    transtype: bool | None = None
    linger: bool | None = None
    timeout: bool | None = None
    truncate: bool | None = None
    private_key: bool | None = None
    pkt_size: bool | None = None

@dataclass
class FfmpegAdtsMuxerAvoptionsParams:
    """Parameters for ffmpeg_adts_muxer_avoptions."""
    write_id3v2: bool | None = None
    write_apetag: bool | None = None
    write_mpeg2: bool | None = None

@dataclass
class FfmpegAiffMuxerAvoptionsParams:
    """Parameters for ffmpeg_aiff_muxer_avoptions."""
    write_id3v2: bool | None = None
    id3v2_version: bool | None = None
    type: bool | None = None

@dataclass
class FfmpegApngMuxerAvoptionsParams:
    """Parameters for ffmpeg_apng_muxer_avoptions."""
    plays: bool | None = None
    final_delay: bool | None = None
    version_major: bool | None = None
    version_minor: bool | None = None
    name: bool | None = None

@dataclass
class FfmpegAsfMuxerAvoptionsParams:
    """Parameters for ffmpeg_asf_muxer_avoptions."""
    packet_size: bool | None = None
    ignore_readorder: bool | None = None

@dataclass
class FfmpegAstMuxerAvoptionsParams:
    """Parameters for ffmpeg_ast_muxer_avoptions."""
    loopstart: bool | None = None
    loopend: bool | None = None

@dataclass
class FfmpegAsfStreamMuxerAvoptionsParams:
    """Parameters for ffmpeg_asf_stream_muxer_avoptions."""
    packet_size: bool | None = None

@dataclass
class FfmpegAviMuxerAvoptionsParams:
    """Parameters for ffmpeg_avi_muxer_avoptions."""
    flipped_raw_rgb: bool | None = None
    adaptation_sets: bool | None = None
    window_size: bool | None = None
    min_seg_duration: bool | None = None
    seg_duration: bool | None = None
    frag_duration: bool | None = None
    frag_type: bool | None = None
    remove_at_exit: bool | None = None
    use_template: bool | None = None
    use_timeline: bool | None = None
    single_file: bool | None = None
    single_file_name: bool | None = None
    init_seg_name: bool | None = None
    media_seg_name: bool | None = None
    utc_timing_url: bool | None = None
    method: bool | None = None
    http_user_agent: bool | None = None
    http_persistent: bool | None = None
    hls_playlist: bool | None = None
    hls_master_name: bool | None = None
    streaming: bool | None = None
    timeout: bool | None = None
    index_correction: bool | None = None
    format_options: bool | None = None
    global_sidx: bool | None = None
    ignore_io_errors: bool | None = None
    lhls: bool | None = None
    ldash: bool | None = None
    write_prft: bool | None = None
    mpd_profile: bool | None = None
    http_opts: bool | None = None
    target_latency: bool | None = None
    update_period: bool | None = None
    movflags: bool | None = None
    moov_size: bool | None = None
    rtpflags: bool | None = None
    skip_iods: bool | None = None
    frag_duration: bool | None = None
    frag_size: bool | None = None
    ism_lookahead: bool | None = None
    brand: bool | None = None
    use_editlist: bool | None = None
    fragment_index: bool | None = None
    mov_gamma: bool | None = None
    frag_interleave: bool | None = None
    encryption_key: bool | None = None
    encryption_kid: bool | None = None
    write_tmcd: bool | None = None
    write_prft: bool | None = None
    empty_hdlr_name: bool | None = None

@dataclass
class FfmpegFifoMuxerAvoptionsParams:
    """Parameters for ffmpeg_fifo_muxer_avoptions."""
    fifo_format: bool | None = None
    queue_size: bool | None = None
    format_opts: bool | None = None
    attempt_recovery: bool | None = None
    timeshift: bool | None = None

@dataclass
class FfmpegFifoTestMuxerAvoptionsParams:
    """Parameters for ffmpeg_fifo_test_muxer_avoptions."""
    write_header_ret: bool | None = None
    write_header: bool | None = None
    flvflags: bool | None = None
    hash: bool | None = None
    format_version: bool | None = None
    hash: bool | None = None
    format_version: bool | None = None

@dataclass
class FfmpegGifMuxerAvoptionsParams:
    """Parameters for ffmpeg_gif_muxer_avoptions."""
    loop: bool | None = None
    final_delay: bool | None = None
    hash: bool | None = None

@dataclass
class FfmpegHdsMuxerAvoptionsParams:
    """Parameters for ffmpeg_hds_muxer_avoptions."""
    window_size: bool | None = None
    remove_at_exit: bool | None = None
    start_number: bool | None = None
    hls_time: bool | None = None
    hls_init_time: bool | None = None
    hls_list_size: bool | None = None
    hls_ts_options: bool | None = None
    hls_vtt_options: bool | None = None
    hls_wrap: bool | None = None
    hls_allow_cache: bool | None = None
    hls_base_url: bool | None = None
    hls_segment_size: bool | None = None
    hls_enc: bool | None = None
    hls_enc_key: bool | None = None
    hls_enc_key_url: bool | None = None
    hls_enc_iv: bool | None = None
    hls_segment_type: bool | None = None
    hls_flags: bool | None = None
    use_localtime: bool | None = None
    strftime: bool | None = None
    strftime_mkdir: bool | None = None
    method: bool | None = None
    http_user_agent: bool | None = None
    var_stream_map: bool | None = None
    cc_stream_map: bool | None = None
    master_pl_name: bool | None = None
    http_persistent: bool | None = None
    timeout: bool | None = None
    ignore_io_errors: bool | None = None
    headers: bool | None = None
    update: bool | None = None
    start_number: bool | None = None
    strftime: bool | None = None
    frame_pts: bool | None = None
    atomic_writing: bool | None = None
    protocol_opts: bool | None = None
    movflags: bool | None = None
    moov_size: bool | None = None
    rtpflags: bool | None = None
    skip_iods: bool | None = None
    frag_duration: bool | None = None
    frag_size: bool | None = None
    ism_lookahead: bool | None = None
    brand: bool | None = None
    use_editlist: bool | None = None
    fragment_index: bool | None = None
    mov_gamma: bool | None = None
    frag_interleave: bool | None = None
    encryption_key: bool | None = None
    encryption_kid: bool | None = None
    write_tmcd: bool | None = None
    write_prft: bool | None = None
    empty_hdlr_name: bool | None = None
    movflags: bool | None = None
    moov_size: bool | None = None
    rtpflags: bool | None = None
    skip_iods: bool | None = None
    frag_duration: bool | None = None
    frag_size: bool | None = None
    ism_lookahead: bool | None = None
    brand: bool | None = None
    use_editlist: bool | None = None
    fragment_index: bool | None = None
    mov_gamma: bool | None = None
    frag_interleave: bool | None = None
    encryption_key: bool | None = None
    encryption_kid: bool | None = None
    write_tmcd: bool | None = None
    write_prft: bool | None = None
    empty_hdlr_name: bool | None = None

@dataclass
class FfmpegLatmLoasMuxerAvoptionsParams:
    """Parameters for ffmpeg_latm_loas_muxer_avoptions."""
    hash: bool | None = None
    dash: bool | None = None
    live: bool | None = None
    allow_raw_vfw: bool | None = None
    flipped_raw_rgb: bool | None = None
    write_crc32: bool | None = None
    default_mode: bool | None = None
    dash: bool | None = None
    live: bool | None = None
    allow_raw_vfw: bool | None = None
    flipped_raw_rgb: bool | None = None
    write_crc32: bool | None = None
    default_mode: bool | None = None
    movflags: bool | None = None
    moov_size: bool | None = None
    rtpflags: bool | None = None
    skip_iods: bool | None = None
    frag_duration: bool | None = None
    frag_size: bool | None = None
    ism_lookahead: bool | None = None
    brand: bool | None = None
    use_editlist: bool | None = None
    fragment_index: bool | None = None
    mov_gamma: bool | None = None
    frag_interleave: bool | None = None
    encryption_key: bool | None = None
    encryption_kid: bool | None = None
    write_tmcd: bool | None = None
    write_prft: bool | None = None
    empty_hdlr_name: bool | None = None
    id3v2_version: bool | None = None
    write_id3v1: bool | None = None
    write_xing: bool | None = None
    movflags: bool | None = None
    moov_size: bool | None = None
    rtpflags: bool | None = None
    skip_iods: bool | None = None
    frag_duration: bool | None = None
    frag_size: bool | None = None
    ism_lookahead: bool | None = None
    brand: bool | None = None
    use_editlist: bool | None = None
    fragment_index: bool | None = None
    mov_gamma: bool | None = None
    frag_interleave: bool | None = None
    encryption_key: bool | None = None
    encryption_kid: bool | None = None
    write_tmcd: bool | None = None
    write_prft: bool | None = None
    empty_hdlr_name: bool | None = None
    muxrate: bool | None = None
    preload: bool | None = None
    muxrate: bool | None = None
    preload: bool | None = None
    muxrate: bool | None = None
    preload: bool | None = None
    muxrate: bool | None = None
    preload: bool | None = None
    muxrate: bool | None = None
    preload: bool | None = None

@dataclass
class FfmpegMpegtsMuxerAvoptionsParams:
    """Parameters for ffmpeg_mpegts_muxer_avoptions."""
    mpegts_start_pid: bool | None = None
    mpegts_m2ts_mode: bool | None = None
    muxrate: bool | None = None
    pes_payload_size: bool | None = None
    mpegts_flags: bool | None = None
    mpegts_copyts: bool | None = None
    tables_version: bool | None = None
    pcr_period: bool | None = None
    pat_period: bool | None = None
    sdt_period: bool | None = None
    boundary_tag: bool | None = None

@dataclass
class FfmpegMxfMuxerAvoptionsParams:
    """Parameters for ffmpeg_mxf_muxer_avoptions."""
    signal_standard: bool | None = None
    d10_channelcount: bool | None = None
    signal_standard: bool | None = None

@dataclass
class FfmpegMxfOpatomMuxerAvoptionsParams:
    """Parameters for ffmpeg_mxf_opatom_muxer_avoptions."""
    signal_standard: bool | None = None
    syncpoints: bool | None = None
    write_index: bool | None = None

@dataclass
class FfmpegOggAudioMuxerAvoptionsParams:
    """Parameters for ffmpeg_ogg_audio_muxer_avoptions."""
    serial_offset: bool | None = None
    oggpagesize: bool | None = None
    pagesize: bool | None = None
    page_duration: bool | None = None

@dataclass
class FfmpegOggMuxerAvoptionsParams:
    """Parameters for ffmpeg_ogg_muxer_avoptions."""
    serial_offset: bool | None = None
    oggpagesize: bool | None = None
    pagesize: bool | None = None
    page_duration: bool | None = None

@dataclass
class FfmpegOggVideoMuxerAvoptionsParams:
    """Parameters for ffmpeg_ogg_video_muxer_avoptions."""
    serial_offset: bool | None = None
    oggpagesize: bool | None = None
    pagesize: bool | None = None
    page_duration: bool | None = None

@dataclass
class FfmpegOggOpusMuxerAvoptionsParams:
    """Parameters for ffmpeg_ogg_opus_muxer_avoptions."""
    serial_offset: bool | None = None
    oggpagesize: bool | None = None
    pagesize: bool | None = None
    page_duration: bool | None = None
    movflags: bool | None = None
    moov_size: bool | None = None
    rtpflags: bool | None = None
    skip_iods: bool | None = None
    frag_duration: bool | None = None
    frag_size: bool | None = None
    ism_lookahead: bool | None = None
    brand: bool | None = None
    use_editlist: bool | None = None
    fragment_index: bool | None = None
    mov_gamma: bool | None = None
    frag_interleave: bool | None = None
    encryption_key: bool | None = None
    encryption_kid: bool | None = None
    write_tmcd: bool | None = None
    write_prft: bool | None = None
    empty_hdlr_name: bool | None = None

@dataclass
class FfmpegRtpMuxerAvoptionsParams:
    """Parameters for ffmpeg_rtp_muxer_avoptions."""
    rtpflags: bool | None = None
    payload_type: bool | None = None
    ssrc: bool | None = None
    cname: bool | None = None
    seq: bool | None = None

@dataclass
class FfmpegRtspMuxerAvoptionsParams:
    """Parameters for ffmpeg_rtsp_muxer_avoptions."""
    initial_pause: bool | None = None
    rtpflags: bool | None = None
    rtsp_transport: bool | None = None
    rtsp_flags: bool | None = None
    min_port: bool | None = None
    max_port: bool | None = None
    listen_timeout: bool | None = None
    timeout: bool | None = None
    stimeout: bool | None = None
    buffer_size: bool | None = None
    pkt_size: bool | None = None
    user_agent: bool | None = None
    reference_stream: bool | None = None
    segment_format: bool | None = None
    segment_list: bool | None = None
    segment_time: bool | None = None
    segment_times: bool | None = None
    segment_frames: bool | None = None
    segment_wrap: bool | None = None
    strftime: bool | None = None
    increment_tc: bool | None = None
    reset_timestamps: bool | None = None
    initial_offset: bool | None = None
    reference_stream: bool | None = None
    segment_format: bool | None = None
    segment_list: bool | None = None
    segment_time: bool | None = None
    segment_times: bool | None = None
    segment_frames: bool | None = None
    segment_wrap: bool | None = None
    strftime: bool | None = None
    increment_tc: bool | None = None
    reset_timestamps: bool | None = None
    initial_offset: bool | None = None
    window_size: bool | None = None
    lookahead_count: bool | None = None
    remove_at_exit: bool | None = None

@dataclass
class FfmpegOggSpeexMuxerAvoptionsParams:
    """Parameters for ffmpeg_ogg_speex_muxer_avoptions."""
    serial_offset: bool | None = None
    oggpagesize: bool | None = None
    pagesize: bool | None = None
    page_duration: bool | None = None
    spdif_flags: bool | None = None
    dtshd_rate: bool | None = None
    hash: bool | None = None

@dataclass
class FfmpegTeeMuxerAvoptionsParams:
    """Parameters for ffmpeg_tee_muxer_avoptions."""
    use_fifo: bool | None = None
    fifo_options: bool | None = None
    movflags: bool | None = None
    moov_size: bool | None = None
    rtpflags: bool | None = None
    skip_iods: bool | None = None
    frag_duration: bool | None = None
    frag_size: bool | None = None
    ism_lookahead: bool | None = None
    brand: bool | None = None
    use_editlist: bool | None = None
    fragment_index: bool | None = None
    mov_gamma: bool | None = None
    frag_interleave: bool | None = None
    encryption_key: bool | None = None
    encryption_kid: bool | None = None
    write_tmcd: bool | None = None
    write_prft: bool | None = None
    empty_hdlr_name: bool | None = None
    movflags: bool | None = None
    moov_size: bool | None = None
    rtpflags: bool | None = None
    skip_iods: bool | None = None
    frag_duration: bool | None = None
    frag_size: bool | None = None
    ism_lookahead: bool | None = None
    brand: bool | None = None
    use_editlist: bool | None = None
    fragment_index: bool | None = None
    mov_gamma: bool | None = None
    frag_interleave: bool | None = None
    encryption_key: bool | None = None
    encryption_kid: bool | None = None
    write_tmcd: bool | None = None
    write_prft: bool | None = None
    empty_hdlr_name: bool | None = None

@dataclass
class FfmpegWavMuxerAvoptionsParams:
    """Parameters for ffmpeg_wav_muxer_avoptions."""
    write_bext: bool | None = None
    write_peak: bool | None = None
    rf64: bool | None = None
    peak_block_size: bool | None = None
    peak_format: bool | None = None
    peak_ppv: bool | None = None
    dash: bool | None = None
    live: bool | None = None
    allow_raw_vfw: bool | None = None
    flipped_raw_rgb: bool | None = None
    write_crc32: bool | None = None
    default_mode: bool | None = None

@dataclass
class FfmpegWebmDashManifestMuxerAvoptionsParams:
    """Parameters for ffmpeg_webm_dash_manifest_muxer_avoptions."""
    adaptation_sets: bool | None = None
    live: bool | None = None
    utc_timing_url: bool | None = None

@dataclass
class FfmpegWebmChunkMuxerAvoptionsParams:
    """Parameters for ffmpeg_webm_chunk_muxer_avoptions."""
    header: bool | None = None
    method: bool | None = None

@dataclass
class FfmpegWebpMuxerAvoptionsParams:
    """Parameters for ffmpeg_webp_muxer_avoptions."""
    loop: bool | None = None
    algorithm: bool | None = None
    fp_format: bool | None = None
    window_size: bool | None = None
    window_title: bool | None = None
    driver: bool | None = None
    algorithm: bool | None = None
    antialias: bool | None = None
    charset: bool | None = None
    color: bool | None = None
    list_drivers: bool | None = None
    list_dither: bool | None = None
    xoffset: bool | None = None
    yoffset: bool | None = None
    background: bool | None = None
    no_window: bool | None = None
    window_title: bool | None = None
    window_size: bool | None = None

@dataclass
class FfmpegPulseaudioOutdevAvoptionsParams:
    """Parameters for ffmpeg_pulseaudio_outdev_avoptions."""
    server: bool | None = None
    name: bool | None = None
    stream_name: bool | None = None
    device: bool | None = None
    buffer_size: bool | None = None
    buffer_duration: bool | None = None
    prebuf: bool | None = None
    minreq: bool | None = None
    window_title: bool | None = None
    window_size: bool | None = None
    window_x: bool | None = None
    window_y: bool | None = None
    display_name: bool | None = None
    window_id: bool | None = None
    window_size: bool | None = None
    window_title: bool | None = None
    window_x: bool | None = None
    window_y: bool | None = None
    aa_fixed_key: bool | None = None
    raw_packet_size: bool | None = None
    raw_packet_size: bool | None = None

@dataclass
class FfmpegArtworxDataFormatDemuxerAvoptionsParams:
    """Parameters for ffmpeg_artworx_data_format_demuxer_avoptions."""
    linespeed: bool | None = None
    video_size: bool | None = None
    framerate: bool | None = None

@dataclass
class FfmpegApngDemuxerAvoptionsParams:
    """Parameters for ffmpeg_apng_demuxer_avoptions."""
    ignore_loop: bool | None = None
    max_fps: bool | None = None
    default_fps: bool | None = None
    sample_rate: bool | None = None
    sample_rate: bool | None = None
    subfps: bool | None = None
    no_resync_search: bool | None = None
    export_xmp: bool | None = None
    framerate: bool | None = None
    use_odml: bool | None = None
    framerate: bool | None = None
    raw_packet_size: bool | None = None
    framerate: bool | None = None
    raw_packet_size: bool | None = None

@dataclass
class FfmpegBinaryTextDemuxerAvoptionsParams:
    """Parameters for ffmpeg_binary_text_demuxer_avoptions."""
    linespeed: bool | None = None
    video_size: bool | None = None
    framerate: bool | None = None
    framerate: bool | None = None
    raw_packet_size: bool | None = None

@dataclass
class FfmpegCdxlDemuxerAvoptionsParams:
    """Parameters for ffmpeg_cdxl_demuxer_avoptions."""
    sample_rate: bool | None = None
    frame_rate: bool | None = None
    mode: bool | None = None
    safe: bool | None = None
    auto_convert: bool | None = None
    raw_packet_size: bool | None = None
    framerate: bool | None = None
    raw_packet_size: bool | None = None
    framerate: bool | None = None
    raw_packet_size: bool | None = None
    raw_packet_size: bool | None = None
    raw_packet_size: bool | None = None
    raw_packet_size: bool | None = None
    raw_packet_size: bool | None = None

@dataclass
class FfmpegFitsDemuxerAvoptionsParams:
    """Parameters for ffmpeg_fits_demuxer_avoptions."""
    framerate: bool | None = None
    raw_packet_size: bool | None = None
    flv_metadata: bool | None = None
    missing_streams: bool | None = None
    flv_metadata: bool | None = None
    missing_streams: bool | None = None
    raw_packet_size: bool | None = None
    code_size: bool | None = None
    sample_rate: bool | None = None
    code_size: bool | None = None
    sample_rate: bool | None = None
    bit_rate: bool | None = None

@dataclass
class FfmpegGifDemuxerAvoptionsParams:
    """Parameters for ffmpeg_gif_demuxer_avoptions."""
    min_delay: bool | None = None
    max_gif_delay: bool | None = None
    default_delay: bool | None = None
    ignore_loop: bool | None = None
    sample_rate: bool | None = None
    framerate: bool | None = None
    raw_packet_size: bool | None = None
    framerate: bool | None = None
    raw_packet_size: bool | None = None
    framerate: bool | None = None
    raw_packet_size: bool | None = None
    framerate: bool | None = None
    raw_packet_size: bool | None = None
    live_start_index: bool | None = None
    max_reload: bool | None = None
    http_persistent: bool | None = None
    http_multiple: bool | None = None
    http_seekable: bool | None = None
    linespeed: bool | None = None
    video_size: bool | None = None
    framerate: bool | None = None
    pattern_type: bool | None = None
    start_number: bool | None = None
    ts_from_file: bool | None = None
    framerate: bool | None = None
    pixel_format: bool | None = None
    video_size: bool | None = None
    loop: bool | None = None
    frame_size: bool | None = None
    framerate: bool | None = None
    pixel_format: bool | None = None
    video_size: bool | None = None
    loop: bool | None = None
    pattern_type: bool | None = None
    start_number: bool | None = None
    ts_from_file: bool | None = None
    framerate: bool | None = None
    pixel_format: bool | None = None
    video_size: bool | None = None
    loop: bool | None = None
    pattern_type: bool | None = None
    start_number: bool | None = None
    ts_from_file: bool | None = None
    framerate: bool | None = None
    pixel_format: bool | None = None
    video_size: bool | None = None
    loop: bool | None = None
    framerate: bool | None = None
    raw_packet_size: bool | None = None
    raw_packet_size: bool | None = None
    flv_metadata: bool | None = None
    missing_streams: bool | None = None
    raw_packet_size: bool | None = None
    framerate: bool | None = None
    raw_packet_size: bool | None = None
    subfps: bool | None = None
    framerate: bool | None = None
    raw_packet_size: bool | None = None
    framerate: bool | None = None
    raw_packet_size: bool | None = None
    raw_packet_size: bool | None = None
    ignore_editlist: bool | None = None
    ignore_chapters: bool | None = None
    use_mfra_for: bool | None = None
    export_all: bool | None = None
    export_xmp: bool | None = None
    activation_bytes: bool | None = None
    audible_key: bool | None = None
    audible_iv: bool | None = None
    decryption_key: bool | None = None
    enable_drefs: bool | None = None
    usetoc: bool | None = None
    resync_size: bool | None = None
    fix_teletext_pts: bool | None = None
    ts_packetsize: bool | None = None
    scan_all_pmts: bool | None = None
    skip_unknown_pmt: bool | None = None
    resync_size: bool | None = None
    compute_pcr: bool | None = None
    ts_packetsize: bool | None = None
    framerate: bool | None = None
    raw_packet_size: bool | None = None

@dataclass
class FfmpegMpjpegDemuxerAvoptionsParams:
    """Parameters for ffmpeg_mpjpeg_demuxer_avoptions."""
    eia608_extract: bool | None = None
    framerate: bool | None = None
    sample_rate: bool | None = None
    channels: bool | None = None
    sample_rate: bool | None = None
    channels: bool | None = None
    sample_rate: bool | None = None
    channels: bool | None = None
    sample_rate: bool | None = None
    channels: bool | None = None
    sample_rate: bool | None = None
    channels: bool | None = None
    sample_rate: bool | None = None
    channels: bool | None = None
    sample_rate: bool | None = None
    channels: bool | None = None
    sample_rate: bool | None = None
    channels: bool | None = None
    sample_rate: bool | None = None
    channels: bool | None = None
    sample_rate: bool | None = None
    channels: bool | None = None
    sample_rate: bool | None = None
    channels: bool | None = None
    sample_rate: bool | None = None
    channels: bool | None = None
    sample_rate: bool | None = None
    channels: bool | None = None
    sample_rate: bool | None = None
    channels: bool | None = None
    sample_rate: bool | None = None
    channels: bool | None = None
    sample_rate: bool | None = None
    channels: bool | None = None
    sample_rate: bool | None = None
    channels: bool | None = None
    sample_rate: bool | None = None
    channels: bool | None = None
    sample_rate: bool | None = None
    channels: bool | None = None
    sample_rate: bool | None = None
    channels: bool | None = None
    sample_rate: bool | None = None
    channels: bool | None = None
    video_size: bool | None = None
    pixel_format: bool | None = None
    framerate: bool | None = None

@dataclass
class FfmpegRtpDemuxerAvoptionsParams:
    """Parameters for ffmpeg_rtp_demuxer_avoptions."""
    rtp_flags: bool | None = None
    listen_timeout: bool | None = None
    buffer_size: bool | None = None
    pkt_size: bool | None = None

@dataclass
class FfmpegRtspDemuxerAvoptionsParams:
    """Parameters for ffmpeg_rtsp_demuxer_avoptions."""
    initial_pause: bool | None = None
    rtpflags: bool | None = None
    rtsp_transport: bool | None = None
    rtsp_flags: bool | None = None
    min_port: bool | None = None
    max_port: bool | None = None
    listen_timeout: bool | None = None
    timeout: bool | None = None
    stimeout: bool | None = None
    buffer_size: bool | None = None
    pkt_size: bool | None = None
    user_agent: bool | None = None
    raw_packet_size: bool | None = None
    sample_rate: bool | None = None
    frame_size: bool | None = None
    max_file_size: bool | None = None

@dataclass
class FfmpegSdpDemuxerAvoptionsParams:
    """Parameters for ffmpeg_sdp_demuxer_avoptions."""
    sdp_flags: bool | None = None
    listen_timeout: bool | None = None
    buffer_size: bool | None = None
    pkt_size: bool | None = None
    framerate: bool | None = None
    raw_packet_size: bool | None = None
    sample_rate: bool | None = None
    channels: bool | None = None
    raw_packet_size: bool | None = None
    start_time: bool | None = None
    raw_packet_size: bool | None = None

@dataclass
class FfmpegTtyDemuxerAvoptionsParams:
    """Parameters for ffmpeg_tty_demuxer_avoptions."""
    chars_per_frame: bool | None = None
    video_size: bool | None = None
    framerate: bool | None = None
    video_size: bool | None = None
    framerate: bool | None = None
    video_size: bool | None = None
    framerate: bool | None = None
    framerate: bool | None = None
    raw_packet_size: bool | None = None
    sub_name: bool | None = None
    max_size: bool | None = None

@dataclass
class FfmpegWavDemuxerAvoptionsParams:
    """Parameters for ffmpeg_wav_demuxer_avoptions."""
    ignore_length: bool | None = None
    max_size: bool | None = None

@dataclass
class FfmpegWebmDashManifestDemuxerAvoptionsParams:
    """Parameters for ffmpeg_webm_dash_manifest_demuxer_avoptions."""
    live: bool | None = None
    bandwidth: bool | None = None

@dataclass
class FfmpegWebvttDemuxerAvoptionsParams:
    """Parameters for ffmpeg_webvtt_demuxer_avoptions."""
    kind: bool | None = None
    raw_packet_size: bool | None = None
    linespeed: bool | None = None
    video_size: bool | None = None
    framerate: bool | None = None
    frame_size: bool | None = None
    framerate: bool | None = None
    pixel_format: bool | None = None
    video_size: bool | None = None
    loop: bool | None = None
    frame_size: bool | None = None
    framerate: bool | None = None
    pixel_format: bool | None = None
    video_size: bool | None = None
    loop: bool | None = None
    frame_size: bool | None = None
    framerate: bool | None = None
    pixel_format: bool | None = None
    video_size: bool | None = None
    loop: bool | None = None
    frame_size: bool | None = None
    framerate: bool | None = None
    pixel_format: bool | None = None
    video_size: bool | None = None
    loop: bool | None = None
    frame_size: bool | None = None
    framerate: bool | None = None
    pixel_format: bool | None = None
    video_size: bool | None = None
    loop: bool | None = None
    frame_size: bool | None = None
    framerate: bool | None = None
    pixel_format: bool | None = None
    video_size: bool | None = None
    loop: bool | None = None
    frame_size: bool | None = None
    framerate: bool | None = None
    pixel_format: bool | None = None
    video_size: bool | None = None
    loop: bool | None = None
    frame_size: bool | None = None
    framerate: bool | None = None
    pixel_format: bool | None = None
    video_size: bool | None = None
    loop: bool | None = None
    frame_size: bool | None = None
    framerate: bool | None = None
    pixel_format: bool | None = None
    video_size: bool | None = None
    loop: bool | None = None
    frame_size: bool | None = None
    framerate: bool | None = None
    pixel_format: bool | None = None
    video_size: bool | None = None
    loop: bool | None = None
    frame_size: bool | None = None
    framerate: bool | None = None
    pixel_format: bool | None = None
    video_size: bool | None = None
    loop: bool | None = None
    frame_size: bool | None = None
    framerate: bool | None = None
    pixel_format: bool | None = None
    video_size: bool | None = None
    loop: bool | None = None
    frame_size: bool | None = None
    framerate: bool | None = None
    pixel_format: bool | None = None
    video_size: bool | None = None
    loop: bool | None = None
    frame_size: bool | None = None
    framerate: bool | None = None
    pixel_format: bool | None = None
    video_size: bool | None = None
    loop: bool | None = None
    frame_size: bool | None = None
    framerate: bool | None = None
    pixel_format: bool | None = None
    video_size: bool | None = None
    loop: bool | None = None
    frame_size: bool | None = None
    framerate: bool | None = None
    pixel_format: bool | None = None
    video_size: bool | None = None
    loop: bool | None = None
    frame_size: bool | None = None
    framerate: bool | None = None
    pixel_format: bool | None = None
    video_size: bool | None = None
    loop: bool | None = None
    frame_size: bool | None = None
    framerate: bool | None = None
    pixel_format: bool | None = None
    video_size: bool | None = None
    loop: bool | None = None
    frame_size: bool | None = None
    framerate: bool | None = None
    pixel_format: bool | None = None
    video_size: bool | None = None
    loop: bool | None = None
    frame_size: bool | None = None
    framerate: bool | None = None
    pixel_format: bool | None = None
    video_size: bool | None = None
    loop: bool | None = None
    frame_size: bool | None = None
    framerate: bool | None = None
    pixel_format: bool | None = None
    video_size: bool | None = None
    loop: bool | None = None
    frame_size: bool | None = None
    framerate: bool | None = None
    pixel_format: bool | None = None
    video_size: bool | None = None
    loop: bool | None = None
    frame_size: bool | None = None
    framerate: bool | None = None
    pixel_format: bool | None = None
    video_size: bool | None = None
    loop: bool | None = None
    frame_size: bool | None = None
    framerate: bool | None = None
    pixel_format: bool | None = None
    video_size: bool | None = None
    loop: bool | None = None
    frame_size: bool | None = None
    framerate: bool | None = None
    pixel_format: bool | None = None
    video_size: bool | None = None
    loop: bool | None = None
    frame_size: bool | None = None
    framerate: bool | None = None
    pixel_format: bool | None = None
    video_size: bool | None = None
    loop: bool | None = None
    frame_size: bool | None = None
    framerate: bool | None = None
    pixel_format: bool | None = None
    video_size: bool | None = None
    loop: bool | None = None
    frame_size: bool | None = None
    framerate: bool | None = None
    pixel_format: bool | None = None
    video_size: bool | None = None
    loop: bool | None = None
    frame_size: bool | None = None
    framerate: bool | None = None
    pixel_format: bool | None = None
    video_size: bool | None = None
    loop: bool | None = None

@dataclass
class FfmpegGameMusicEmuDemuxerAvoptionsParams:
    """Parameters for ffmpeg_game_music_emu_demuxer_avoptions."""
    track_index: bool | None = None
    sample_rate: bool | None = None
    max_size: bool | None = None
    sample_rate: bool | None = None
    layout: bool | None = None
    subsong: bool | None = None

@dataclass
class FfmpegAlsaIndevAvoptionsParams:
    """Parameters for ffmpeg_alsa_indev_avoptions."""
    sample_rate: bool | None = None
    channels: bool | None = None
    framerate: bool | None = None
    dvtype: bool | None = None
    dvbuffer: bool | None = None
    dvguid: bool | None = None

@dataclass
class FfmpegJackIndevAvoptionsParams:
    """Parameters for ffmpeg_jack_indev_avoptions."""
    channels: bool | None = None
    device: bool | None = None
    format: bool | None = None
    format_modifier: bool | None = None
    crtc_id: bool | None = None
    plane_id: bool | None = None
    framerate: bool | None = None
    graph: bool | None = None
    graph_file: bool | None = None
    dumpgraph: bool | None = None
    channels: bool | None = None
    sample_rate: bool | None = None
    sample_size: bool | None = None
    list_devices: bool | None = None

@dataclass
class FfmpegOssIndevAvoptionsParams:
    """Parameters for ffmpeg_oss_indev_avoptions."""
    sample_rate: bool | None = None
    channels: bool | None = None

@dataclass
class FfmpegPulseIndevAvoptionsParams:
    """Parameters for ffmpeg_pulse_indev_avoptions."""
    server: bool | None = None
    name: bool | None = None
    stream_name: bool | None = None
    sample_rate: bool | None = None
    channels: bool | None = None
    frame_size: bool | None = None
    fragment_size: bool | None = None
    wallclock: bool | None = None
    sample_rate: bool | None = None
    channels: bool | None = None
    standard: bool | None = None
    channel: bool | None = None
    video_size: bool | None = None
    pixel_format: bool | None = None
    input_format: bool | None = None
    framerate: bool | None = None
    list_formats: bool | None = None
    list_standards: bool | None = None
    timestamps: bool | None = None
    ts: bool | None = None
    use_libv4l2: bool | None = None
    window_id: bool | None = None
    x: bool | None = None
    y: bool | None = None
    grab_x: bool | None = None
    grab_y: bool | None = None
    video_size: bool | None = None
    framerate: bool | None = None
    draw_mouse: bool | None = None
    follow_mouse: bool | None = None
    show_region: bool | None = None
    region_border: bool | None = None
    select_region: bool | None = None
    speed: bool | None = None
    paranoia_mode: bool | None = None
    video_size: bool | None = None
    pixel_format: bool | None = None
    framerate: bool | None = None

@dataclass
class FfmpegSwscalerAvoptionsParams:
    """Parameters for ffmpeg_swscaler_avoptions."""
    sws_flags: bool | None = None
    srcw: bool | None = None
    srch: bool | None = None
    dstw: bool | None = None
    dsth: bool | None = None
    src_format: bool | None = None
    dst_format: bool | None = None
    src_range: bool | None = None
    dst_range: bool | None = None
    param0: bool | None = None
    param1: bool | None = None
    src_v_chr_pos: bool | None = None
    src_h_chr_pos: bool | None = None
    dst_v_chr_pos: bool | None = None
    dst_h_chr_pos: bool | None = None
    sws_dither: bool | None = None
    gamma: bool | None = None
    alphablend: bool | None = None

@dataclass
class FfmpegSwresamplerAvoptionsParams:
    """Parameters for ffmpeg_swresampler_avoptions."""
    ich: bool | None = None
    in_channel_count: bool | None = None
    och: bool | None = None
    uch: bool | None = None
    isr: bool | None = None
    in_sample_rate: bool | None = None
    osr: bool | None = None
    out_sample_rate: bool | None = None
    isf: bool | None = None
    in_sample_fmt: bool | None = None
    osf: bool | None = None
    out_sample_fmt: bool | None = None
    tsf: bool | None = None
    icl: bool | None = None
    ocl: bool | None = None
    clev: bool | None = None
    center_mix_level: bool | None = None
    slev: bool | None = None
    lfe_mix_level: bool | None = None
    rmvol: bool | None = None
    rematrix_volume: bool | None = None
    rematrix_maxval: bool | None = None
    flags: bool | None = None
    swr_flags: bool | None = None
    dither_scale: bool | None = None
    dither_method: bool | None = None
    filter_size: bool | None = None
    phase_shift: bool | None = None
    linear_interp: bool | None = None
    exact_rational: bool | None = None
    cutoff: bool | None = None
    resample_cutoff: bool | None = None
    resampler: bool | None = None
    precision: bool | None = None
    cheby: bool | None = None
    min_comp: bool | None = None
    min_hard_comp: bool | None = None
    comp_duration: bool | None = None
    max_soft_comp: bool | None = None
    async_: bool | None = None
    first_pts: bool | None = None
    matrix_encoding: bool | None = None
    filter_type: bool | None = None
    kaiser_beta: bool | None = None

@dataclass
class FfmpegSwresamplerAvoptionsParams:
    """Parameters for ffmpeg_swresampler_avoptions."""
    ich: bool | None = None
    in_channel_count: bool | None = None
    och: bool | None = None
    uch: bool | None = None
    isr: bool | None = None
    in_sample_rate: bool | None = None
    osr: bool | None = None
    out_sample_rate: bool | None = None
    isf: bool | None = None
    in_sample_fmt: bool | None = None
    osf: bool | None = None
    out_sample_fmt: bool | None = None
    tsf: bool | None = None
    icl: bool | None = None
    ocl: bool | None = None
    clev: bool | None = None
    center_mix_level: bool | None = None
    slev: bool | None = None
    lfe_mix_level: bool | None = None
    rmvol: bool | None = None
    rematrix_volume: bool | None = None
    rematrix_maxval: bool | None = None
    flags: bool | None = None
    swr_flags: bool | None = None
    dither_scale: bool | None = None
    dither_method: bool | None = None
    filter_size: bool | None = None
    phase_shift: bool | None = None
    linear_interp: bool | None = None
    exact_rational: bool | None = None
    cutoff: bool | None = None
    resample_cutoff: bool | None = None
    resampler: bool | None = None
    precision: bool | None = None
    cheby: bool | None = None
    min_comp: bool | None = None
    min_hard_comp: bool | None = None
    comp_duration: bool | None = None
    max_soft_comp: bool | None = None
    async_: bool | None = None
    first_pts: bool | None = None
    matrix_encoding: bool | None = None
    filter_type: bool | None = None
    kaiser_beta: bool | None = None

@dataclass
class FfmpegSwscalerAvoptionsParams:
    """Parameters for ffmpeg_swscaler_avoptions."""
    sws_flags: bool | None = None
    srcw: bool | None = None
    srch: bool | None = None
    dstw: bool | None = None
    dsth: bool | None = None
    src_format: bool | None = None
    dst_format: bool | None = None
    src_range: bool | None = None
    dst_range: bool | None = None
    param0: bool | None = None
    param1: bool | None = None
    src_v_chr_pos: bool | None = None
    src_h_chr_pos: bool | None = None
    dst_v_chr_pos: bool | None = None
    dst_h_chr_pos: bool | None = None
    sws_dither: bool | None = None
    gamma: bool | None = None
    alphablend: bool | None = None

@dataclass
class FfmpegSwscalerAvoptionsParams:
    """Parameters for ffmpeg_swscaler_avoptions."""
    sws_flags: bool | None = None
    srcw: bool | None = None
    srch: bool | None = None
    dstw: bool | None = None
    dsth: bool | None = None
    src_format: bool | None = None
    dst_format: bool | None = None
    src_range: bool | None = None
    dst_range: bool | None = None
    param0: bool | None = None
    param1: bool | None = None
    src_v_chr_pos: bool | None = None
    src_h_chr_pos: bool | None = None
    dst_v_chr_pos: bool | None = None
    dst_h_chr_pos: bool | None = None
    sws_dither: bool | None = None
    gamma: bool | None = None
    alphablend: bool | None = None

@dataclass
class FfmpegAvdctAvoptionsParams:
    """Parameters for ffmpeg_avdct_avoptions."""
    dct: bool | None = None
    idct: bool | None = None
    td: bool | None = None
    color_primaries: bool | None = None
    color_range: bool | None = None
    tick_rate: bool | None = None
    delete_padding: bool | None = None
    freq: bool | None = None
    remove: bool | None = None
    pass_types: bool | None = None
    remove_types: bool | None = None
    aud: bool | None = None
    video_format: bool | None = None
    colour_primaries: bool | None = None
    tick_rate: bool | None = None
    crop_left: bool | None = None
    crop_right: bool | None = None
    crop_top: bool | None = None
    crop_bottom: bool | None = None
    sei_user_data: bool | None = None
    delete_filler: bool | None = None
    rotate: bool | None = None
    flip: bool | None = None
    level: bool | None = None
    texture: bool | None = None
    aud: bool | None = None
    video_format: bool | None = None
    colour_primaries: bool | None = None
    tick_rate: bool | None = None
    crop_left: bool | None = None
    crop_right: bool | None = None
    crop_top: bool | None = None
    crop_bottom: bool | None = None
    level: bool | None = None
    frame_rate: bool | None = None
    video_format: bool | None = None
    colour_primaries: bool | None = None
    amount: bool | None = None
    dropamount: bool | None = None
    gain: bool | None = None
    nb_out_samples: bool | None = None
    n: bool | None = None
    pad: bool | None = None
    p: bool | None = None
    frame_rate: bool | None = None
    r: bool | None = None
    color_primaries: bool | None = None
    color_trc: bool | None = None
    colorspace: bool | None = None
    freq: bool | None = None
    ts: bool | None = None
    pts: bool | None = None
    dts: bool | None = None
    color_space: bool | None = None
    color_range: bool | None = None

