"""cli_options tools for ffmpeg."""

import inspect
import json
import sys
import importlib
import importlib.util
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# Instance cache for reusing class instances across tool calls
_instance_cache: dict[str, object] = {}


def _get_or_create_instance(mod, class_name: str, **init_kwargs):
    """Get a cached class instance or create a new one."""
    cache_key = f"{mod.__name__}.{class_name}"
    if init_kwargs:
        # When explicit init args are provided, always create fresh
        cls = getattr(mod, class_name)
        return cls(**init_kwargs)
    if cache_key not in _instance_cache:
        cls = getattr(mod, class_name)
        try:
            _instance_cache[cache_key] = cls()
        except TypeError:
            # __init__ requires arguments we don't have — try with empty defaults
            import inspect as _ins
            sig = _ins.signature(cls.__init__)
            kwargs = {}
            for name, param in sig.parameters.items():
                if name == "self":
                    continue
                if param.default is not _ins.Parameter.empty:
                    kwargs[name] = param.default
                elif param.annotation is str or param.annotation == "str":
                    kwargs[name] = ""
                elif param.annotation is int or param.annotation == "int":
                    kwargs[name] = 0
                elif param.annotation is bool or param.annotation == "bool":
                    kwargs[name] = False
                elif param.annotation is list or param.annotation == "list":
                    kwargs[name] = []
                elif param.annotation is dict or param.annotation == "dict":
                    kwargs[name] = {}
                else:
                    kwargs[name] = None
            _instance_cache[cache_key] = cls(**kwargs)
    return _instance_cache[cache_key]


def _setup_import_path(codebase_path: str):
    """Add codebase to sys.path for imports."""
    codebase = Path(codebase_path)
    for path in [str(codebase), str(codebase.parent)]:
        if path not in sys.path:
            sys.path.insert(0, path)


def _load_source_module(codebase_path: str, module_path: str):
    """Load a module from the source codebase, avoiding package name collisions.

    Strategy:
    1. If codebase is inside a proper Python package (has __init__.py in parent),
       use the package's canonical import path.
    2. Otherwise, use importlib.util.spec_from_file_location to load directly
       from the source file, bypassing sys.modules name conflicts.
    """
    codebase = Path(codebase_path)

    # Check if codebase is itself a Python package (e.g., /path/to/wand/)
    if (codebase / "__init__.py").exists():
        # This is a package — import using package.module path
        package_name = codebase.name
        parent_dir = str(codebase.parent)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        full_module = f"{package_name}.{module_path}" if module_path != package_name else package_name
        try:
            return importlib.import_module(full_module)
        except ImportError:
            pass

    # For standalone files, load directly by file path to avoid name collisions
    parts = module_path.split(".")
    file_path = codebase / (parts[-1] + ".py") if len(parts) == 1 else codebase / "/".join(parts[:-1]) / (parts[-1] + ".py")
    if not file_path.exists():
        file_path = codebase / (module_path.replace(".", "/") + ".py")
    if not file_path.exists():
        # Final fallback: regular import
        return importlib.import_module(module_path)

    # Use a collision-safe name in sys.modules
    safe_name = f"_mcp_src_{codebase.name}_.{module_path}"
    if safe_name in sys.modules:
        return sys.modules[safe_name]

    spec = importlib.util.spec_from_file_location(safe_name, file_path,
        submodule_search_locations=[str(codebase)])
    if spec is None or spec.loader is None:
        return importlib.import_module(module_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[safe_name] = mod
    spec.loader.exec_module(mod)
    return mod


def register_tools(server: FastMCP, backend) -> None:
    """Register cli_options tools with the server."""

    @server.tool()
    async def ffmpeg_getting_help(
        h: bool | None = None,
    ) -> str:
        """Getting help options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if h is not None:
            if h:
                cmd_args.append("-h")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_print_help_information_capabilities(
        L: bool | None = None,
        h: str | None = None,
        help: str | None = None,
        version: bool | None = None,
        buildconf: bool | None = None,
        formats: bool | None = None,
        muxers: bool | None = None,
        demuxers: bool | None = None,
        devices: bool | None = None,
        codecs: bool | None = None,
        decoders: bool | None = None,
        encoders: bool | None = None,
        bsfs: bool | None = None,
        protocols: bool | None = None,
        filters: bool | None = None,
        pix_fmts: bool | None = None,
        layouts: bool | None = None,
        sample_fmts: bool | None = None,
        colors: bool | None = None,
        sources: str | None = None,
        sinks: str | None = None,
        hwaccels: bool | None = None,
    ) -> str:
        """Print help / information / capabilities options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if L is not None:
            if L:
                cmd_args.append("-L")
        if h is not None:
            cmd_args.extend(["-h", str(h)])
        if help is not None:
            cmd_args.extend(["-help", str(help)])
        if version is not None:
            if version:
                cmd_args.append("-version")
        if buildconf is not None:
            if buildconf:
                cmd_args.append("-buildconf")
        if formats is not None:
            if formats:
                cmd_args.append("-formats")
        if muxers is not None:
            if muxers:
                cmd_args.append("-muxers")
        if demuxers is not None:
            if demuxers:
                cmd_args.append("-demuxers")
        if devices is not None:
            if devices:
                cmd_args.append("-devices")
        if codecs is not None:
            if codecs:
                cmd_args.append("-codecs")
        if decoders is not None:
            if decoders:
                cmd_args.append("-decoders")
        if encoders is not None:
            if encoders:
                cmd_args.append("-encoders")
        if bsfs is not None:
            if bsfs:
                cmd_args.append("-bsfs")
        if protocols is not None:
            if protocols:
                cmd_args.append("-protocols")
        if filters is not None:
            if filters:
                cmd_args.append("-filters")
        if pix_fmts is not None:
            if pix_fmts:
                cmd_args.append("-pix_fmts")
        if layouts is not None:
            if layouts:
                cmd_args.append("-layouts")
        if sample_fmts is not None:
            if sample_fmts:
                cmd_args.append("-sample_fmts")
        if colors is not None:
            if colors:
                cmd_args.append("-colors")
        if sources is not None:
            cmd_args.extend(["-sources", str(sources)])
        if sinks is not None:
            cmd_args.extend(["-sinks", str(sinks)])
        if hwaccels is not None:
            if hwaccels:
                cmd_args.append("-hwaccels")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_global_options_affect_whole_program_instead_of_just_one_file(
        loglevel: str | None = None,
        v: str | None = None,
        report: bool | None = None,
        max_alloc: int | None = None,
        y: bool | None = None,
        n: bool | None = None,
        ignore_unknown: bool | None = None,
        filter_threads: bool | None = None,
        filter_complex_threads: bool | None = None,
        stats: bool | None = None,
        bits_per_raw_sample: int | None = None,
        vol: int | None = None,
    ) -> str:
        """Global options (affect whole program instead of just one file) options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if loglevel is not None:
            cmd_args.extend(["-loglevel", str(loglevel)])
        if v is not None:
            cmd_args.extend(["-v", str(v)])
        if report is not None:
            if report:
                cmd_args.append("-report")
        if max_alloc is not None:
            cmd_args.extend(["-max_alloc", str(max_alloc)])
        if y is not None:
            if y:
                cmd_args.append("-y")
        if n is not None:
            if n:
                cmd_args.append("-n")
        if ignore_unknown is not None:
            if ignore_unknown:
                cmd_args.append("-ignore_unknown")
        if filter_threads is not None:
            if filter_threads:
                cmd_args.append("-filter_threads")
        if filter_complex_threads is not None:
            if filter_complex_threads:
                cmd_args.append("-filter_complex_threads")
        if stats is not None:
            if stats:
                cmd_args.append("-stats")
        if bits_per_raw_sample is not None:
            cmd_args.extend(["-bits_per_raw_sample", str(bits_per_raw_sample)])
        if vol is not None:
            cmd_args.extend(["-vol", str(vol)])
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_advanced_global_options(
        cpuflags: str | None = None,
        hide_banner: str | None = None,
        copy_unknown: bool | None = None,
        benchmark: bool | None = None,
        benchmark_all: bool | None = None,
        progress: str | None = None,
        stdin: bool | None = None,
        timelimit: int | None = None,
        dump: bool | None = None,
        hex: bool | None = None,
        vsync: bool | None = None,
        frame_drop_threshold: bool | None = None,
        async_: bool | None = None,
        adrift_threshold: str | None = None,
        copyts: bool | None = None,
        start_at_zero: bool | None = None,
        copytb: str | None = None,
        dts_delta_threshold: str | None = None,
        dts_error_threshold: str | None = None,
        xerror: str | None = None,
        abort_on: str | None = None,
        filter_complex: str | None = None,
        lavfi: str | None = None,
        filter_complex_script: str | None = None,
        auto_conversion_filters: bool | None = None,
        stats_period: str | None = None,
        debug_ts: bool | None = None,
        intra: bool | None = None,
        sameq: bool | None = None,
        same_quant: bool | None = None,
        deinterlace: bool | None = None,
        psnr: bool | None = None,
        vstats: bool | None = None,
        vstats_file: str | None = None,
        vstats_version: bool | None = None,
        qphist: bool | None = None,
        vc: str | None = None,
        tvstd: str | None = None,
        isync: bool | None = None,
        sdp_file: str | None = None,
        vaapi_device: str | None = None,
        qsv_device: str | None = None,
        init_hw_device: str | None = None,
        filter_hw_device: str | None = None,
    ) -> str:
        """Advanced global options options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if cpuflags is not None:
            cmd_args.extend(["-cpuflags", str(cpuflags)])
        if hide_banner is not None:
            cmd_args.extend(["-hide_banner", str(hide_banner)])
        if copy_unknown is not None:
            if copy_unknown:
                cmd_args.append("-copy_unknown")
        if benchmark is not None:
            if benchmark:
                cmd_args.append("-benchmark")
        if benchmark_all is not None:
            if benchmark_all:
                cmd_args.append("-benchmark_all")
        if progress is not None:
            cmd_args.extend(["-progress", str(progress)])
        if stdin is not None:
            if stdin:
                cmd_args.append("-stdin")
        if timelimit is not None:
            cmd_args.extend(["-timelimit", str(timelimit)])
        if dump is not None:
            if dump:
                cmd_args.append("-dump")
        if hex is not None:
            if hex:
                cmd_args.append("-hex")
        if vsync is not None:
            if vsync:
                cmd_args.append("-vsync")
        if frame_drop_threshold is not None:
            if frame_drop_threshold:
                cmd_args.append("-frame_drop_threshold")
        if async_ is not None:
            if async_:
                cmd_args.append("-async")
        if adrift_threshold is not None:
            cmd_args.extend(["-adrift_threshold", str(adrift_threshold)])
        if copyts is not None:
            if copyts:
                cmd_args.append("-copyts")
        if start_at_zero is not None:
            if start_at_zero:
                cmd_args.append("-start_at_zero")
        if copytb is not None:
            cmd_args.extend(["-copytb", str(copytb)])
        if dts_delta_threshold is not None:
            cmd_args.extend(["-dts_delta_threshold", str(dts_delta_threshold)])
        if dts_error_threshold is not None:
            cmd_args.extend(["-dts_error_threshold", str(dts_error_threshold)])
        if xerror is not None:
            cmd_args.extend(["-xerror", str(xerror)])
        if abort_on is not None:
            cmd_args.extend(["-abort_on", str(abort_on)])
        if filter_complex is not None:
            cmd_args.extend(["-filter_complex", str(filter_complex)])
        if lavfi is not None:
            cmd_args.extend(["-lavfi", str(lavfi)])
        if filter_complex_script is not None:
            cmd_args.extend(["-filter_complex_script", str(filter_complex_script)])
        if auto_conversion_filters is not None:
            if auto_conversion_filters:
                cmd_args.append("-auto_conversion_filters")
        if stats_period is not None:
            cmd_args.extend(["-stats_period", str(stats_period)])
        if debug_ts is not None:
            if debug_ts:
                cmd_args.append("-debug_ts")
        if intra is not None:
            if intra:
                cmd_args.append("-intra")
        if sameq is not None:
            if sameq:
                cmd_args.append("-sameq")
        if same_quant is not None:
            if same_quant:
                cmd_args.append("-same_quant")
        if deinterlace is not None:
            if deinterlace:
                cmd_args.append("-deinterlace")
        if psnr is not None:
            if psnr:
                cmd_args.append("-psnr")
        if vstats is not None:
            if vstats:
                cmd_args.append("-vstats")
        if vstats_file is not None:
            cmd_args.extend(["-vstats_file", str(vstats_file)])
        if vstats_version is not None:
            if vstats_version:
                cmd_args.append("-vstats_version")
        if qphist is not None:
            if qphist:
                cmd_args.append("-qphist")
        if vc is not None:
            cmd_args.extend(["-vc", str(vc)])
        if tvstd is not None:
            cmd_args.extend(["-tvstd", str(tvstd)])
        if isync is not None:
            if isync:
                cmd_args.append("-isync")
        if sdp_file is not None:
            cmd_args.extend(["-sdp_file", str(sdp_file)])
        if vaapi_device is not None:
            cmd_args.extend(["-vaapi_device", str(vaapi_device)])
        if qsv_device is not None:
            cmd_args.extend(["-qsv_device", str(qsv_device)])
        if init_hw_device is not None:
            cmd_args.extend(["-init_hw_device", str(init_hw_device)])
        if filter_hw_device is not None:
            cmd_args.extend(["-filter_hw_device", str(filter_hw_device)])
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_per_file_main_options(
        f: str | None = None,
        c: str | None = None,
        codec: str | None = None,
        pre: str | None = None,
        t: str | None = None,
        to: str | None = None,
        fs: str | None = None,
        ss: str | None = None,
        sseof: str | None = None,
        seek_timestamp: bool | None = None,
        timestamp: str | None = None,
        target: str | None = None,
        apad: bool | None = None,
        frames: int | None = None,
        filter: str | None = None,
        filter_script: str | None = None,
        reinit_filter: bool | None = None,
        discard: bool | None = None,
        disposition: bool | None = None,
    ) -> str:
        """Per-file main options options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if f is not None:
            cmd_args.extend(["-f", str(f)])
        if c is not None:
            cmd_args.extend(["-c", str(c)])
        if codec is not None:
            cmd_args.extend(["-codec", str(codec)])
        if pre is not None:
            cmd_args.extend(["-pre", str(pre)])
        if t is not None:
            cmd_args.extend(["-t", str(t)])
        if to is not None:
            cmd_args.extend(["-to", str(to)])
        if fs is not None:
            cmd_args.extend(["-fs", str(fs)])
        if ss is not None:
            cmd_args.extend(["-ss", str(ss)])
        if sseof is not None:
            cmd_args.extend(["-sseof", str(sseof)])
        if seek_timestamp is not None:
            if seek_timestamp:
                cmd_args.append("-seek_timestamp")
        if timestamp is not None:
            cmd_args.extend(["-timestamp", str(timestamp)])
        if target is not None:
            cmd_args.extend(["-target", str(target)])
        if apad is not None:
            if apad:
                cmd_args.append("-apad")
        if frames is not None:
            cmd_args.extend(["-frames", str(frames)])
        if filter is not None:
            cmd_args.extend(["-filter", str(filter)])
        if filter_script is not None:
            cmd_args.extend(["-filter_script", str(filter_script)])
        if reinit_filter is not None:
            if reinit_filter:
                cmd_args.append("-reinit_filter")
        if discard is not None:
            if discard:
                cmd_args.append("-discard")
        if disposition is not None:
            if disposition:
                cmd_args.append("-disposition")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_advanced_per_file_options(
        map_chapters: str | None = None,
        accurate_seek: bool | None = None,
        itsoffset: str | None = None,
        itsscale: str | None = None,
        dframes: int | None = None,
        re: bool | None = None,
        shortest: bool | None = None,
        bitexact: bool | None = None,
        copyinkf: bool | None = None,
        copypriorss: bool | None = None,
        tag: str | None = None,
        q: str | None = None,
        qscale: str | None = None,
        profile: str | None = None,
        attach: str | None = None,
        dump_attachment: str | None = None,
        thread_queue_size: bool | None = None,
        find_stream_info: bool | None = None,
        autorotate: bool | None = None,
        autoscale: bool | None = None,
        muxdelay: str | None = None,
        muxpreload: str | None = None,
        time_base: str | None = None,
        enc_time_base: str | None = None,
        bsf: str | None = None,
        fpre: str | None = None,
        max_muxing_queue_size: str | None = None,
        muxing_queue_data_threshold: int | None = None,
        dcodec: str | None = None,
    ) -> str:
        """Advanced per-file options options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if map_chapters is not None:
            cmd_args.extend(["-map_chapters", str(map_chapters)])
        if accurate_seek is not None:
            if accurate_seek:
                cmd_args.append("-accurate_seek")
        if itsoffset is not None:
            cmd_args.extend(["-itsoffset", str(itsoffset)])
        if itsscale is not None:
            cmd_args.extend(["-itsscale", str(itsscale)])
        if dframes is not None:
            cmd_args.extend(["-dframes", str(dframes)])
        if re is not None:
            if re:
                cmd_args.append("-re")
        if shortest is not None:
            if shortest:
                cmd_args.append("-shortest")
        if bitexact is not None:
            if bitexact:
                cmd_args.append("-bitexact")
        if copyinkf is not None:
            if copyinkf:
                cmd_args.append("-copyinkf")
        if copypriorss is not None:
            if copypriorss:
                cmd_args.append("-copypriorss")
        if tag is not None:
            cmd_args.extend(["-tag", str(tag)])
        if q is not None:
            cmd_args.extend(["-q", str(q)])
        if qscale is not None:
            cmd_args.extend(["-qscale", str(qscale)])
        if profile is not None:
            cmd_args.extend(["-profile", str(profile)])
        if attach is not None:
            cmd_args.extend(["-attach", str(attach)])
        if dump_attachment is not None:
            cmd_args.extend(["-dump_attachment", str(dump_attachment)])
        if thread_queue_size is not None:
            if thread_queue_size:
                cmd_args.append("-thread_queue_size")
        if find_stream_info is not None:
            if find_stream_info:
                cmd_args.append("-find_stream_info")
        if autorotate is not None:
            if autorotate:
                cmd_args.append("-autorotate")
        if autoscale is not None:
            if autoscale:
                cmd_args.append("-autoscale")
        if muxdelay is not None:
            cmd_args.extend(["-muxdelay", str(muxdelay)])
        if muxpreload is not None:
            cmd_args.extend(["-muxpreload", str(muxpreload)])
        if time_base is not None:
            cmd_args.extend(["-time_base", str(time_base)])
        if enc_time_base is not None:
            cmd_args.extend(["-enc_time_base", str(enc_time_base)])
        if bsf is not None:
            cmd_args.extend(["-bsf", str(bsf)])
        if fpre is not None:
            cmd_args.extend(["-fpre", str(fpre)])
        if max_muxing_queue_size is not None:
            cmd_args.extend(["-max_muxing_queue_size", str(max_muxing_queue_size)])
        if muxing_queue_data_threshold is not None:
            cmd_args.extend(["-muxing_queue_data_threshold", str(muxing_queue_data_threshold)])
        if dcodec is not None:
            cmd_args.extend(["-dcodec", str(dcodec)])
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_video_options(
        vframes: int | None = None,
        r: str | None = None,
        fpsmax: str | None = None,
        s: str | None = None,
        aspect: str | None = None,
        bits_per_raw_sample: int | None = None,
        vn: bool | None = None,
        vcodec: str | None = None,
        pass_: str | None = None,
        vf: str | None = None,
        ab: str | None = None,
        b: str | None = None,
        dn: bool | None = None,
    ) -> str:
        """Video options options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if vframes is not None:
            cmd_args.extend(["-vframes", str(vframes)])
        if r is not None:
            cmd_args.extend(["-r", str(r)])
        if fpsmax is not None:
            cmd_args.extend(["-fpsmax", str(fpsmax)])
        if s is not None:
            cmd_args.extend(["-s", str(s)])
        if aspect is not None:
            cmd_args.extend(["-aspect", str(aspect)])
        if bits_per_raw_sample is not None:
            cmd_args.extend(["-bits_per_raw_sample", str(bits_per_raw_sample)])
        if vn is not None:
            if vn:
                cmd_args.append("-vn")
        if vcodec is not None:
            cmd_args.extend(["-vcodec", str(vcodec)])
        if pass_ is not None:
            cmd_args.extend(["-pass", str(pass_)])
        if vf is not None:
            cmd_args.extend(["-vf", str(vf)])
        if ab is not None:
            cmd_args.extend(["-ab", str(ab)])
        if b is not None:
            cmd_args.extend(["-b", str(b)])
        if dn is not None:
            if dn:
                cmd_args.append("-dn")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_advanced_video_options(
        pix_fmt: str | None = None,
        intra: bool | None = None,
        rc_override: str | None = None,
        sameq: bool | None = None,
        same_quant: bool | None = None,
        passlogfile: str | None = None,
        deinterlace: bool | None = None,
        psnr: bool | None = None,
        vstats: bool | None = None,
        vstats_file: str | None = None,
        vstats_version: bool | None = None,
        intra_matrix: str | None = None,
        inter_matrix: str | None = None,
        chroma_intra_matrix: str | None = None,
        top: bool | None = None,
        vtag: str | None = None,
        qphist: bool | None = None,
        force_fps: bool | None = None,
        force_key_frames: str | None = None,
        hwaccel_device: str | None = None,
        hwaccel_output_format: str | None = None,
        vc: str | None = None,
        tvstd: str | None = None,
        vpre: str | None = None,
    ) -> str:
        """Advanced Video options options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if pix_fmt is not None:
            cmd_args.extend(["-pix_fmt", str(pix_fmt)])
        if intra is not None:
            if intra:
                cmd_args.append("-intra")
        if rc_override is not None:
            cmd_args.extend(["-rc_override", str(rc_override)])
        if sameq is not None:
            if sameq:
                cmd_args.append("-sameq")
        if same_quant is not None:
            if same_quant:
                cmd_args.append("-same_quant")
        if passlogfile is not None:
            cmd_args.extend(["-passlogfile", str(passlogfile)])
        if deinterlace is not None:
            if deinterlace:
                cmd_args.append("-deinterlace")
        if psnr is not None:
            if psnr:
                cmd_args.append("-psnr")
        if vstats is not None:
            if vstats:
                cmd_args.append("-vstats")
        if vstats_file is not None:
            cmd_args.extend(["-vstats_file", str(vstats_file)])
        if vstats_version is not None:
            if vstats_version:
                cmd_args.append("-vstats_version")
        if intra_matrix is not None:
            cmd_args.extend(["-intra_matrix", str(intra_matrix)])
        if inter_matrix is not None:
            cmd_args.extend(["-inter_matrix", str(inter_matrix)])
        if chroma_intra_matrix is not None:
            cmd_args.extend(["-chroma_intra_matrix", str(chroma_intra_matrix)])
        if top is not None:
            if top:
                cmd_args.append("-top")
        if vtag is not None:
            cmd_args.extend(["-vtag", str(vtag)])
        if qphist is not None:
            if qphist:
                cmd_args.append("-qphist")
        if force_fps is not None:
            if force_fps:
                cmd_args.append("-force_fps")
        if force_key_frames is not None:
            cmd_args.extend(["-force_key_frames", str(force_key_frames)])
        if hwaccel_device is not None:
            cmd_args.extend(["-hwaccel_device", str(hwaccel_device)])
        if hwaccel_output_format is not None:
            cmd_args.extend(["-hwaccel_output_format", str(hwaccel_output_format)])
        if vc is not None:
            cmd_args.extend(["-vc", str(vc)])
        if tvstd is not None:
            cmd_args.extend(["-tvstd", str(tvstd)])
        if vpre is not None:
            cmd_args.extend(["-vpre", str(vpre)])
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_audio_options(
        aframes: int | None = None,
        aq: str | None = None,
        ar: str | None = None,
        ac: str | None = None,
        an: bool | None = None,
        acodec: str | None = None,
        vol: int | None = None,
        af: str | None = None,
    ) -> str:
        """Audio options options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if aframes is not None:
            cmd_args.extend(["-aframes", str(aframes)])
        if aq is not None:
            cmd_args.extend(["-aq", str(aq)])
        if ar is not None:
            cmd_args.extend(["-ar", str(ar)])
        if ac is not None:
            cmd_args.extend(["-ac", str(ac)])
        if an is not None:
            if an:
                cmd_args.append("-an")
        if acodec is not None:
            cmd_args.extend(["-acodec", str(acodec)])
        if vol is not None:
            cmd_args.extend(["-vol", str(vol)])
        if af is not None:
            cmd_args.extend(["-af", str(af)])
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_advanced_audio_options(
        atag: str | None = None,
        sample_fmt: str | None = None,
        channel_layout: str | None = None,
        guess_layout_max: bool | None = None,
        apre: str | None = None,
    ) -> str:
        """Advanced Audio options options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if atag is not None:
            cmd_args.extend(["-atag", str(atag)])
        if sample_fmt is not None:
            cmd_args.extend(["-sample_fmt", str(sample_fmt)])
        if channel_layout is not None:
            cmd_args.extend(["-channel_layout", str(channel_layout)])
        if guess_layout_max is not None:
            if guess_layout_max:
                cmd_args.append("-guess_layout_max")
        if apre is not None:
            cmd_args.extend(["-apre", str(apre)])
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_subtitle_options(
        s: str | None = None,
        sn: bool | None = None,
        scodec: str | None = None,
        stag: str | None = None,
        fix_sub_duration: bool | None = None,
        canvas_size: str | None = None,
        spre: str | None = None,
    ) -> str:
        """Subtitle options options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if s is not None:
            cmd_args.extend(["-s", str(s)])
        if sn is not None:
            if sn:
                cmd_args.append("-sn")
        if scodec is not None:
            cmd_args.extend(["-scodec", str(scodec)])
        if stag is not None:
            cmd_args.extend(["-stag", str(stag)])
        if fix_sub_duration is not None:
            if fix_sub_duration:
                cmd_args.append("-fix_sub_duration")
        if canvas_size is not None:
            cmd_args.extend(["-canvas_size", str(canvas_size)])
        if spre is not None:
            cmd_args.extend(["-spre", str(spre)])
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_avcodeccontext_avoptions(
        b: bool | None = None,
        ab: bool | None = None,
        bt: bool | None = None,
        flags: bool | None = None,
        flags2: bool | None = None,
        export_side_data: bool | None = None,
        g: bool | None = None,
        ar: bool | None = None,
        ac: bool | None = None,
        cutoff: bool | None = None,
        frame_size: bool | None = None,
        qcomp: bool | None = None,
        qblur: bool | None = None,
        qmin: bool | None = None,
        qmax: bool | None = None,
        qdiff: bool | None = None,
        bf: bool | None = None,
        b_qfactor: bool | None = None,
        b_strategy: bool | None = None,
        ps: bool | None = None,
        bug: bool | None = None,
        strict: bool | None = None,
        b_qoffset: bool | None = None,
        err_detect: bool | None = None,
        mpeg_quant: bool | None = None,
        maxrate: bool | None = None,
        minrate: bool | None = None,
        bufsize: bool | None = None,
        i_qfactor: bool | None = None,
        i_qoffset: bool | None = None,
        dct: bool | None = None,
        lumi_mask: bool | None = None,
        tcplx_mask: bool | None = None,
        scplx_mask: bool | None = None,
        p_mask: bool | None = None,
        dark_mask: bool | None = None,
        idct: bool | None = None,
        ec: bool | None = None,
        pred: bool | None = None,
        aspect: bool | None = None,
        sar: bool | None = None,
        debug: bool | None = None,
        dia_size: bool | None = None,
        last_pred: bool | None = None,
        preme: bool | None = None,
        pre_dia_size: bool | None = None,
        subq: bool | None = None,
        me_range: bool | None = None,
        global_quality: bool | None = None,
        coder: bool | None = None,
        context: bool | None = None,
        mbd: bool | None = None,
        sc_threshold: bool | None = None,
        nr: bool | None = None,
        threads: bool | None = None,
        dc: bool | None = None,
        nssew: bool | None = None,
        skip_top: bool | None = None,
        skip_bottom: bool | None = None,
        profile: bool | None = None,
        level: bool | None = None,
        lowres: bool | None = None,
        skip_threshold: bool | None = None,
        skip_factor: bool | None = None,
        skip_exp: bool | None = None,
        skipcmp: bool | None = None,
        cmp: bool | None = None,
        subcmp: bool | None = None,
        mbcmp: bool | None = None,
        ildctcmp: bool | None = None,
        precmp: bool | None = None,
        mblmin: bool | None = None,
        mblmax: bool | None = None,
        mepc: bool | None = None,
        skip_loop_filter: bool | None = None,
        skip_idct: bool | None = None,
        skip_frame: bool | None = None,
        bidir_refine: bool | None = None,
        brd_scale: bool | None = None,
        keyint_min: bool | None = None,
        refs: bool | None = None,
        chromaoffset: bool | None = None,
        trellis: bool | None = None,
        mv0_threshold: bool | None = None,
        b_sensitivity: bool | None = None,
        channel_layout: bool | None = None,
        rc_max_vbv_use: bool | None = None,
        rc_min_vbv_use: bool | None = None,
        ticks_per_frame: bool | None = None,
        color_primaries: bool | None = None,
        color_trc: bool | None = None,
        colorspace: bool | None = None,
        color_range: bool | None = None,
        slices: bool | None = None,
        thread_type: bool | None = None,
        sub_charenc: bool | None = None,
        sub_charenc_mode: bool | None = None,
        sub_text_format: bool | None = None,
        apply_cropping: bool | None = None,
        skip_alpha: bool | None = None,
        field_order: bool | None = None,
        dump_separator: bool | None = None,
        codec_whitelist: bool | None = None,
        max_pixels: bool | None = None,
        max_samples: bool | None = None,
        hwaccel_flags: bool | None = None,
        extra_hw_frames: bool | None = None,
        mpv_flags: bool | None = None,
        error_rate: bool | None = None,
        qsquish: bool | None = None,
        rc_qmod_amp: bool | None = None,
        rc_qmod_freq: bool | None = None,
        rc_eq: bool | None = None,
        rc_init_cplx: bool | None = None,
        border_mask: bool | None = None,
        lmin: bool | None = None,
        lmax: bool | None = None,
        ibias: bool | None = None,
        pbias: bool | None = None,
        motion_est: bool | None = None,
        skip_cmp: bool | None = None,
        noise_reduction: bool | None = None,
        mepre: bool | None = None,
        intra_penalty: bool | None = None,
        a53cc: bool | None = None,
        rc_strategy: bool | None = None,
        huffman: bool | None = None,
    ) -> str:
        """AVCodecContext AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if b is not None:
            if b:
                cmd_args.append("-b")
        if ab is not None:
            if ab:
                cmd_args.append("-ab")
        if bt is not None:
            if bt:
                cmd_args.append("-bt")
        if flags is not None:
            if flags:
                cmd_args.append("-flags")
        if flags2 is not None:
            if flags2:
                cmd_args.append("-flags2")
        if export_side_data is not None:
            if export_side_data:
                cmd_args.append("-export_side_data")
        if g is not None:
            if g:
                cmd_args.append("-g")
        if ar is not None:
            if ar:
                cmd_args.append("-ar")
        if ac is not None:
            if ac:
                cmd_args.append("-ac")
        if cutoff is not None:
            if cutoff:
                cmd_args.append("-cutoff")
        if frame_size is not None:
            if frame_size:
                cmd_args.append("-frame_size")
        if qcomp is not None:
            if qcomp:
                cmd_args.append("-qcomp")
        if qblur is not None:
            if qblur:
                cmd_args.append("-qblur")
        if qmin is not None:
            if qmin:
                cmd_args.append("-qmin")
        if qmax is not None:
            if qmax:
                cmd_args.append("-qmax")
        if qdiff is not None:
            if qdiff:
                cmd_args.append("-qdiff")
        if bf is not None:
            if bf:
                cmd_args.append("-bf")
        if b_qfactor is not None:
            if b_qfactor:
                cmd_args.append("-b_qfactor")
        if b_strategy is not None:
            if b_strategy:
                cmd_args.append("-b_strategy")
        if ps is not None:
            if ps:
                cmd_args.append("-ps")
        if bug is not None:
            if bug:
                cmd_args.append("-bug")
        if strict is not None:
            if strict:
                cmd_args.append("-strict")
        if b_qoffset is not None:
            if b_qoffset:
                cmd_args.append("-b_qoffset")
        if err_detect is not None:
            if err_detect:
                cmd_args.append("-err_detect")
        if mpeg_quant is not None:
            if mpeg_quant:
                cmd_args.append("-mpeg_quant")
        if maxrate is not None:
            if maxrate:
                cmd_args.append("-maxrate")
        if minrate is not None:
            if minrate:
                cmd_args.append("-minrate")
        if bufsize is not None:
            if bufsize:
                cmd_args.append("-bufsize")
        if i_qfactor is not None:
            if i_qfactor:
                cmd_args.append("-i_qfactor")
        if i_qoffset is not None:
            if i_qoffset:
                cmd_args.append("-i_qoffset")
        if dct is not None:
            if dct:
                cmd_args.append("-dct")
        if lumi_mask is not None:
            if lumi_mask:
                cmd_args.append("-lumi_mask")
        if tcplx_mask is not None:
            if tcplx_mask:
                cmd_args.append("-tcplx_mask")
        if scplx_mask is not None:
            if scplx_mask:
                cmd_args.append("-scplx_mask")
        if p_mask is not None:
            if p_mask:
                cmd_args.append("-p_mask")
        if dark_mask is not None:
            if dark_mask:
                cmd_args.append("-dark_mask")
        if idct is not None:
            if idct:
                cmd_args.append("-idct")
        if ec is not None:
            if ec:
                cmd_args.append("-ec")
        if pred is not None:
            if pred:
                cmd_args.append("-pred")
        if aspect is not None:
            if aspect:
                cmd_args.append("-aspect")
        if sar is not None:
            if sar:
                cmd_args.append("-sar")
        if debug is not None:
            if debug:
                cmd_args.append("-debug")
        if dia_size is not None:
            if dia_size:
                cmd_args.append("-dia_size")
        if last_pred is not None:
            if last_pred:
                cmd_args.append("-last_pred")
        if preme is not None:
            if preme:
                cmd_args.append("-preme")
        if pre_dia_size is not None:
            if pre_dia_size:
                cmd_args.append("-pre_dia_size")
        if subq is not None:
            if subq:
                cmd_args.append("-subq")
        if me_range is not None:
            if me_range:
                cmd_args.append("-me_range")
        if global_quality is not None:
            if global_quality:
                cmd_args.append("-global_quality")
        if coder is not None:
            if coder:
                cmd_args.append("-coder")
        if context is not None:
            if context:
                cmd_args.append("-context")
        if mbd is not None:
            if mbd:
                cmd_args.append("-mbd")
        if sc_threshold is not None:
            if sc_threshold:
                cmd_args.append("-sc_threshold")
        if nr is not None:
            if nr:
                cmd_args.append("-nr")
        if threads is not None:
            if threads:
                cmd_args.append("-threads")
        if dc is not None:
            if dc:
                cmd_args.append("-dc")
        if nssew is not None:
            if nssew:
                cmd_args.append("-nssew")
        if skip_top is not None:
            if skip_top:
                cmd_args.append("-skip_top")
        if skip_bottom is not None:
            if skip_bottom:
                cmd_args.append("-skip_bottom")
        if profile is not None:
            if profile:
                cmd_args.append("-profile")
        if level is not None:
            if level:
                cmd_args.append("-level")
        if lowres is not None:
            if lowres:
                cmd_args.append("-lowres")
        if skip_threshold is not None:
            if skip_threshold:
                cmd_args.append("-skip_threshold")
        if skip_factor is not None:
            if skip_factor:
                cmd_args.append("-skip_factor")
        if skip_exp is not None:
            if skip_exp:
                cmd_args.append("-skip_exp")
        if skipcmp is not None:
            if skipcmp:
                cmd_args.append("-skipcmp")
        if cmp is not None:
            if cmp:
                cmd_args.append("-cmp")
        if subcmp is not None:
            if subcmp:
                cmd_args.append("-subcmp")
        if mbcmp is not None:
            if mbcmp:
                cmd_args.append("-mbcmp")
        if ildctcmp is not None:
            if ildctcmp:
                cmd_args.append("-ildctcmp")
        if precmp is not None:
            if precmp:
                cmd_args.append("-precmp")
        if mblmin is not None:
            if mblmin:
                cmd_args.append("-mblmin")
        if mblmax is not None:
            if mblmax:
                cmd_args.append("-mblmax")
        if mepc is not None:
            if mepc:
                cmd_args.append("-mepc")
        if skip_loop_filter is not None:
            if skip_loop_filter:
                cmd_args.append("-skip_loop_filter")
        if skip_idct is not None:
            if skip_idct:
                cmd_args.append("-skip_idct")
        if skip_frame is not None:
            if skip_frame:
                cmd_args.append("-skip_frame")
        if bidir_refine is not None:
            if bidir_refine:
                cmd_args.append("-bidir_refine")
        if brd_scale is not None:
            if brd_scale:
                cmd_args.append("-brd_scale")
        if keyint_min is not None:
            if keyint_min:
                cmd_args.append("-keyint_min")
        if refs is not None:
            if refs:
                cmd_args.append("-refs")
        if chromaoffset is not None:
            if chromaoffset:
                cmd_args.append("-chromaoffset")
        if trellis is not None:
            if trellis:
                cmd_args.append("-trellis")
        if mv0_threshold is not None:
            if mv0_threshold:
                cmd_args.append("-mv0_threshold")
        if b_sensitivity is not None:
            if b_sensitivity:
                cmd_args.append("-b_sensitivity")
        if channel_layout is not None:
            if channel_layout:
                cmd_args.append("-channel_layout")
        if rc_max_vbv_use is not None:
            if rc_max_vbv_use:
                cmd_args.append("-rc_max_vbv_use")
        if rc_min_vbv_use is not None:
            if rc_min_vbv_use:
                cmd_args.append("-rc_min_vbv_use")
        if ticks_per_frame is not None:
            if ticks_per_frame:
                cmd_args.append("-ticks_per_frame")
        if color_primaries is not None:
            if color_primaries:
                cmd_args.append("-color_primaries")
        if color_trc is not None:
            if color_trc:
                cmd_args.append("-color_trc")
        if colorspace is not None:
            if colorspace:
                cmd_args.append("-colorspace")
        if color_range is not None:
            if color_range:
                cmd_args.append("-color_range")
        if slices is not None:
            if slices:
                cmd_args.append("-slices")
        if thread_type is not None:
            if thread_type:
                cmd_args.append("-thread_type")
        if sub_charenc is not None:
            if sub_charenc:
                cmd_args.append("-sub_charenc")
        if sub_charenc_mode is not None:
            if sub_charenc_mode:
                cmd_args.append("-sub_charenc_mode")
        if sub_text_format is not None:
            if sub_text_format:
                cmd_args.append("-sub_text_format")
        if apply_cropping is not None:
            if apply_cropping:
                cmd_args.append("-apply_cropping")
        if skip_alpha is not None:
            if skip_alpha:
                cmd_args.append("-skip_alpha")
        if field_order is not None:
            if field_order:
                cmd_args.append("-field_order")
        if dump_separator is not None:
            if dump_separator:
                cmd_args.append("-dump_separator")
        if codec_whitelist is not None:
            if codec_whitelist:
                cmd_args.append("-codec_whitelist")
        if max_pixels is not None:
            if max_pixels:
                cmd_args.append("-max_pixels")
        if max_samples is not None:
            if max_samples:
                cmd_args.append("-max_samples")
        if hwaccel_flags is not None:
            if hwaccel_flags:
                cmd_args.append("-hwaccel_flags")
        if extra_hw_frames is not None:
            if extra_hw_frames:
                cmd_args.append("-extra_hw_frames")
        if mpv_flags is not None:
            if mpv_flags:
                cmd_args.append("-mpv_flags")
        if error_rate is not None:
            if error_rate:
                cmd_args.append("-error_rate")
        if qsquish is not None:
            if qsquish:
                cmd_args.append("-qsquish")
        if rc_qmod_amp is not None:
            if rc_qmod_amp:
                cmd_args.append("-rc_qmod_amp")
        if rc_qmod_freq is not None:
            if rc_qmod_freq:
                cmd_args.append("-rc_qmod_freq")
        if rc_eq is not None:
            if rc_eq:
                cmd_args.append("-rc_eq")
        if rc_init_cplx is not None:
            if rc_init_cplx:
                cmd_args.append("-rc_init_cplx")
        if border_mask is not None:
            if border_mask:
                cmd_args.append("-border_mask")
        if lmin is not None:
            if lmin:
                cmd_args.append("-lmin")
        if lmax is not None:
            if lmax:
                cmd_args.append("-lmax")
        if ibias is not None:
            if ibias:
                cmd_args.append("-ibias")
        if pbias is not None:
            if pbias:
                cmd_args.append("-pbias")
        if motion_est is not None:
            if motion_est:
                cmd_args.append("-motion_est")
        if skip_cmp is not None:
            if skip_cmp:
                cmd_args.append("-skip_cmp")
        if noise_reduction is not None:
            if noise_reduction:
                cmd_args.append("-noise_reduction")
        if mepre is not None:
            if mepre:
                cmd_args.append("-mepre")
        if intra_penalty is not None:
            if intra_penalty:
                cmd_args.append("-intra_penalty")
        if a53cc is not None:
            if a53cc:
                cmd_args.append("-a53cc")
        if rc_strategy is not None:
            if rc_strategy:
                cmd_args.append("-rc_strategy")
        if huffman is not None:
            if huffman:
                cmd_args.append("-huffman")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_apng_encoder_avoptions(
        dpi: bool | None = None,
        dpm: bool | None = None,
        pred: bool | None = None,
        quality: bool | None = None,
        skip_empty_cb: bool | None = None,
        max_strips: bool | None = None,
        min_strips: bool | None = None,
        dither_type: bool | None = None,
        nitris_compat: bool | None = None,
        ibias: bool | None = None,
        profile: bool | None = None,
        quant_deadzone: bool | None = None,
        compression: bool | None = None,
        format: bool | None = None,
        gamma: bool | None = None,
        slicecrc: bool | None = None,
        coder: bool | None = None,
        context: bool | None = None,
        mpv_flags: bool | None = None,
        error_rate: bool | None = None,
        qsquish: bool | None = None,
        rc_qmod_amp: bool | None = None,
        rc_qmod_freq: bool | None = None,
        rc_eq: bool | None = None,
        rc_init_cplx: bool | None = None,
        border_mask: bool | None = None,
        lmin: bool | None = None,
        lmax: bool | None = None,
        pbias: bool | None = None,
        motion_est: bool | None = None,
        b_strategy: bool | None = None,
        b_sensitivity: bool | None = None,
        brd_scale: bool | None = None,
        skip_threshold: bool | None = None,
        skip_factor: bool | None = None,
        skip_exp: bool | None = None,
        skip_cmp: bool | None = None,
        sc_threshold: bool | None = None,
        noise_reduction: bool | None = None,
        mpeg_quant: bool | None = None,
        ps: bool | None = None,
        mepc: bool | None = None,
        mepre: bool | None = None,
        intra_penalty: bool | None = None,
        a53cc: bool | None = None,
        rc_strategy: bool | None = None,
    ) -> str:
        """APNG encoder AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if dpi is not None:
            if dpi:
                cmd_args.append("-dpi")
        if dpm is not None:
            if dpm:
                cmd_args.append("-dpm")
        if pred is not None:
            if pred:
                cmd_args.append("-pred")
        if quality is not None:
            if quality:
                cmd_args.append("-quality")
        if skip_empty_cb is not None:
            if skip_empty_cb:
                cmd_args.append("-skip_empty_cb")
        if max_strips is not None:
            if max_strips:
                cmd_args.append("-max_strips")
        if min_strips is not None:
            if min_strips:
                cmd_args.append("-min_strips")
        if dither_type is not None:
            if dither_type:
                cmd_args.append("-dither_type")
        if nitris_compat is not None:
            if nitris_compat:
                cmd_args.append("-nitris_compat")
        if ibias is not None:
            if ibias:
                cmd_args.append("-ibias")
        if profile is not None:
            if profile:
                cmd_args.append("-profile")
        if quant_deadzone is not None:
            if quant_deadzone:
                cmd_args.append("-quant_deadzone")
        if compression is not None:
            if compression:
                cmd_args.append("-compression")
        if format is not None:
            if format:
                cmd_args.append("-format")
        if gamma is not None:
            if gamma:
                cmd_args.append("-gamma")
        if slicecrc is not None:
            if slicecrc:
                cmd_args.append("-slicecrc")
        if coder is not None:
            if coder:
                cmd_args.append("-coder")
        if context is not None:
            if context:
                cmd_args.append("-context")
        if mpv_flags is not None:
            if mpv_flags:
                cmd_args.append("-mpv_flags")
        if error_rate is not None:
            if error_rate:
                cmd_args.append("-error_rate")
        if qsquish is not None:
            if qsquish:
                cmd_args.append("-qsquish")
        if rc_qmod_amp is not None:
            if rc_qmod_amp:
                cmd_args.append("-rc_qmod_amp")
        if rc_qmod_freq is not None:
            if rc_qmod_freq:
                cmd_args.append("-rc_qmod_freq")
        if rc_eq is not None:
            if rc_eq:
                cmd_args.append("-rc_eq")
        if rc_init_cplx is not None:
            if rc_init_cplx:
                cmd_args.append("-rc_init_cplx")
        if border_mask is not None:
            if border_mask:
                cmd_args.append("-border_mask")
        if lmin is not None:
            if lmin:
                cmd_args.append("-lmin")
        if lmax is not None:
            if lmax:
                cmd_args.append("-lmax")
        if pbias is not None:
            if pbias:
                cmd_args.append("-pbias")
        if motion_est is not None:
            if motion_est:
                cmd_args.append("-motion_est")
        if b_strategy is not None:
            if b_strategy:
                cmd_args.append("-b_strategy")
        if b_sensitivity is not None:
            if b_sensitivity:
                cmd_args.append("-b_sensitivity")
        if brd_scale is not None:
            if brd_scale:
                cmd_args.append("-brd_scale")
        if skip_threshold is not None:
            if skip_threshold:
                cmd_args.append("-skip_threshold")
        if skip_factor is not None:
            if skip_factor:
                cmd_args.append("-skip_factor")
        if skip_exp is not None:
            if skip_exp:
                cmd_args.append("-skip_exp")
        if skip_cmp is not None:
            if skip_cmp:
                cmd_args.append("-skip_cmp")
        if sc_threshold is not None:
            if sc_threshold:
                cmd_args.append("-sc_threshold")
        if noise_reduction is not None:
            if noise_reduction:
                cmd_args.append("-noise_reduction")
        if mpeg_quant is not None:
            if mpeg_quant:
                cmd_args.append("-mpeg_quant")
        if ps is not None:
            if ps:
                cmd_args.append("-ps")
        if mepc is not None:
            if mepc:
                cmd_args.append("-mepc")
        if mepre is not None:
            if mepre:
                cmd_args.append("-mepre")
        if intra_penalty is not None:
            if intra_penalty:
                cmd_args.append("-intra_penalty")
        if a53cc is not None:
            if a53cc:
                cmd_args.append("-a53cc")
        if rc_strategy is not None:
            if rc_strategy:
                cmd_args.append("-rc_strategy")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_gif_encoder_avoptions(
        gifflags: bool | None = None,
        gifimage: bool | None = None,
        global_palette: bool | None = None,
        mpv_flags: bool | None = None,
        error_rate: bool | None = None,
        qsquish: bool | None = None,
        rc_qmod_amp: bool | None = None,
        rc_qmod_freq: bool | None = None,
        rc_eq: bool | None = None,
        rc_init_cplx: bool | None = None,
        border_mask: bool | None = None,
        lmin: bool | None = None,
        lmax: bool | None = None,
        ibias: bool | None = None,
        pbias: bool | None = None,
        motion_est: bool | None = None,
        b_strategy: bool | None = None,
        b_sensitivity: bool | None = None,
        brd_scale: bool | None = None,
        skip_threshold: bool | None = None,
        skip_factor: bool | None = None,
        skip_exp: bool | None = None,
        skip_cmp: bool | None = None,
        sc_threshold: bool | None = None,
        noise_reduction: bool | None = None,
        mpeg_quant: bool | None = None,
        ps: bool | None = None,
        mepc: bool | None = None,
        mepre: bool | None = None,
        intra_penalty: bool | None = None,
        a53cc: bool | None = None,
        rc_strategy: bool | None = None,
        obmc: bool | None = None,
        mb_info: bool | None = None,
        umv: bool | None = None,
        aiv: bool | None = None,
    ) -> str:
        """GIF encoder AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if gifflags is not None:
            if gifflags:
                cmd_args.append("-gifflags")
        if gifimage is not None:
            if gifimage:
                cmd_args.append("-gifimage")
        if global_palette is not None:
            if global_palette:
                cmd_args.append("-global_palette")
        if mpv_flags is not None:
            if mpv_flags:
                cmd_args.append("-mpv_flags")
        if error_rate is not None:
            if error_rate:
                cmd_args.append("-error_rate")
        if qsquish is not None:
            if qsquish:
                cmd_args.append("-qsquish")
        if rc_qmod_amp is not None:
            if rc_qmod_amp:
                cmd_args.append("-rc_qmod_amp")
        if rc_qmod_freq is not None:
            if rc_qmod_freq:
                cmd_args.append("-rc_qmod_freq")
        if rc_eq is not None:
            if rc_eq:
                cmd_args.append("-rc_eq")
        if rc_init_cplx is not None:
            if rc_init_cplx:
                cmd_args.append("-rc_init_cplx")
        if border_mask is not None:
            if border_mask:
                cmd_args.append("-border_mask")
        if lmin is not None:
            if lmin:
                cmd_args.append("-lmin")
        if lmax is not None:
            if lmax:
                cmd_args.append("-lmax")
        if ibias is not None:
            if ibias:
                cmd_args.append("-ibias")
        if pbias is not None:
            if pbias:
                cmd_args.append("-pbias")
        if motion_est is not None:
            if motion_est:
                cmd_args.append("-motion_est")
        if b_strategy is not None:
            if b_strategy:
                cmd_args.append("-b_strategy")
        if b_sensitivity is not None:
            if b_sensitivity:
                cmd_args.append("-b_sensitivity")
        if brd_scale is not None:
            if brd_scale:
                cmd_args.append("-brd_scale")
        if skip_threshold is not None:
            if skip_threshold:
                cmd_args.append("-skip_threshold")
        if skip_factor is not None:
            if skip_factor:
                cmd_args.append("-skip_factor")
        if skip_exp is not None:
            if skip_exp:
                cmd_args.append("-skip_exp")
        if skip_cmp is not None:
            if skip_cmp:
                cmd_args.append("-skip_cmp")
        if sc_threshold is not None:
            if sc_threshold:
                cmd_args.append("-sc_threshold")
        if noise_reduction is not None:
            if noise_reduction:
                cmd_args.append("-noise_reduction")
        if mpeg_quant is not None:
            if mpeg_quant:
                cmd_args.append("-mpeg_quant")
        if ps is not None:
            if ps:
                cmd_args.append("-ps")
        if mepc is not None:
            if mepc:
                cmd_args.append("-mepc")
        if mepre is not None:
            if mepre:
                cmd_args.append("-mepre")
        if intra_penalty is not None:
            if intra_penalty:
                cmd_args.append("-intra_penalty")
        if a53cc is not None:
            if a53cc:
                cmd_args.append("-a53cc")
        if rc_strategy is not None:
            if rc_strategy:
                cmd_args.append("-rc_strategy")
        if obmc is not None:
            if obmc:
                cmd_args.append("-obmc")
        if mb_info is not None:
            if mb_info:
                cmd_args.append("-mb_info")
        if umv is not None:
            if umv:
                cmd_args.append("-umv")
        if aiv is not None:
            if aiv:
                cmd_args.append("-aiv")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_hap_encoder_avoptions(
        format: bool | None = None,
        chunks: bool | None = None,
        compressor: bool | None = None,
        pred: bool | None = None,
        tile_width: bool | None = None,
        tile_height: bool | None = None,
        sop: bool | None = None,
        eph: bool | None = None,
        prog: bool | None = None,
        layer_rates: bool | None = None,
        mpv_flags: bool | None = None,
        error_rate: bool | None = None,
        qsquish: bool | None = None,
        rc_qmod_amp: bool | None = None,
        rc_qmod_freq: bool | None = None,
        rc_eq: bool | None = None,
        rc_init_cplx: bool | None = None,
        border_mask: bool | None = None,
        lmin: bool | None = None,
        lmax: bool | None = None,
        ibias: bool | None = None,
        pbias: bool | None = None,
        motion_est: bool | None = None,
        b_strategy: bool | None = None,
        b_sensitivity: bool | None = None,
        brd_scale: bool | None = None,
        skip_threshold: bool | None = None,
        skip_factor: bool | None = None,
        skip_exp: bool | None = None,
        skip_cmp: bool | None = None,
        sc_threshold: bool | None = None,
        noise_reduction: bool | None = None,
        mpeg_quant: bool | None = None,
        ps: bool | None = None,
        mepc: bool | None = None,
        mepre: bool | None = None,
        intra_penalty: bool | None = None,
        a53cc: bool | None = None,
        rc_strategy: bool | None = None,
        huffman: bool | None = None,
        gop_timecode: bool | None = None,
        scan_offset: bool | None = None,
        intra_vlc: bool | None = None,
        non_linear_quant: bool | None = None,
        alternate_scan: bool | None = None,
        seq_disp_ext: bool | None = None,
        video_format: bool | None = None,
    ) -> str:
        """Hap encoder AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if format is not None:
            if format:
                cmd_args.append("-format")
        if chunks is not None:
            if chunks:
                cmd_args.append("-chunks")
        if compressor is not None:
            if compressor:
                cmd_args.append("-compressor")
        if pred is not None:
            if pred:
                cmd_args.append("-pred")
        if tile_width is not None:
            if tile_width:
                cmd_args.append("-tile_width")
        if tile_height is not None:
            if tile_height:
                cmd_args.append("-tile_height")
        if sop is not None:
            if sop:
                cmd_args.append("-sop")
        if eph is not None:
            if eph:
                cmd_args.append("-eph")
        if prog is not None:
            if prog:
                cmd_args.append("-prog")
        if layer_rates is not None:
            if layer_rates:
                cmd_args.append("-layer_rates")
        if mpv_flags is not None:
            if mpv_flags:
                cmd_args.append("-mpv_flags")
        if error_rate is not None:
            if error_rate:
                cmd_args.append("-error_rate")
        if qsquish is not None:
            if qsquish:
                cmd_args.append("-qsquish")
        if rc_qmod_amp is not None:
            if rc_qmod_amp:
                cmd_args.append("-rc_qmod_amp")
        if rc_qmod_freq is not None:
            if rc_qmod_freq:
                cmd_args.append("-rc_qmod_freq")
        if rc_eq is not None:
            if rc_eq:
                cmd_args.append("-rc_eq")
        if rc_init_cplx is not None:
            if rc_init_cplx:
                cmd_args.append("-rc_init_cplx")
        if border_mask is not None:
            if border_mask:
                cmd_args.append("-border_mask")
        if lmin is not None:
            if lmin:
                cmd_args.append("-lmin")
        if lmax is not None:
            if lmax:
                cmd_args.append("-lmax")
        if ibias is not None:
            if ibias:
                cmd_args.append("-ibias")
        if pbias is not None:
            if pbias:
                cmd_args.append("-pbias")
        if motion_est is not None:
            if motion_est:
                cmd_args.append("-motion_est")
        if b_strategy is not None:
            if b_strategy:
                cmd_args.append("-b_strategy")
        if b_sensitivity is not None:
            if b_sensitivity:
                cmd_args.append("-b_sensitivity")
        if brd_scale is not None:
            if brd_scale:
                cmd_args.append("-brd_scale")
        if skip_threshold is not None:
            if skip_threshold:
                cmd_args.append("-skip_threshold")
        if skip_factor is not None:
            if skip_factor:
                cmd_args.append("-skip_factor")
        if skip_exp is not None:
            if skip_exp:
                cmd_args.append("-skip_exp")
        if skip_cmp is not None:
            if skip_cmp:
                cmd_args.append("-skip_cmp")
        if sc_threshold is not None:
            if sc_threshold:
                cmd_args.append("-sc_threshold")
        if noise_reduction is not None:
            if noise_reduction:
                cmd_args.append("-noise_reduction")
        if mpeg_quant is not None:
            if mpeg_quant:
                cmd_args.append("-mpeg_quant")
        if ps is not None:
            if ps:
                cmd_args.append("-ps")
        if mepc is not None:
            if mepc:
                cmd_args.append("-mepc")
        if mepre is not None:
            if mepre:
                cmd_args.append("-mepre")
        if intra_penalty is not None:
            if intra_penalty:
                cmd_args.append("-intra_penalty")
        if a53cc is not None:
            if a53cc:
                cmd_args.append("-a53cc")
        if rc_strategy is not None:
            if rc_strategy:
                cmd_args.append("-rc_strategy")
        if huffman is not None:
            if huffman:
                cmd_args.append("-huffman")
        if gop_timecode is not None:
            if gop_timecode:
                cmd_args.append("-gop_timecode")
        if scan_offset is not None:
            if scan_offset:
                cmd_args.append("-scan_offset")
        if intra_vlc is not None:
            if intra_vlc:
                cmd_args.append("-intra_vlc")
        if non_linear_quant is not None:
            if non_linear_quant:
                cmd_args.append("-non_linear_quant")
        if alternate_scan is not None:
            if alternate_scan:
                cmd_args.append("-alternate_scan")
        if seq_disp_ext is not None:
            if seq_disp_ext:
                cmd_args.append("-seq_disp_ext")
        if video_format is not None:
            if video_format:
                cmd_args.append("-video_format")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_png_encoder_avoptions(
        dpi: bool | None = None,
        dpm: bool | None = None,
        pred: bool | None = None,
    ) -> str:
        """PNG encoder AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if dpi is not None:
            if dpi:
                cmd_args.append("-dpi")
        if dpm is not None:
            if dpm:
                cmd_args.append("-dpm")
        if pred is not None:
            if pred:
                cmd_args.append("-pred")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_prores_encoder_avoptions(
        vendor: bool | None = None,
    ) -> str:
        """ProRes encoder AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if vendor is not None:
            if vendor:
                cmd_args.append("-vendor")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_proresaw_encoder_avoptions(
        vendor: bool | None = None,
    ) -> str:
        """ProResAw encoder AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if vendor is not None:
            if vendor:
                cmd_args.append("-vendor")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_roq_avoptions(
        quake3_compat: bool | None = None,
        mpv_flags: bool | None = None,
        error_rate: bool | None = None,
        qsquish: bool | None = None,
        rc_qmod_amp: bool | None = None,
        rc_qmod_freq: bool | None = None,
        rc_eq: bool | None = None,
        rc_init_cplx: bool | None = None,
        border_mask: bool | None = None,
        lmin: bool | None = None,
        lmax: bool | None = None,
        ibias: bool | None = None,
        pbias: bool | None = None,
        motion_est: bool | None = None,
        b_strategy: bool | None = None,
        b_sensitivity: bool | None = None,
        brd_scale: bool | None = None,
        skip_threshold: bool | None = None,
        skip_factor: bool | None = None,
        skip_exp: bool | None = None,
        skip_cmp: bool | None = None,
        sc_threshold: bool | None = None,
        noise_reduction: bool | None = None,
        mpeg_quant: bool | None = None,
        ps: bool | None = None,
        mepc: bool | None = None,
        mepre: bool | None = None,
        intra_penalty: bool | None = None,
        a53cc: bool | None = None,
        rc_strategy: bool | None = None,
        rle: bool | None = None,
        memc_only: bool | None = None,
        no_bitstream: bool | None = None,
        pred: bool | None = None,
    ) -> str:
        """RoQ AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if quake3_compat is not None:
            if quake3_compat:
                cmd_args.append("-quake3_compat")
        if mpv_flags is not None:
            if mpv_flags:
                cmd_args.append("-mpv_flags")
        if error_rate is not None:
            if error_rate:
                cmd_args.append("-error_rate")
        if qsquish is not None:
            if qsquish:
                cmd_args.append("-qsquish")
        if rc_qmod_amp is not None:
            if rc_qmod_amp:
                cmd_args.append("-rc_qmod_amp")
        if rc_qmod_freq is not None:
            if rc_qmod_freq:
                cmd_args.append("-rc_qmod_freq")
        if rc_eq is not None:
            if rc_eq:
                cmd_args.append("-rc_eq")
        if rc_init_cplx is not None:
            if rc_init_cplx:
                cmd_args.append("-rc_init_cplx")
        if border_mask is not None:
            if border_mask:
                cmd_args.append("-border_mask")
        if lmin is not None:
            if lmin:
                cmd_args.append("-lmin")
        if lmax is not None:
            if lmax:
                cmd_args.append("-lmax")
        if ibias is not None:
            if ibias:
                cmd_args.append("-ibias")
        if pbias is not None:
            if pbias:
                cmd_args.append("-pbias")
        if motion_est is not None:
            if motion_est:
                cmd_args.append("-motion_est")
        if b_strategy is not None:
            if b_strategy:
                cmd_args.append("-b_strategy")
        if b_sensitivity is not None:
            if b_sensitivity:
                cmd_args.append("-b_sensitivity")
        if brd_scale is not None:
            if brd_scale:
                cmd_args.append("-brd_scale")
        if skip_threshold is not None:
            if skip_threshold:
                cmd_args.append("-skip_threshold")
        if skip_factor is not None:
            if skip_factor:
                cmd_args.append("-skip_factor")
        if skip_exp is not None:
            if skip_exp:
                cmd_args.append("-skip_exp")
        if skip_cmp is not None:
            if skip_cmp:
                cmd_args.append("-skip_cmp")
        if sc_threshold is not None:
            if sc_threshold:
                cmd_args.append("-sc_threshold")
        if noise_reduction is not None:
            if noise_reduction:
                cmd_args.append("-noise_reduction")
        if mpeg_quant is not None:
            if mpeg_quant:
                cmd_args.append("-mpeg_quant")
        if ps is not None:
            if ps:
                cmd_args.append("-ps")
        if mepc is not None:
            if mepc:
                cmd_args.append("-mepc")
        if mepre is not None:
            if mepre:
                cmd_args.append("-mepre")
        if intra_penalty is not None:
            if intra_penalty:
                cmd_args.append("-intra_penalty")
        if a53cc is not None:
            if a53cc:
                cmd_args.append("-a53cc")
        if rc_strategy is not None:
            if rc_strategy:
                cmd_args.append("-rc_strategy")
        if rle is not None:
            if rle:
                cmd_args.append("-rle")
        if memc_only is not None:
            if memc_only:
                cmd_args.append("-memc_only")
        if no_bitstream is not None:
            if no_bitstream:
                cmd_args.append("-no_bitstream")
        if pred is not None:
            if pred:
                cmd_args.append("-pred")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_tiff_encoder_avoptions(
        dpi: bool | None = None,
        compression_algo: bool | None = None,
        pred: bool | None = None,
        tolerance: bool | None = None,
        slice_width: bool | None = None,
        slice_height: bool | None = None,
        wavelet_depth: bool | None = None,
        wavelet_type: bool | None = None,
        qm: bool | None = None,
        mpv_flags: bool | None = None,
        error_rate: bool | None = None,
        qsquish: bool | None = None,
        rc_qmod_amp: bool | None = None,
        rc_qmod_freq: bool | None = None,
        rc_eq: bool | None = None,
        rc_init_cplx: bool | None = None,
        border_mask: bool | None = None,
        lmin: bool | None = None,
        lmax: bool | None = None,
        ibias: bool | None = None,
        pbias: bool | None = None,
        motion_est: bool | None = None,
        b_strategy: bool | None = None,
        b_sensitivity: bool | None = None,
        brd_scale: bool | None = None,
        skip_threshold: bool | None = None,
        skip_factor: bool | None = None,
        skip_exp: bool | None = None,
        skip_cmp: bool | None = None,
        sc_threshold: bool | None = None,
        noise_reduction: bool | None = None,
        mpeg_quant: bool | None = None,
        ps: bool | None = None,
        mepc: bool | None = None,
        mepre: bool | None = None,
        intra_penalty: bool | None = None,
        a53cc: bool | None = None,
        rc_strategy: bool | None = None,
    ) -> str:
        """TIFF encoder AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if dpi is not None:
            if dpi:
                cmd_args.append("-dpi")
        if compression_algo is not None:
            if compression_algo:
                cmd_args.append("-compression_algo")
        if pred is not None:
            if pred:
                cmd_args.append("-pred")
        if tolerance is not None:
            if tolerance:
                cmd_args.append("-tolerance")
        if slice_width is not None:
            if slice_width:
                cmd_args.append("-slice_width")
        if slice_height is not None:
            if slice_height:
                cmd_args.append("-slice_height")
        if wavelet_depth is not None:
            if wavelet_depth:
                cmd_args.append("-wavelet_depth")
        if wavelet_type is not None:
            if wavelet_type:
                cmd_args.append("-wavelet_type")
        if qm is not None:
            if qm:
                cmd_args.append("-qm")
        if mpv_flags is not None:
            if mpv_flags:
                cmd_args.append("-mpv_flags")
        if error_rate is not None:
            if error_rate:
                cmd_args.append("-error_rate")
        if qsquish is not None:
            if qsquish:
                cmd_args.append("-qsquish")
        if rc_qmod_amp is not None:
            if rc_qmod_amp:
                cmd_args.append("-rc_qmod_amp")
        if rc_qmod_freq is not None:
            if rc_qmod_freq:
                cmd_args.append("-rc_qmod_freq")
        if rc_eq is not None:
            if rc_eq:
                cmd_args.append("-rc_eq")
        if rc_init_cplx is not None:
            if rc_init_cplx:
                cmd_args.append("-rc_init_cplx")
        if border_mask is not None:
            if border_mask:
                cmd_args.append("-border_mask")
        if lmin is not None:
            if lmin:
                cmd_args.append("-lmin")
        if lmax is not None:
            if lmax:
                cmd_args.append("-lmax")
        if ibias is not None:
            if ibias:
                cmd_args.append("-ibias")
        if pbias is not None:
            if pbias:
                cmd_args.append("-pbias")
        if motion_est is not None:
            if motion_est:
                cmd_args.append("-motion_est")
        if b_strategy is not None:
            if b_strategy:
                cmd_args.append("-b_strategy")
        if b_sensitivity is not None:
            if b_sensitivity:
                cmd_args.append("-b_sensitivity")
        if brd_scale is not None:
            if brd_scale:
                cmd_args.append("-brd_scale")
        if skip_threshold is not None:
            if skip_threshold:
                cmd_args.append("-skip_threshold")
        if skip_factor is not None:
            if skip_factor:
                cmd_args.append("-skip_factor")
        if skip_exp is not None:
            if skip_exp:
                cmd_args.append("-skip_exp")
        if skip_cmp is not None:
            if skip_cmp:
                cmd_args.append("-skip_cmp")
        if sc_threshold is not None:
            if sc_threshold:
                cmd_args.append("-sc_threshold")
        if noise_reduction is not None:
            if noise_reduction:
                cmd_args.append("-noise_reduction")
        if mpeg_quant is not None:
            if mpeg_quant:
                cmd_args.append("-mpeg_quant")
        if ps is not None:
            if ps:
                cmd_args.append("-ps")
        if mepc is not None:
            if mepc:
                cmd_args.append("-mepc")
        if mepre is not None:
            if mepre:
                cmd_args.append("-mepre")
        if intra_penalty is not None:
            if intra_penalty:
                cmd_args.append("-intra_penalty")
        if a53cc is not None:
            if a53cc:
                cmd_args.append("-a53cc")
        if rc_strategy is not None:
            if rc_strategy:
                cmd_args.append("-rc_strategy")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_aac_encoder_avoptions(
        aac_coder: bool | None = None,
        aac_ms: bool | None = None,
        aac_is: bool | None = None,
        aac_pns: bool | None = None,
        aac_tns: bool | None = None,
        aac_ltp: bool | None = None,
        aac_pred: bool | None = None,
        aac_pce: bool | None = None,
        center_mixlev: bool | None = None,
        surround_mixlev: bool | None = None,
        mixing_level: bool | None = None,
        room_type: bool | None = None,
        copyright: bool | None = None,
        dialnorm: bool | None = None,
        dsur_mode: bool | None = None,
        original: bool | None = None,
        dmix_mode: bool | None = None,
        ltrt_cmixlev: bool | None = None,
        ltrt_surmixlev: bool | None = None,
        loro_cmixlev: bool | None = None,
        loro_surmixlev: bool | None = None,
        dsurex_mode: bool | None = None,
        dheadphone_mode: bool | None = None,
        ad_conv_type: bool | None = None,
        channel_coupling: bool | None = None,
        cpl_start_band: bool | None = None,
    ) -> str:
        """AAC encoder AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if aac_coder is not None:
            if aac_coder:
                cmd_args.append("-aac_coder")
        if aac_ms is not None:
            if aac_ms:
                cmd_args.append("-aac_ms")
        if aac_is is not None:
            if aac_is:
                cmd_args.append("-aac_is")
        if aac_pns is not None:
            if aac_pns:
                cmd_args.append("-aac_pns")
        if aac_tns is not None:
            if aac_tns:
                cmd_args.append("-aac_tns")
        if aac_ltp is not None:
            if aac_ltp:
                cmd_args.append("-aac_ltp")
        if aac_pred is not None:
            if aac_pred:
                cmd_args.append("-aac_pred")
        if aac_pce is not None:
            if aac_pce:
                cmd_args.append("-aac_pce")
        if center_mixlev is not None:
            if center_mixlev:
                cmd_args.append("-center_mixlev")
        if surround_mixlev is not None:
            if surround_mixlev:
                cmd_args.append("-surround_mixlev")
        if mixing_level is not None:
            if mixing_level:
                cmd_args.append("-mixing_level")
        if room_type is not None:
            if room_type:
                cmd_args.append("-room_type")
        if copyright is not None:
            if copyright:
                cmd_args.append("-copyright")
        if dialnorm is not None:
            if dialnorm:
                cmd_args.append("-dialnorm")
        if dsur_mode is not None:
            if dsur_mode:
                cmd_args.append("-dsur_mode")
        if original is not None:
            if original:
                cmd_args.append("-original")
        if dmix_mode is not None:
            if dmix_mode:
                cmd_args.append("-dmix_mode")
        if ltrt_cmixlev is not None:
            if ltrt_cmixlev:
                cmd_args.append("-ltrt_cmixlev")
        if ltrt_surmixlev is not None:
            if ltrt_surmixlev:
                cmd_args.append("-ltrt_surmixlev")
        if loro_cmixlev is not None:
            if loro_cmixlev:
                cmd_args.append("-loro_cmixlev")
        if loro_surmixlev is not None:
            if loro_surmixlev:
                cmd_args.append("-loro_surmixlev")
        if dsurex_mode is not None:
            if dsurex_mode:
                cmd_args.append("-dsurex_mode")
        if dheadphone_mode is not None:
            if dheadphone_mode:
                cmd_args.append("-dheadphone_mode")
        if ad_conv_type is not None:
            if ad_conv_type:
                cmd_args.append("-ad_conv_type")
        if channel_coupling is not None:
            if channel_coupling:
                cmd_args.append("-channel_coupling")
        if cpl_start_band is not None:
            if cpl_start_band:
                cmd_args.append("-cpl_start_band")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_dca_dts_coherent_acoustics_avoptions(
        dca_adpcm: bool | None = None,
        mixing_level: bool | None = None,
        room_type: bool | None = None,
        copyright: bool | None = None,
        dialnorm: bool | None = None,
        dsur_mode: bool | None = None,
        original: bool | None = None,
        dmix_mode: bool | None = None,
        ltrt_cmixlev: bool | None = None,
        ltrt_surmixlev: bool | None = None,
        loro_cmixlev: bool | None = None,
        loro_surmixlev: bool | None = None,
        dsurex_mode: bool | None = None,
        dheadphone_mode: bool | None = None,
        ad_conv_type: bool | None = None,
        channel_coupling: bool | None = None,
        cpl_start_band: bool | None = None,
    ) -> str:
        """DCA (DTS Coherent Acoustics) AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if dca_adpcm is not None:
            if dca_adpcm:
                cmd_args.append("-dca_adpcm")
        if mixing_level is not None:
            if mixing_level:
                cmd_args.append("-mixing_level")
        if room_type is not None:
            if room_type:
                cmd_args.append("-room_type")
        if copyright is not None:
            if copyright:
                cmd_args.append("-copyright")
        if dialnorm is not None:
            if dialnorm:
                cmd_args.append("-dialnorm")
        if dsur_mode is not None:
            if dsur_mode:
                cmd_args.append("-dsur_mode")
        if original is not None:
            if original:
                cmd_args.append("-original")
        if dmix_mode is not None:
            if dmix_mode:
                cmd_args.append("-dmix_mode")
        if ltrt_cmixlev is not None:
            if ltrt_cmixlev:
                cmd_args.append("-ltrt_cmixlev")
        if ltrt_surmixlev is not None:
            if ltrt_surmixlev:
                cmd_args.append("-ltrt_surmixlev")
        if loro_cmixlev is not None:
            if loro_cmixlev:
                cmd_args.append("-loro_cmixlev")
        if loro_surmixlev is not None:
            if loro_surmixlev:
                cmd_args.append("-loro_surmixlev")
        if dsurex_mode is not None:
            if dsurex_mode:
                cmd_args.append("-dsurex_mode")
        if dheadphone_mode is not None:
            if dheadphone_mode:
                cmd_args.append("-dheadphone_mode")
        if ad_conv_type is not None:
            if ad_conv_type:
                cmd_args.append("-ad_conv_type")
        if channel_coupling is not None:
            if channel_coupling:
                cmd_args.append("-channel_coupling")
        if cpl_start_band is not None:
            if cpl_start_band:
                cmd_args.append("-cpl_start_band")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_flac_encoder_avoptions(
        lpc_type: bool | None = None,
        lpc_passes: bool | None = None,
        ch_mode: bool | None = None,
        multi_dim_quant: bool | None = None,
    ) -> str:
        """FLAC encoder AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if lpc_type is not None:
            if lpc_type:
                cmd_args.append("-lpc_type")
        if lpc_passes is not None:
            if lpc_passes:
                cmd_args.append("-lpc_passes")
        if ch_mode is not None:
            if ch_mode:
                cmd_args.append("-ch_mode")
        if multi_dim_quant is not None:
            if multi_dim_quant:
                cmd_args.append("-multi_dim_quant")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_opus_encoder_avoptions(
        opus_delay: bool | None = None,
        apply_phase_inv: bool | None = None,
        sbc_delay: bool | None = None,
        msbc: bool | None = None,
    ) -> str:
        """Opus encoder AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if opus_delay is not None:
            if opus_delay:
                cmd_args.append("-opus_delay")
        if apply_phase_inv is not None:
            if apply_phase_inv:
                cmd_args.append("-apply_phase_inv")
        if sbc_delay is not None:
            if sbc_delay:
                cmd_args.append("-sbc_delay")
        if msbc is not None:
            if msbc:
                cmd_args.append("-msbc")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_wavpack_encoder_avoptions(
        joint_stereo: bool | None = None,
        optimize_mono: bool | None = None,
        block_size: bool | None = None,
        code_size: bool | None = None,
    ) -> str:
        """WavPack encoder AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if joint_stereo is not None:
            if joint_stereo:
                cmd_args.append("-joint_stereo")
        if optimize_mono is not None:
            if optimize_mono:
                cmd_args.append("-optimize_mono")
        if block_size is not None:
            if block_size:
                cmd_args.append("-block_size")
        if code_size is not None:
            if code_size:
                cmd_args.append("-code_size")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_vobsub_subtitle_encoder_avoptions(
        palette: bool | None = None,
        even_rows_fix: bool | None = None,
    ) -> str:
        """VOBSUB subtitle encoder AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if palette is not None:
            if palette:
                cmd_args.append("-palette")
        if even_rows_fix is not None:
            if even_rows_fix:
                cmd_args.append("-even_rows_fix")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_mov_text_enoder_avoptions(
        height: bool | None = None,
        crf: bool | None = None,
        tiles: bool | None = None,
        usage: bool | None = None,
        tune: bool | None = None,
        mode: bool | None = None,
        reservoir: bool | None = None,
        joint_stereo: bool | None = None,
        abr: bool | None = None,
        format: bool | None = None,
        profile: bool | None = None,
        cinema_mode: bool | None = None,
        prog_order: bool | None = None,
        numresolution: bool | None = None,
        irreversible: bool | None = None,
        disto_alloc: bool | None = None,
        fixed_quality: bool | None = None,
        application: bool | None = None,
        frame_duration: bool | None = None,
        packet_loss: bool | None = None,
        fec: bool | None = None,
        vbr: bool | None = None,
        mapping_family: bool | None = None,
        apply_phase_inv: bool | None = None,
        cbr_quality: bool | None = None,
        vad: bool | None = None,
        dtx: bool | None = None,
        psymodel: bool | None = None,
        energy_levels: bool | None = None,
        error_protection: bool | None = None,
        copyright: bool | None = None,
        original: bool | None = None,
        verbosity: bool | None = None,
        iblock: bool | None = None,
        deadline: bool | None = None,
        speed: bool | None = None,
        quality: bool | None = None,
        vp8flags: bool | None = None,
        arnr_max_frames: bool | None = None,
        arnr_strength: bool | None = None,
        arnr_type: bool | None = None,
        rc_lookahead: bool | None = None,
        sharpness: bool | None = None,
        lossless: bool | None = None,
        level: bool | None = None,
        preset: bool | None = None,
        cr_threshold: bool | None = None,
        cr_size: bool | None = None,
        fastfirstpass: bool | None = None,
        passlogfile: bool | None = None,
        wpredp: bool | None = None,
        a53cc: bool | None = None,
        x264opts: bool | None = None,
        crf_max: bool | None = None,
        qp: bool | None = None,
        psy: bool | None = None,
        weightb: bool | None = None,
        weightp: bool | None = None,
        ssim: bool | None = None,
        p_8x8dct: bool | None = None,
        aud: bool | None = None,
        mbtree: bool | None = None,
        deblock: bool | None = None,
        cplxblur: bool | None = None,
        partitions: bool | None = None,
        stats: bool | None = None,
        me_method: bool | None = None,
        coder: bool | None = None,
        b_strategy: bool | None = None,
        chromaoffset: bool | None = None,
        sc_threshold: bool | None = None,
        noise_reduction: bool | None = None,
        lumi_aq: bool | None = None,
        variance_aq: bool | None = None,
        ssim_acc: bool | None = None,
        gmc: bool | None = None,
        me_quality: bool | None = None,
        mpeg_quant: bool | None = None,
        rc: bool | None = None,
        surfaces: bool | None = None,
        cbr: bool | None = None,
        p_2pass: bool | None = None,
        gpu: bool | None = None,
        delay: bool | None = None,
        b_adapt: bool | None = None,
        spatial_aq: bool | None = None,
        temporal_aq: bool | None = None,
        zerolatency: bool | None = None,
        nonref_p: bool | None = None,
        strict_gop: bool | None = None,
        cq: bool | None = None,
        init_qpP: bool | None = None,
        init_qpB: bool | None = None,
        init_qpI: bool | None = None,
        weighted_pred: bool | None = None,
        b_ref_mode: bool | None = None,
        dpb_size: bool | None = None,
        multipass: bool | None = None,
        ldkfs: bool | None = None,
        omx_libname: bool | None = None,
        omx_libprefix: bool | None = None,
        zerocopy: bool | None = None,
        async_depth: bool | None = None,
        avbr_accuracy: bool | None = None,
        avbr_convergence: bool | None = None,
        rdo: bool | None = None,
        max_frame_size: bool | None = None,
        max_slice_size: bool | None = None,
        bitrate_limit: bool | None = None,
        mbbrc: bool | None = None,
        extbrc: bool | None = None,
        adaptive_i: bool | None = None,
        adaptive_b: bool | None = None,
        forced_idr: bool | None = None,
        low_power: bool | None = None,
        cavlc: bool | None = None,
        idr_interval: bool | None = None,
        pic_timing_sei: bool | None = None,
        look_ahead: bool | None = None,
        look_ahead_depth: bool | None = None,
        int_ref_type: bool | None = None,
        int_ref_qp_delta: bool | None = None,
        mfmode: bool | None = None,
        repeat_pps: bool | None = None,
        b_depth: bool | None = None,
        rc_mode: bool | None = None,
        sei: bool | None = None,
        tier: bool | None = None,
        s12m_tc: bool | None = None,
        load_plugin: bool | None = None,
        load_plugins: bool | None = None,
        gpb: bool | None = None,
        tile_cols: bool | None = None,
        tile_rows: bool | None = None,
        jfif: bool | None = None,
        huffman: bool | None = None,
    ) -> str:
        """MOV text enoder AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if height is not None:
            if height:
                cmd_args.append("-height")
        if crf is not None:
            if crf:
                cmd_args.append("-crf")
        if tiles is not None:
            if tiles:
                cmd_args.append("-tiles")
        if usage is not None:
            if usage:
                cmd_args.append("-usage")
        if tune is not None:
            if tune:
                cmd_args.append("-tune")
        if mode is not None:
            if mode:
                cmd_args.append("-mode")
        if reservoir is not None:
            if reservoir:
                cmd_args.append("-reservoir")
        if joint_stereo is not None:
            if joint_stereo:
                cmd_args.append("-joint_stereo")
        if abr is not None:
            if abr:
                cmd_args.append("-abr")
        if format is not None:
            if format:
                cmd_args.append("-format")
        if profile is not None:
            if profile:
                cmd_args.append("-profile")
        if cinema_mode is not None:
            if cinema_mode:
                cmd_args.append("-cinema_mode")
        if prog_order is not None:
            if prog_order:
                cmd_args.append("-prog_order")
        if numresolution is not None:
            if numresolution:
                cmd_args.append("-numresolution")
        if irreversible is not None:
            if irreversible:
                cmd_args.append("-irreversible")
        if disto_alloc is not None:
            if disto_alloc:
                cmd_args.append("-disto_alloc")
        if fixed_quality is not None:
            if fixed_quality:
                cmd_args.append("-fixed_quality")
        if application is not None:
            if application:
                cmd_args.append("-application")
        if frame_duration is not None:
            if frame_duration:
                cmd_args.append("-frame_duration")
        if packet_loss is not None:
            if packet_loss:
                cmd_args.append("-packet_loss")
        if fec is not None:
            if fec:
                cmd_args.append("-fec")
        if vbr is not None:
            if vbr:
                cmd_args.append("-vbr")
        if mapping_family is not None:
            if mapping_family:
                cmd_args.append("-mapping_family")
        if apply_phase_inv is not None:
            if apply_phase_inv:
                cmd_args.append("-apply_phase_inv")
        if cbr_quality is not None:
            if cbr_quality:
                cmd_args.append("-cbr_quality")
        if vad is not None:
            if vad:
                cmd_args.append("-vad")
        if dtx is not None:
            if dtx:
                cmd_args.append("-dtx")
        if psymodel is not None:
            if psymodel:
                cmd_args.append("-psymodel")
        if energy_levels is not None:
            if energy_levels:
                cmd_args.append("-energy_levels")
        if error_protection is not None:
            if error_protection:
                cmd_args.append("-error_protection")
        if copyright is not None:
            if copyright:
                cmd_args.append("-copyright")
        if original is not None:
            if original:
                cmd_args.append("-original")
        if verbosity is not None:
            if verbosity:
                cmd_args.append("-verbosity")
        if iblock is not None:
            if iblock:
                cmd_args.append("-iblock")
        if deadline is not None:
            if deadline:
                cmd_args.append("-deadline")
        if speed is not None:
            if speed:
                cmd_args.append("-speed")
        if quality is not None:
            if quality:
                cmd_args.append("-quality")
        if vp8flags is not None:
            if vp8flags:
                cmd_args.append("-vp8flags")
        if arnr_max_frames is not None:
            if arnr_max_frames:
                cmd_args.append("-arnr_max_frames")
        if arnr_strength is not None:
            if arnr_strength:
                cmd_args.append("-arnr_strength")
        if arnr_type is not None:
            if arnr_type:
                cmd_args.append("-arnr_type")
        if rc_lookahead is not None:
            if rc_lookahead:
                cmd_args.append("-rc_lookahead")
        if sharpness is not None:
            if sharpness:
                cmd_args.append("-sharpness")
        if lossless is not None:
            if lossless:
                cmd_args.append("-lossless")
        if level is not None:
            if level:
                cmd_args.append("-level")
        if preset is not None:
            if preset:
                cmd_args.append("-preset")
        if cr_threshold is not None:
            if cr_threshold:
                cmd_args.append("-cr_threshold")
        if cr_size is not None:
            if cr_size:
                cmd_args.append("-cr_size")
        if fastfirstpass is not None:
            if fastfirstpass:
                cmd_args.append("-fastfirstpass")
        if passlogfile is not None:
            if passlogfile:
                cmd_args.append("-passlogfile")
        if wpredp is not None:
            if wpredp:
                cmd_args.append("-wpredp")
        if a53cc is not None:
            if a53cc:
                cmd_args.append("-a53cc")
        if x264opts is not None:
            if x264opts:
                cmd_args.append("-x264opts")
        if crf_max is not None:
            if crf_max:
                cmd_args.append("-crf_max")
        if qp is not None:
            if qp:
                cmd_args.append("-qp")
        if psy is not None:
            if psy:
                cmd_args.append("-psy")
        if weightb is not None:
            if weightb:
                cmd_args.append("-weightb")
        if weightp is not None:
            if weightp:
                cmd_args.append("-weightp")
        if ssim is not None:
            if ssim:
                cmd_args.append("-ssim")
        if p_8x8dct is not None:
            if p_8x8dct:
                cmd_args.append("-8x8dct")
        if aud is not None:
            if aud:
                cmd_args.append("-aud")
        if mbtree is not None:
            if mbtree:
                cmd_args.append("-mbtree")
        if deblock is not None:
            if deblock:
                cmd_args.append("-deblock")
        if cplxblur is not None:
            if cplxblur:
                cmd_args.append("-cplxblur")
        if partitions is not None:
            if partitions:
                cmd_args.append("-partitions")
        if stats is not None:
            if stats:
                cmd_args.append("-stats")
        if me_method is not None:
            if me_method:
                cmd_args.append("-me_method")
        if coder is not None:
            if coder:
                cmd_args.append("-coder")
        if b_strategy is not None:
            if b_strategy:
                cmd_args.append("-b_strategy")
        if chromaoffset is not None:
            if chromaoffset:
                cmd_args.append("-chromaoffset")
        if sc_threshold is not None:
            if sc_threshold:
                cmd_args.append("-sc_threshold")
        if noise_reduction is not None:
            if noise_reduction:
                cmd_args.append("-noise_reduction")
        if lumi_aq is not None:
            if lumi_aq:
                cmd_args.append("-lumi_aq")
        if variance_aq is not None:
            if variance_aq:
                cmd_args.append("-variance_aq")
        if ssim_acc is not None:
            if ssim_acc:
                cmd_args.append("-ssim_acc")
        if gmc is not None:
            if gmc:
                cmd_args.append("-gmc")
        if me_quality is not None:
            if me_quality:
                cmd_args.append("-me_quality")
        if mpeg_quant is not None:
            if mpeg_quant:
                cmd_args.append("-mpeg_quant")
        if rc is not None:
            if rc:
                cmd_args.append("-rc")
        if surfaces is not None:
            if surfaces:
                cmd_args.append("-surfaces")
        if cbr is not None:
            if cbr:
                cmd_args.append("-cbr")
        if p_2pass is not None:
            if p_2pass:
                cmd_args.append("-2pass")
        if gpu is not None:
            if gpu:
                cmd_args.append("-gpu")
        if delay is not None:
            if delay:
                cmd_args.append("-delay")
        if b_adapt is not None:
            if b_adapt:
                cmd_args.append("-b_adapt")
        if spatial_aq is not None:
            if spatial_aq:
                cmd_args.append("-spatial_aq")
        if temporal_aq is not None:
            if temporal_aq:
                cmd_args.append("-temporal_aq")
        if zerolatency is not None:
            if zerolatency:
                cmd_args.append("-zerolatency")
        if nonref_p is not None:
            if nonref_p:
                cmd_args.append("-nonref_p")
        if strict_gop is not None:
            if strict_gop:
                cmd_args.append("-strict_gop")
        if cq is not None:
            if cq:
                cmd_args.append("-cq")
        if init_qpP is not None:
            if init_qpP:
                cmd_args.append("-init_qpP")
        if init_qpB is not None:
            if init_qpB:
                cmd_args.append("-init_qpB")
        if init_qpI is not None:
            if init_qpI:
                cmd_args.append("-init_qpI")
        if weighted_pred is not None:
            if weighted_pred:
                cmd_args.append("-weighted_pred")
        if b_ref_mode is not None:
            if b_ref_mode:
                cmd_args.append("-b_ref_mode")
        if dpb_size is not None:
            if dpb_size:
                cmd_args.append("-dpb_size")
        if multipass is not None:
            if multipass:
                cmd_args.append("-multipass")
        if ldkfs is not None:
            if ldkfs:
                cmd_args.append("-ldkfs")
        if omx_libname is not None:
            if omx_libname:
                cmd_args.append("-omx_libname")
        if omx_libprefix is not None:
            if omx_libprefix:
                cmd_args.append("-omx_libprefix")
        if zerocopy is not None:
            if zerocopy:
                cmd_args.append("-zerocopy")
        if async_depth is not None:
            if async_depth:
                cmd_args.append("-async_depth")
        if avbr_accuracy is not None:
            if avbr_accuracy:
                cmd_args.append("-avbr_accuracy")
        if avbr_convergence is not None:
            if avbr_convergence:
                cmd_args.append("-avbr_convergence")
        if rdo is not None:
            if rdo:
                cmd_args.append("-rdo")
        if max_frame_size is not None:
            if max_frame_size:
                cmd_args.append("-max_frame_size")
        if max_slice_size is not None:
            if max_slice_size:
                cmd_args.append("-max_slice_size")
        if bitrate_limit is not None:
            if bitrate_limit:
                cmd_args.append("-bitrate_limit")
        if mbbrc is not None:
            if mbbrc:
                cmd_args.append("-mbbrc")
        if extbrc is not None:
            if extbrc:
                cmd_args.append("-extbrc")
        if adaptive_i is not None:
            if adaptive_i:
                cmd_args.append("-adaptive_i")
        if adaptive_b is not None:
            if adaptive_b:
                cmd_args.append("-adaptive_b")
        if forced_idr is not None:
            if forced_idr:
                cmd_args.append("-forced_idr")
        if low_power is not None:
            if low_power:
                cmd_args.append("-low_power")
        if cavlc is not None:
            if cavlc:
                cmd_args.append("-cavlc")
        if idr_interval is not None:
            if idr_interval:
                cmd_args.append("-idr_interval")
        if pic_timing_sei is not None:
            if pic_timing_sei:
                cmd_args.append("-pic_timing_sei")
        if look_ahead is not None:
            if look_ahead:
                cmd_args.append("-look_ahead")
        if look_ahead_depth is not None:
            if look_ahead_depth:
                cmd_args.append("-look_ahead_depth")
        if int_ref_type is not None:
            if int_ref_type:
                cmd_args.append("-int_ref_type")
        if int_ref_qp_delta is not None:
            if int_ref_qp_delta:
                cmd_args.append("-int_ref_qp_delta")
        if mfmode is not None:
            if mfmode:
                cmd_args.append("-mfmode")
        if repeat_pps is not None:
            if repeat_pps:
                cmd_args.append("-repeat_pps")
        if b_depth is not None:
            if b_depth:
                cmd_args.append("-b_depth")
        if rc_mode is not None:
            if rc_mode:
                cmd_args.append("-rc_mode")
        if sei is not None:
            if sei:
                cmd_args.append("-sei")
        if tier is not None:
            if tier:
                cmd_args.append("-tier")
        if s12m_tc is not None:
            if s12m_tc:
                cmd_args.append("-s12m_tc")
        if load_plugin is not None:
            if load_plugin:
                cmd_args.append("-load_plugin")
        if load_plugins is not None:
            if load_plugins:
                cmd_args.append("-load_plugins")
        if gpb is not None:
            if gpb:
                cmd_args.append("-gpb")
        if tile_cols is not None:
            if tile_cols:
                cmd_args.append("-tile_cols")
        if tile_rows is not None:
            if tile_rows:
                cmd_args.append("-tile_rows")
        if jfif is not None:
            if jfif:
                cmd_args.append("-jfif")
        if huffman is not None:
            if huffman:
                cmd_args.append("-huffman")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_exr_avoptions(
        layer: bool | None = None,
        part: bool | None = None,
        gamma: bool | None = None,
        apply_trc: bool | None = None,
    ) -> str:
        """EXR AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if layer is not None:
            if layer:
                cmd_args.append("-layer")
        if part is not None:
            if part:
                cmd_args.append("-part")
        if gamma is not None:
            if gamma:
                cmd_args.append("-gamma")
        if apply_trc is not None:
            if apply_trc:
                cmd_args.append("-apply_trc")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_fic_decoder_avoptions(
        skip_cursor: bool | None = None,
    ) -> str:
        """FIC decoder AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if skip_cursor is not None:
            if skip_cursor:
                cmd_args.append("-skip_cursor")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_fits_decoder_avoptions(
        blank_value: bool | None = None,
        trans_color: bool | None = None,
        enable_er: bool | None = None,
        x264_build: bool | None = None,
        async_depth: bool | None = None,
        gpu_copy: bool | None = None,
    ) -> str:
        """FITS decoder AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if blank_value is not None:
            if blank_value:
                cmd_args.append("-blank_value")
        if trans_color is not None:
            if trans_color:
                cmd_args.append("-trans_color")
        if enable_er is not None:
            if enable_er:
                cmd_args.append("-enable_er")
        if x264_build is not None:
            if x264_build:
                cmd_args.append("-x264_build")
        if async_depth is not None:
            if async_depth:
                cmd_args.append("-async_depth")
        if gpu_copy is not None:
            if gpu_copy:
                cmd_args.append("-gpu_copy")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_hevc_decoder_avoptions(
        apply_defdispwin: bool | None = None,
        async_depth: bool | None = None,
        load_plugin: bool | None = None,
        load_plugins: bool | None = None,
        gpu_copy: bool | None = None,
        lowres: bool | None = None,
    ) -> str:
        """HEVC decoder AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if apply_defdispwin is not None:
            if apply_defdispwin:
                cmd_args.append("-apply_defdispwin")
        if async_depth is not None:
            if async_depth:
                cmd_args.append("-async_depth")
        if load_plugin is not None:
            if load_plugin:
                cmd_args.append("-load_plugin")
        if load_plugins is not None:
            if load_plugins:
                cmd_args.append("-load_plugins")
        if gpu_copy is not None:
            if gpu_copy:
                cmd_args.append("-gpu_copy")
        if lowres is not None:
            if lowres:
                cmd_args.append("-lowres")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_mjpeg_decoder_avoptions(
        extern_huff: bool | None = None,
        async_depth: bool | None = None,
        gpu_copy: bool | None = None,
        lowres: bool | None = None,
        skip_cursor: bool | None = None,
        top: bool | None = None,
        non_pcm_mode: bool | None = None,
    ) -> str:
        """MJPEG decoder AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if extern_huff is not None:
            if extern_huff:
                cmd_args.append("-extern_huff")
        if async_depth is not None:
            if async_depth:
                cmd_args.append("-async_depth")
        if gpu_copy is not None:
            if gpu_copy:
                cmd_args.append("-gpu_copy")
        if lowres is not None:
            if lowres:
                cmd_args.append("-lowres")
        if skip_cursor is not None:
            if skip_cursor:
                cmd_args.append("-skip_cursor")
        if top is not None:
            if top:
                cmd_args.append("-top")
        if non_pcm_mode is not None:
            if non_pcm_mode:
                cmd_args.append("-non_pcm_mode")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_tiff_decoder_avoptions(
        subimage: bool | None = None,
        thumbnail: bool | None = None,
        page: bool | None = None,
        custom_stride: bool | None = None,
        async_depth: bool | None = None,
        gpu_copy: bool | None = None,
    ) -> str:
        """TIFF decoder AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if subimage is not None:
            if subimage:
                cmd_args.append("-subimage")
        if thumbnail is not None:
            if thumbnail:
                cmd_args.append("-thumbnail")
        if page is not None:
            if page:
                cmd_args.append("-page")
        if custom_stride is not None:
            if custom_stride:
                cmd_args.append("-custom_stride")
        if async_depth is not None:
            if async_depth:
                cmd_args.append("-async_depth")
        if gpu_copy is not None:
            if gpu_copy:
                cmd_args.append("-gpu_copy")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_aac_decoder_avoptions(
        dual_mono_mode: bool | None = None,
        cons_noisegen: bool | None = None,
        drc_scale: bool | None = None,
        heavy_compr: bool | None = None,
        target_level: bool | None = None,
        extra_bits_bug: bool | None = None,
    ) -> str:
        """AAC decoder AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if dual_mono_mode is not None:
            if dual_mono_mode:
                cmd_args.append("-dual_mono_mode")
        if cons_noisegen is not None:
            if cons_noisegen:
                cmd_args.append("-cons_noisegen")
        if drc_scale is not None:
            if drc_scale:
                cmd_args.append("-drc_scale")
        if heavy_compr is not None:
            if heavy_compr:
                cmd_args.append("-heavy_compr")
        if target_level is not None:
            if target_level:
                cmd_args.append("-target_level")
        if extra_bits_bug is not None:
            if extra_bits_bug:
                cmd_args.append("-extra_bits_bug")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_ape_decoder_avoptions(
        max_samples: bool | None = None,
    ) -> str:
        """APE decoder AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if max_samples is not None:
            if max_samples:
                cmd_args.append("-max_samples")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_dca_decoder_avoptions(
        core_only: bool | None = None,
        cons_noisegen: bool | None = None,
        drc_scale: bool | None = None,
        heavy_compr: bool | None = None,
        target_level: bool | None = None,
        postfilter: bool | None = None,
    ) -> str:
        """DCA decoder AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if core_only is not None:
            if core_only:
                cmd_args.append("-core_only")
        if cons_noisegen is not None:
            if cons_noisegen:
                cmd_args.append("-cons_noisegen")
        if drc_scale is not None:
            if drc_scale:
                cmd_args.append("-drc_scale")
        if heavy_compr is not None:
            if heavy_compr:
                cmd_args.append("-heavy_compr")
        if target_level is not None:
            if target_level:
                cmd_args.append("-target_level")
        if postfilter is not None:
            if postfilter:
                cmd_args.append("-postfilter")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_flac_decoder_avoptions(
        use_buggy_lpc: bool | None = None,
        postfilter: bool | None = None,
    ) -> str:
        """FLAC decoder AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if use_buggy_lpc is not None:
            if use_buggy_lpc:
                cmd_args.append("-use_buggy_lpc")
        if postfilter is not None:
            if postfilter:
                cmd_args.append("-postfilter")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_opus_decoder_avoptions(
        apply_phase_inv: bool | None = None,
    ) -> str:
        """Opus Decoder AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if apply_phase_inv is not None:
            if apply_phase_inv:
                cmd_args.append("-apply_phase_inv")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_tta_decoder_avoptions(
        password: bool | None = None,
    ) -> str:
        """TTA Decoder AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if password is not None:
            if password:
                cmd_args.append("-password")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_closed_caption_decoder_avoptions(
        real_time: bool | None = None,
        data_field: bool | None = None,
    ) -> str:
        """Closed caption Decoder AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if real_time is not None:
            if real_time:
                cmd_args.append("-real_time")
        if data_field is not None:
            if data_field:
                cmd_args.append("-data_field")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_dvb_sub_decoder_avoptions(
        compute_edt: bool | None = None,
        compute_clut: bool | None = None,
        dvb_substream: bool | None = None,
        palette: bool | None = None,
        ifo_palette: bool | None = None,
        forced_subs_only: bool | None = None,
    ) -> str:
        """DVB Sub Decoder AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if compute_edt is not None:
            if compute_edt:
                cmd_args.append("-compute_edt")
        if compute_clut is not None:
            if compute_clut:
                cmd_args.append("-compute_clut")
        if dvb_substream is not None:
            if dvb_substream:
                cmd_args.append("-dvb_substream")
        if palette is not None:
            if palette:
                cmd_args.append("-palette")
        if ifo_palette is not None:
            if ifo_palette:
                cmd_args.append("-ifo_palette")
        if forced_subs_only is not None:
            if forced_subs_only:
                cmd_args.append("-forced_subs_only")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_mov_text_decoder_avoptions(
        width: bool | None = None,
        height: bool | None = None,
    ) -> str:
        """MOV text decoder AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if width is not None:
            if width:
                cmd_args.append("-width")
        if height is not None:
            if height:
                cmd_args.append("-height")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_pgs_subtitle_decoder_avoptions(
        forced_subs_only: bool | None = None,
        keep_ass_markup: bool | None = None,
        tilethreads: bool | None = None,
        framethreads: bool | None = None,
        filmgrain: bool | None = None,
        oppoint: bool | None = None,
        alllayers: bool | None = None,
        lowqual: bool | None = None,
        apply_phase_inv: bool | None = None,
    ) -> str:
        """PGS subtitle decoder AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if forced_subs_only is not None:
            if forced_subs_only:
                cmd_args.append("-forced_subs_only")
        if keep_ass_markup is not None:
            if keep_ass_markup:
                cmd_args.append("-keep_ass_markup")
        if tilethreads is not None:
            if tilethreads:
                cmd_args.append("-tilethreads")
        if framethreads is not None:
            if framethreads:
                cmd_args.append("-framethreads")
        if filmgrain is not None:
            if filmgrain:
                cmd_args.append("-filmgrain")
        if oppoint is not None:
            if oppoint:
                cmd_args.append("-oppoint")
        if alllayers is not None:
            if alllayers:
                cmd_args.append("-alllayers")
        if lowqual is not None:
            if lowqual:
                cmd_args.append("-lowqual")
        if apply_phase_inv is not None:
            if apply_phase_inv:
                cmd_args.append("-apply_phase_inv")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_librsvg_avoptions(
        width: bool | None = None,
        height: bool | None = None,
        keep_ar: bool | None = None,
        txt_page: bool | None = None,
        txt_chop_top: bool | None = None,
        txt_format: bool | None = None,
        txt_left: bool | None = None,
        txt_top: bool | None = None,
        txt_chop_spaces: bool | None = None,
        txt_duration: bool | None = None,
        txt_transparent: bool | None = None,
        txt_opacity: bool | None = None,
        operating_point: bool | None = None,
        deint: bool | None = None,
        gpu: bool | None = None,
        surfaces: bool | None = None,
        crop: bool | None = None,
        resize: bool | None = None,
        async_depth: bool | None = None,
        gpu_copy: bool | None = None,
    ) -> str:
        """Librsvg AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if width is not None:
            if width:
                cmd_args.append("-width")
        if height is not None:
            if height:
                cmd_args.append("-height")
        if keep_ar is not None:
            if keep_ar:
                cmd_args.append("-keep_ar")
        if txt_page is not None:
            if txt_page:
                cmd_args.append("-txt_page")
        if txt_chop_top is not None:
            if txt_chop_top:
                cmd_args.append("-txt_chop_top")
        if txt_format is not None:
            if txt_format:
                cmd_args.append("-txt_format")
        if txt_left is not None:
            if txt_left:
                cmd_args.append("-txt_left")
        if txt_top is not None:
            if txt_top:
                cmd_args.append("-txt_top")
        if txt_chop_spaces is not None:
            if txt_chop_spaces:
                cmd_args.append("-txt_chop_spaces")
        if txt_duration is not None:
            if txt_duration:
                cmd_args.append("-txt_duration")
        if txt_transparent is not None:
            if txt_transparent:
                cmd_args.append("-txt_transparent")
        if txt_opacity is not None:
            if txt_opacity:
                cmd_args.append("-txt_opacity")
        if operating_point is not None:
            if operating_point:
                cmd_args.append("-operating_point")
        if deint is not None:
            if deint:
                cmd_args.append("-deint")
        if gpu is not None:
            if gpu:
                cmd_args.append("-gpu")
        if surfaces is not None:
            if surfaces:
                cmd_args.append("-surfaces")
        if crop is not None:
            if crop:
                cmd_args.append("-crop")
        if resize is not None:
            if resize:
                cmd_args.append("-resize")
        if async_depth is not None:
            if async_depth:
                cmd_args.append("-async_depth")
        if gpu_copy is not None:
            if gpu_copy:
                cmd_args.append("-gpu_copy")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_avformatcontext_avoptions(
        avioflags: bool | None = None,
        probesize: bool | None = None,
        formatprobesize: bool | None = None,
        packetsize: bool | None = None,
        fflags: bool | None = None,
        seek2any: bool | None = None,
        analyzeduration: bool | None = None,
        cryptokey: bool | None = None,
        indexmem: bool | None = None,
        rtbufsize: bool | None = None,
        fdebug: bool | None = None,
        max_delay: bool | None = None,
        fpsprobesize: bool | None = None,
        audio_preload: bool | None = None,
        chunk_duration: bool | None = None,
        chunk_size: bool | None = None,
        f_err_detect: bool | None = None,
        err_detect: bool | None = None,
        flush_packets: bool | None = None,
        output_ts_offset: bool | None = None,
        f_strict: bool | None = None,
        strict: bool | None = None,
        max_ts_probe: bool | None = None,
        dump_separator: bool | None = None,
        codec_whitelist: bool | None = None,
        format_whitelist: bool | None = None,
        max_streams: bool | None = None,
    ) -> str:
        """AVFormatContext AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if avioflags is not None:
            if avioflags:
                cmd_args.append("-avioflags")
        if probesize is not None:
            if probesize:
                cmd_args.append("-probesize")
        if formatprobesize is not None:
            if formatprobesize:
                cmd_args.append("-formatprobesize")
        if packetsize is not None:
            if packetsize:
                cmd_args.append("-packetsize")
        if fflags is not None:
            if fflags:
                cmd_args.append("-fflags")
        if seek2any is not None:
            if seek2any:
                cmd_args.append("-seek2any")
        if analyzeduration is not None:
            if analyzeduration:
                cmd_args.append("-analyzeduration")
        if cryptokey is not None:
            if cryptokey:
                cmd_args.append("-cryptokey")
        if indexmem is not None:
            if indexmem:
                cmd_args.append("-indexmem")
        if rtbufsize is not None:
            if rtbufsize:
                cmd_args.append("-rtbufsize")
        if fdebug is not None:
            if fdebug:
                cmd_args.append("-fdebug")
        if max_delay is not None:
            if max_delay:
                cmd_args.append("-max_delay")
        if fpsprobesize is not None:
            if fpsprobesize:
                cmd_args.append("-fpsprobesize")
        if audio_preload is not None:
            if audio_preload:
                cmd_args.append("-audio_preload")
        if chunk_duration is not None:
            if chunk_duration:
                cmd_args.append("-chunk_duration")
        if chunk_size is not None:
            if chunk_size:
                cmd_args.append("-chunk_size")
        if f_err_detect is not None:
            if f_err_detect:
                cmd_args.append("-f_err_detect")
        if err_detect is not None:
            if err_detect:
                cmd_args.append("-err_detect")
        if flush_packets is not None:
            if flush_packets:
                cmd_args.append("-flush_packets")
        if output_ts_offset is not None:
            if output_ts_offset:
                cmd_args.append("-output_ts_offset")
        if f_strict is not None:
            if f_strict:
                cmd_args.append("-f_strict")
        if strict is not None:
            if strict:
                cmd_args.append("-strict")
        if max_ts_probe is not None:
            if max_ts_probe:
                cmd_args.append("-max_ts_probe")
        if dump_separator is not None:
            if dump_separator:
                cmd_args.append("-dump_separator")
        if codec_whitelist is not None:
            if codec_whitelist:
                cmd_args.append("-codec_whitelist")
        if format_whitelist is not None:
            if format_whitelist:
                cmd_args.append("-format_whitelist")
        if max_streams is not None:
            if max_streams:
                cmd_args.append("-max_streams")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_urlcontext_avoptions(
        rw_timeout: bool | None = None,
    ) -> str:
        """URLContext AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if rw_timeout is not None:
            if rw_timeout:
                cmd_args.append("-rw_timeout")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_async_avoptions(
        playlist: bool | None = None,
        angle: bool | None = None,
        chapter: bool | None = None,
        read_ahead_limit: bool | None = None,
        key: bool | None = None,
        iv: bool | None = None,
        decryption_key: bool | None = None,
        decryption_iv: bool | None = None,
        encryption_key: bool | None = None,
        encryption_iv: bool | None = None,
        ffrtmphttp_tls: bool | None = None,
        truncate: bool | None = None,
        blocksize: bool | None = None,
        follow: bool | None = None,
        seekable: bool | None = None,
        timeout: bool | None = None,
        chunked_post: bool | None = None,
        http_proxy: bool | None = None,
        headers: bool | None = None,
        content_type: bool | None = None,
        user_agent: bool | None = None,
        referer: bool | None = None,
        post_data: bool | None = None,
        cookies: bool | None = None,
        icy: bool | None = None,
        auth_type: bool | None = None,
        send_expect_100: bool | None = None,
        location: bool | None = None,
        offset: bool | None = None,
        end_offset: bool | None = None,
        method: bool | None = None,
        reconnect: bool | None = None,
        reconnect_at_eof: bool | None = None,
        listen: bool | None = None,
        resource: bool | None = None,
        reply_code: bool | None = None,
        ice_genre: bool | None = None,
        ice_name: bool | None = None,
        ice_description: bool | None = None,
        ice_url: bool | None = None,
        ice_public: bool | None = None,
        password: bool | None = None,
        legacy_icecast: bool | None = None,
        tls: bool | None = None,
        ttl: bool | None = None,
        l: bool | None = None,
        d: bool | None = None,
        rtmp_app: bool | None = None,
        rtmp_buffer: bool | None = None,
        rtmp_conn: bool | None = None,
        rtmp_flashver: bool | None = None,
        rtmp_live: bool | None = None,
        rtmp_pageurl: bool | None = None,
        rtmp_playpath: bool | None = None,
        rtmp_subscribe: bool | None = None,
        rtmp_swfhash: bool | None = None,
        rtmp_swfsize: bool | None = None,
        rtmp_swfurl: bool | None = None,
        rtmp_swfverify: bool | None = None,
        rtmp_tcurl: bool | None = None,
        rtmp_listen: bool | None = None,
        buffer_size: bool | None = None,
        rtcp_port: bool | None = None,
        local_rtpport: bool | None = None,
        local_rtcpport: bool | None = None,
        connect: bool | None = None,
        write_to_source: bool | None = None,
        pkt_size: bool | None = None,
        dscp: bool | None = None,
        sources: bool | None = None,
        block: bool | None = None,
        fec: bool | None = None,
        listen_timeout: bool | None = None,
        max_streams: bool | None = None,
        srtp_out_suite: bool | None = None,
        srtp_out_params: bool | None = None,
        srtp_in_suite: bool | None = None,
        srtp_in_params: bool | None = None,
        start: bool | None = None,
        end: bool | None = None,
        send_buffer_size: bool | None = None,
        recv_buffer_size: bool | None = None,
        tcp_nodelay: bool | None = None,
        tcp_mss: bool | None = None,
        ca_file: bool | None = None,
        cafile: bool | None = None,
        tls_verify: bool | None = None,
        cert_file: bool | None = None,
        key_file: bool | None = None,
        verifyhost: bool | None = None,
        bitrate: bool | None = None,
        burst_bits: bool | None = None,
        localport: bool | None = None,
        local_port: bool | None = None,
        localaddr: bool | None = None,
        udplite_coverage: bool | None = None,
        reuse: bool | None = None,
        reuse_socket: bool | None = None,
        broadcast: bool | None = None,
        fifo_size: bool | None = None,
        overrun_nonfatal: bool | None = None,
        type: bool | None = None,
        exchange: bool | None = None,
        routing_key: bool | None = None,
        delivery_mode: bool | None = None,
        payload_size: bool | None = None,
        maxbw: bool | None = None,
        pbkeylen: bool | None = None,
        passphrase: bool | None = None,
        kmrefreshrate: bool | None = None,
        kmpreannounce: bool | None = None,
        mss: bool | None = None,
        ffs: bool | None = None,
        ipttl: bool | None = None,
        iptos: bool | None = None,
        inputbw: bool | None = None,
        oheadbw: bool | None = None,
        latency: bool | None = None,
        tsbpddelay: bool | None = None,
        rcvlatency: bool | None = None,
        peerlatency: bool | None = None,
        tlpktdrop: bool | None = None,
        nakreport: bool | None = None,
        connect_timeout: bool | None = None,
        mode: bool | None = None,
        sndbuf: bool | None = None,
        rcvbuf: bool | None = None,
        lossmaxttl: bool | None = None,
        minversion: bool | None = None,
        streamid: bool | None = None,
        smoother: bool | None = None,
        messageapi: bool | None = None,
        transtype: bool | None = None,
        linger: bool | None = None,
        private_key: bool | None = None,
    ) -> str:
        """Async AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if playlist is not None:
            if playlist:
                cmd_args.append("-playlist")
        if angle is not None:
            if angle:
                cmd_args.append("-angle")
        if chapter is not None:
            if chapter:
                cmd_args.append("-chapter")
        if read_ahead_limit is not None:
            if read_ahead_limit:
                cmd_args.append("-read_ahead_limit")
        if key is not None:
            if key:
                cmd_args.append("-key")
        if iv is not None:
            if iv:
                cmd_args.append("-iv")
        if decryption_key is not None:
            if decryption_key:
                cmd_args.append("-decryption_key")
        if decryption_iv is not None:
            if decryption_iv:
                cmd_args.append("-decryption_iv")
        if encryption_key is not None:
            if encryption_key:
                cmd_args.append("-encryption_key")
        if encryption_iv is not None:
            if encryption_iv:
                cmd_args.append("-encryption_iv")
        if ffrtmphttp_tls is not None:
            if ffrtmphttp_tls:
                cmd_args.append("-ffrtmphttp_tls")
        if truncate is not None:
            if truncate:
                cmd_args.append("-truncate")
        if blocksize is not None:
            if blocksize:
                cmd_args.append("-blocksize")
        if follow is not None:
            if follow:
                cmd_args.append("-follow")
        if seekable is not None:
            if seekable:
                cmd_args.append("-seekable")
        if timeout is not None:
            if timeout:
                cmd_args.append("-timeout")
        if chunked_post is not None:
            if chunked_post:
                cmd_args.append("-chunked_post")
        if http_proxy is not None:
            if http_proxy:
                cmd_args.append("-http_proxy")
        if headers is not None:
            if headers:
                cmd_args.append("-headers")
        if content_type is not None:
            if content_type:
                cmd_args.append("-content_type")
        if user_agent is not None:
            if user_agent:
                cmd_args.append("-user_agent")
        if referer is not None:
            if referer:
                cmd_args.append("-referer")
        if post_data is not None:
            if post_data:
                cmd_args.append("-post_data")
        if cookies is not None:
            if cookies:
                cmd_args.append("-cookies")
        if icy is not None:
            if icy:
                cmd_args.append("-icy")
        if auth_type is not None:
            if auth_type:
                cmd_args.append("-auth_type")
        if send_expect_100 is not None:
            if send_expect_100:
                cmd_args.append("-send_expect_100")
        if location is not None:
            if location:
                cmd_args.append("-location")
        if offset is not None:
            if offset:
                cmd_args.append("-offset")
        if end_offset is not None:
            if end_offset:
                cmd_args.append("-end_offset")
        if method is not None:
            if method:
                cmd_args.append("-method")
        if reconnect is not None:
            if reconnect:
                cmd_args.append("-reconnect")
        if reconnect_at_eof is not None:
            if reconnect_at_eof:
                cmd_args.append("-reconnect_at_eof")
        if listen is not None:
            if listen:
                cmd_args.append("-listen")
        if resource is not None:
            if resource:
                cmd_args.append("-resource")
        if reply_code is not None:
            if reply_code:
                cmd_args.append("-reply_code")
        if ice_genre is not None:
            if ice_genre:
                cmd_args.append("-ice_genre")
        if ice_name is not None:
            if ice_name:
                cmd_args.append("-ice_name")
        if ice_description is not None:
            if ice_description:
                cmd_args.append("-ice_description")
        if ice_url is not None:
            if ice_url:
                cmd_args.append("-ice_url")
        if ice_public is not None:
            if ice_public:
                cmd_args.append("-ice_public")
        if password is not None:
            if password:
                cmd_args.append("-password")
        if legacy_icecast is not None:
            if legacy_icecast:
                cmd_args.append("-legacy_icecast")
        if tls is not None:
            if tls:
                cmd_args.append("-tls")
        if ttl is not None:
            if ttl:
                cmd_args.append("-ttl")
        if l is not None:
            if l:
                cmd_args.append("-l")
        if d is not None:
            if d:
                cmd_args.append("-d")
        if rtmp_app is not None:
            if rtmp_app:
                cmd_args.append("-rtmp_app")
        if rtmp_buffer is not None:
            if rtmp_buffer:
                cmd_args.append("-rtmp_buffer")
        if rtmp_conn is not None:
            if rtmp_conn:
                cmd_args.append("-rtmp_conn")
        if rtmp_flashver is not None:
            if rtmp_flashver:
                cmd_args.append("-rtmp_flashver")
        if rtmp_live is not None:
            if rtmp_live:
                cmd_args.append("-rtmp_live")
        if rtmp_pageurl is not None:
            if rtmp_pageurl:
                cmd_args.append("-rtmp_pageurl")
        if rtmp_playpath is not None:
            if rtmp_playpath:
                cmd_args.append("-rtmp_playpath")
        if rtmp_subscribe is not None:
            if rtmp_subscribe:
                cmd_args.append("-rtmp_subscribe")
        if rtmp_swfhash is not None:
            if rtmp_swfhash:
                cmd_args.append("-rtmp_swfhash")
        if rtmp_swfsize is not None:
            if rtmp_swfsize:
                cmd_args.append("-rtmp_swfsize")
        if rtmp_swfurl is not None:
            if rtmp_swfurl:
                cmd_args.append("-rtmp_swfurl")
        if rtmp_swfverify is not None:
            if rtmp_swfverify:
                cmd_args.append("-rtmp_swfverify")
        if rtmp_tcurl is not None:
            if rtmp_tcurl:
                cmd_args.append("-rtmp_tcurl")
        if rtmp_listen is not None:
            if rtmp_listen:
                cmd_args.append("-rtmp_listen")
        if buffer_size is not None:
            if buffer_size:
                cmd_args.append("-buffer_size")
        if rtcp_port is not None:
            if rtcp_port:
                cmd_args.append("-rtcp_port")
        if local_rtpport is not None:
            if local_rtpport:
                cmd_args.append("-local_rtpport")
        if local_rtcpport is not None:
            if local_rtcpport:
                cmd_args.append("-local_rtcpport")
        if connect is not None:
            if connect:
                cmd_args.append("-connect")
        if write_to_source is not None:
            if write_to_source:
                cmd_args.append("-write_to_source")
        if pkt_size is not None:
            if pkt_size:
                cmd_args.append("-pkt_size")
        if dscp is not None:
            if dscp:
                cmd_args.append("-dscp")
        if sources is not None:
            if sources:
                cmd_args.append("-sources")
        if block is not None:
            if block:
                cmd_args.append("-block")
        if fec is not None:
            if fec:
                cmd_args.append("-fec")
        if listen_timeout is not None:
            if listen_timeout:
                cmd_args.append("-listen_timeout")
        if max_streams is not None:
            if max_streams:
                cmd_args.append("-max_streams")
        if srtp_out_suite is not None:
            if srtp_out_suite:
                cmd_args.append("-srtp_out_suite")
        if srtp_out_params is not None:
            if srtp_out_params:
                cmd_args.append("-srtp_out_params")
        if srtp_in_suite is not None:
            if srtp_in_suite:
                cmd_args.append("-srtp_in_suite")
        if srtp_in_params is not None:
            if srtp_in_params:
                cmd_args.append("-srtp_in_params")
        if start is not None:
            if start:
                cmd_args.append("-start")
        if end is not None:
            if end:
                cmd_args.append("-end")
        if send_buffer_size is not None:
            if send_buffer_size:
                cmd_args.append("-send_buffer_size")
        if recv_buffer_size is not None:
            if recv_buffer_size:
                cmd_args.append("-recv_buffer_size")
        if tcp_nodelay is not None:
            if tcp_nodelay:
                cmd_args.append("-tcp_nodelay")
        if tcp_mss is not None:
            if tcp_mss:
                cmd_args.append("-tcp_mss")
        if ca_file is not None:
            if ca_file:
                cmd_args.append("-ca_file")
        if cafile is not None:
            if cafile:
                cmd_args.append("-cafile")
        if tls_verify is not None:
            if tls_verify:
                cmd_args.append("-tls_verify")
        if cert_file is not None:
            if cert_file:
                cmd_args.append("-cert_file")
        if key_file is not None:
            if key_file:
                cmd_args.append("-key_file")
        if verifyhost is not None:
            if verifyhost:
                cmd_args.append("-verifyhost")
        if bitrate is not None:
            if bitrate:
                cmd_args.append("-bitrate")
        if burst_bits is not None:
            if burst_bits:
                cmd_args.append("-burst_bits")
        if localport is not None:
            if localport:
                cmd_args.append("-localport")
        if local_port is not None:
            if local_port:
                cmd_args.append("-local_port")
        if localaddr is not None:
            if localaddr:
                cmd_args.append("-localaddr")
        if udplite_coverage is not None:
            if udplite_coverage:
                cmd_args.append("-udplite_coverage")
        if reuse is not None:
            if reuse:
                cmd_args.append("-reuse")
        if reuse_socket is not None:
            if reuse_socket:
                cmd_args.append("-reuse_socket")
        if broadcast is not None:
            if broadcast:
                cmd_args.append("-broadcast")
        if fifo_size is not None:
            if fifo_size:
                cmd_args.append("-fifo_size")
        if overrun_nonfatal is not None:
            if overrun_nonfatal:
                cmd_args.append("-overrun_nonfatal")
        if type is not None:
            if type:
                cmd_args.append("-type")
        if exchange is not None:
            if exchange:
                cmd_args.append("-exchange")
        if routing_key is not None:
            if routing_key:
                cmd_args.append("-routing_key")
        if delivery_mode is not None:
            if delivery_mode:
                cmd_args.append("-delivery_mode")
        if payload_size is not None:
            if payload_size:
                cmd_args.append("-payload_size")
        if maxbw is not None:
            if maxbw:
                cmd_args.append("-maxbw")
        if pbkeylen is not None:
            if pbkeylen:
                cmd_args.append("-pbkeylen")
        if passphrase is not None:
            if passphrase:
                cmd_args.append("-passphrase")
        if kmrefreshrate is not None:
            if kmrefreshrate:
                cmd_args.append("-kmrefreshrate")
        if kmpreannounce is not None:
            if kmpreannounce:
                cmd_args.append("-kmpreannounce")
        if mss is not None:
            if mss:
                cmd_args.append("-mss")
        if ffs is not None:
            if ffs:
                cmd_args.append("-ffs")
        if ipttl is not None:
            if ipttl:
                cmd_args.append("-ipttl")
        if iptos is not None:
            if iptos:
                cmd_args.append("-iptos")
        if inputbw is not None:
            if inputbw:
                cmd_args.append("-inputbw")
        if oheadbw is not None:
            if oheadbw:
                cmd_args.append("-oheadbw")
        if latency is not None:
            if latency:
                cmd_args.append("-latency")
        if tsbpddelay is not None:
            if tsbpddelay:
                cmd_args.append("-tsbpddelay")
        if rcvlatency is not None:
            if rcvlatency:
                cmd_args.append("-rcvlatency")
        if peerlatency is not None:
            if peerlatency:
                cmd_args.append("-peerlatency")
        if tlpktdrop is not None:
            if tlpktdrop:
                cmd_args.append("-tlpktdrop")
        if nakreport is not None:
            if nakreport:
                cmd_args.append("-nakreport")
        if connect_timeout is not None:
            if connect_timeout:
                cmd_args.append("-connect_timeout")
        if mode is not None:
            if mode:
                cmd_args.append("-mode")
        if sndbuf is not None:
            if sndbuf:
                cmd_args.append("-sndbuf")
        if rcvbuf is not None:
            if rcvbuf:
                cmd_args.append("-rcvbuf")
        if lossmaxttl is not None:
            if lossmaxttl:
                cmd_args.append("-lossmaxttl")
        if minversion is not None:
            if minversion:
                cmd_args.append("-minversion")
        if streamid is not None:
            if streamid:
                cmd_args.append("-streamid")
        if smoother is not None:
            if smoother:
                cmd_args.append("-smoother")
        if messageapi is not None:
            if messageapi:
                cmd_args.append("-messageapi")
        if transtype is not None:
            if transtype:
                cmd_args.append("-transtype")
        if linger is not None:
            if linger:
                cmd_args.append("-linger")
        if private_key is not None:
            if private_key:
                cmd_args.append("-private_key")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_adts_muxer_avoptions(
        write_id3v2: bool | None = None,
        write_apetag: bool | None = None,
        write_mpeg2: bool | None = None,
    ) -> str:
        """ADTS muxer AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if write_id3v2 is not None:
            if write_id3v2:
                cmd_args.append("-write_id3v2")
        if write_apetag is not None:
            if write_apetag:
                cmd_args.append("-write_apetag")
        if write_mpeg2 is not None:
            if write_mpeg2:
                cmd_args.append("-write_mpeg2")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_aiff_muxer_avoptions(
        write_id3v2: bool | None = None,
        id3v2_version: bool | None = None,
        type: bool | None = None,
    ) -> str:
        """AIFF muxer AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if write_id3v2 is not None:
            if write_id3v2:
                cmd_args.append("-write_id3v2")
        if id3v2_version is not None:
            if id3v2_version:
                cmd_args.append("-id3v2_version")
        if type is not None:
            if type:
                cmd_args.append("-type")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_apng_muxer_avoptions(
        plays: bool | None = None,
        final_delay: bool | None = None,
        version_major: bool | None = None,
        version_minor: bool | None = None,
        name: bool | None = None,
    ) -> str:
        """APNG muxer AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if plays is not None:
            if plays:
                cmd_args.append("-plays")
        if final_delay is not None:
            if final_delay:
                cmd_args.append("-final_delay")
        if version_major is not None:
            if version_major:
                cmd_args.append("-version_major")
        if version_minor is not None:
            if version_minor:
                cmd_args.append("-version_minor")
        if name is not None:
            if name:
                cmd_args.append("-name")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_asf_muxer_avoptions(
        packet_size: bool | None = None,
        ignore_readorder: bool | None = None,
    ) -> str:
        """ASF muxer AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if packet_size is not None:
            if packet_size:
                cmd_args.append("-packet_size")
        if ignore_readorder is not None:
            if ignore_readorder:
                cmd_args.append("-ignore_readorder")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_ast_muxer_avoptions(
        loopstart: bool | None = None,
        loopend: bool | None = None,
    ) -> str:
        """AST muxer AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if loopstart is not None:
            if loopstart:
                cmd_args.append("-loopstart")
        if loopend is not None:
            if loopend:
                cmd_args.append("-loopend")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_asf_stream_muxer_avoptions(
        packet_size: bool | None = None,
    ) -> str:
        """ASF stream muxer AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if packet_size is not None:
            if packet_size:
                cmd_args.append("-packet_size")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_avi_muxer_avoptions(
        flipped_raw_rgb: bool | None = None,
        adaptation_sets: bool | None = None,
        window_size: bool | None = None,
        min_seg_duration: bool | None = None,
        seg_duration: bool | None = None,
        frag_duration: bool | None = None,
        frag_type: bool | None = None,
        remove_at_exit: bool | None = None,
        use_template: bool | None = None,
        use_timeline: bool | None = None,
        single_file: bool | None = None,
        single_file_name: bool | None = None,
        init_seg_name: bool | None = None,
        media_seg_name: bool | None = None,
        utc_timing_url: bool | None = None,
        method: bool | None = None,
        http_user_agent: bool | None = None,
        http_persistent: bool | None = None,
        hls_playlist: bool | None = None,
        hls_master_name: bool | None = None,
        streaming: bool | None = None,
        timeout: bool | None = None,
        index_correction: bool | None = None,
        format_options: bool | None = None,
        global_sidx: bool | None = None,
        ignore_io_errors: bool | None = None,
        lhls: bool | None = None,
        ldash: bool | None = None,
        write_prft: bool | None = None,
        mpd_profile: bool | None = None,
        http_opts: bool | None = None,
        target_latency: bool | None = None,
        update_period: bool | None = None,
        movflags: bool | None = None,
        moov_size: bool | None = None,
        rtpflags: bool | None = None,
        skip_iods: bool | None = None,
        frag_size: bool | None = None,
        ism_lookahead: bool | None = None,
        brand: bool | None = None,
        use_editlist: bool | None = None,
        fragment_index: bool | None = None,
        mov_gamma: bool | None = None,
        frag_interleave: bool | None = None,
        encryption_key: bool | None = None,
        encryption_kid: bool | None = None,
        write_tmcd: bool | None = None,
        empty_hdlr_name: bool | None = None,
    ) -> str:
        """AVI muxer AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if flipped_raw_rgb is not None:
            if flipped_raw_rgb:
                cmd_args.append("-flipped_raw_rgb")
        if adaptation_sets is not None:
            if adaptation_sets:
                cmd_args.append("-adaptation_sets")
        if window_size is not None:
            if window_size:
                cmd_args.append("-window_size")
        if min_seg_duration is not None:
            if min_seg_duration:
                cmd_args.append("-min_seg_duration")
        if seg_duration is not None:
            if seg_duration:
                cmd_args.append("-seg_duration")
        if frag_duration is not None:
            if frag_duration:
                cmd_args.append("-frag_duration")
        if frag_type is not None:
            if frag_type:
                cmd_args.append("-frag_type")
        if remove_at_exit is not None:
            if remove_at_exit:
                cmd_args.append("-remove_at_exit")
        if use_template is not None:
            if use_template:
                cmd_args.append("-use_template")
        if use_timeline is not None:
            if use_timeline:
                cmd_args.append("-use_timeline")
        if single_file is not None:
            if single_file:
                cmd_args.append("-single_file")
        if single_file_name is not None:
            if single_file_name:
                cmd_args.append("-single_file_name")
        if init_seg_name is not None:
            if init_seg_name:
                cmd_args.append("-init_seg_name")
        if media_seg_name is not None:
            if media_seg_name:
                cmd_args.append("-media_seg_name")
        if utc_timing_url is not None:
            if utc_timing_url:
                cmd_args.append("-utc_timing_url")
        if method is not None:
            if method:
                cmd_args.append("-method")
        if http_user_agent is not None:
            if http_user_agent:
                cmd_args.append("-http_user_agent")
        if http_persistent is not None:
            if http_persistent:
                cmd_args.append("-http_persistent")
        if hls_playlist is not None:
            if hls_playlist:
                cmd_args.append("-hls_playlist")
        if hls_master_name is not None:
            if hls_master_name:
                cmd_args.append("-hls_master_name")
        if streaming is not None:
            if streaming:
                cmd_args.append("-streaming")
        if timeout is not None:
            if timeout:
                cmd_args.append("-timeout")
        if index_correction is not None:
            if index_correction:
                cmd_args.append("-index_correction")
        if format_options is not None:
            if format_options:
                cmd_args.append("-format_options")
        if global_sidx is not None:
            if global_sidx:
                cmd_args.append("-global_sidx")
        if ignore_io_errors is not None:
            if ignore_io_errors:
                cmd_args.append("-ignore_io_errors")
        if lhls is not None:
            if lhls:
                cmd_args.append("-lhls")
        if ldash is not None:
            if ldash:
                cmd_args.append("-ldash")
        if write_prft is not None:
            if write_prft:
                cmd_args.append("-write_prft")
        if mpd_profile is not None:
            if mpd_profile:
                cmd_args.append("-mpd_profile")
        if http_opts is not None:
            if http_opts:
                cmd_args.append("-http_opts")
        if target_latency is not None:
            if target_latency:
                cmd_args.append("-target_latency")
        if update_period is not None:
            if update_period:
                cmd_args.append("-update_period")
        if movflags is not None:
            if movflags:
                cmd_args.append("-movflags")
        if moov_size is not None:
            if moov_size:
                cmd_args.append("-moov_size")
        if rtpflags is not None:
            if rtpflags:
                cmd_args.append("-rtpflags")
        if skip_iods is not None:
            if skip_iods:
                cmd_args.append("-skip_iods")
        if frag_size is not None:
            if frag_size:
                cmd_args.append("-frag_size")
        if ism_lookahead is not None:
            if ism_lookahead:
                cmd_args.append("-ism_lookahead")
        if brand is not None:
            if brand:
                cmd_args.append("-brand")
        if use_editlist is not None:
            if use_editlist:
                cmd_args.append("-use_editlist")
        if fragment_index is not None:
            if fragment_index:
                cmd_args.append("-fragment_index")
        if mov_gamma is not None:
            if mov_gamma:
                cmd_args.append("-mov_gamma")
        if frag_interleave is not None:
            if frag_interleave:
                cmd_args.append("-frag_interleave")
        if encryption_key is not None:
            if encryption_key:
                cmd_args.append("-encryption_key")
        if encryption_kid is not None:
            if encryption_kid:
                cmd_args.append("-encryption_kid")
        if write_tmcd is not None:
            if write_tmcd:
                cmd_args.append("-write_tmcd")
        if empty_hdlr_name is not None:
            if empty_hdlr_name:
                cmd_args.append("-empty_hdlr_name")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_fifo_muxer_avoptions(
        fifo_format: bool | None = None,
        queue_size: bool | None = None,
        format_opts: bool | None = None,
        attempt_recovery: bool | None = None,
        timeshift: bool | None = None,
    ) -> str:
        """Fifo muxer AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if fifo_format is not None:
            if fifo_format:
                cmd_args.append("-fifo_format")
        if queue_size is not None:
            if queue_size:
                cmd_args.append("-queue_size")
        if format_opts is not None:
            if format_opts:
                cmd_args.append("-format_opts")
        if attempt_recovery is not None:
            if attempt_recovery:
                cmd_args.append("-attempt_recovery")
        if timeshift is not None:
            if timeshift:
                cmd_args.append("-timeshift")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_fifo_test_muxer_avoptions(
        write_header_ret: bool | None = None,
        write_header: bool | None = None,
        flvflags: bool | None = None,
        hash: bool | None = None,
        format_version: bool | None = None,
    ) -> str:
        """Fifo test muxer AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if write_header_ret is not None:
            if write_header_ret:
                cmd_args.append("-write_header_ret")
        if write_header is not None:
            if write_header:
                cmd_args.append("-write_header")
        if flvflags is not None:
            if flvflags:
                cmd_args.append("-flvflags")
        if hash is not None:
            if hash:
                cmd_args.append("-hash")
        if format_version is not None:
            if format_version:
                cmd_args.append("-format_version")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_gif_muxer_avoptions(
        loop: bool | None = None,
        final_delay: bool | None = None,
        hash: bool | None = None,
    ) -> str:
        """GIF muxer AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if loop is not None:
            if loop:
                cmd_args.append("-loop")
        if final_delay is not None:
            if final_delay:
                cmd_args.append("-final_delay")
        if hash is not None:
            if hash:
                cmd_args.append("-hash")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_hds_muxer_avoptions(
        window_size: bool | None = None,
        remove_at_exit: bool | None = None,
        start_number: bool | None = None,
        hls_time: bool | None = None,
        hls_init_time: bool | None = None,
        hls_list_size: bool | None = None,
        hls_ts_options: bool | None = None,
        hls_vtt_options: bool | None = None,
        hls_wrap: bool | None = None,
        hls_allow_cache: bool | None = None,
        hls_base_url: bool | None = None,
        hls_segment_size: bool | None = None,
        hls_enc: bool | None = None,
        hls_enc_key: bool | None = None,
        hls_enc_key_url: bool | None = None,
        hls_enc_iv: bool | None = None,
        hls_segment_type: bool | None = None,
        hls_flags: bool | None = None,
        use_localtime: bool | None = None,
        strftime: bool | None = None,
        strftime_mkdir: bool | None = None,
        method: bool | None = None,
        http_user_agent: bool | None = None,
        var_stream_map: bool | None = None,
        cc_stream_map: bool | None = None,
        master_pl_name: bool | None = None,
        http_persistent: bool | None = None,
        timeout: bool | None = None,
        ignore_io_errors: bool | None = None,
        headers: bool | None = None,
        update: bool | None = None,
        frame_pts: bool | None = None,
        atomic_writing: bool | None = None,
        protocol_opts: bool | None = None,
        movflags: bool | None = None,
        moov_size: bool | None = None,
        rtpflags: bool | None = None,
        skip_iods: bool | None = None,
        frag_duration: bool | None = None,
        frag_size: bool | None = None,
        ism_lookahead: bool | None = None,
        brand: bool | None = None,
        use_editlist: bool | None = None,
        fragment_index: bool | None = None,
        mov_gamma: bool | None = None,
        frag_interleave: bool | None = None,
        encryption_key: bool | None = None,
        encryption_kid: bool | None = None,
        write_tmcd: bool | None = None,
        write_prft: bool | None = None,
        empty_hdlr_name: bool | None = None,
    ) -> str:
        """HDS muxer AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if window_size is not None:
            if window_size:
                cmd_args.append("-window_size")
        if remove_at_exit is not None:
            if remove_at_exit:
                cmd_args.append("-remove_at_exit")
        if start_number is not None:
            if start_number:
                cmd_args.append("-start_number")
        if hls_time is not None:
            if hls_time:
                cmd_args.append("-hls_time")
        if hls_init_time is not None:
            if hls_init_time:
                cmd_args.append("-hls_init_time")
        if hls_list_size is not None:
            if hls_list_size:
                cmd_args.append("-hls_list_size")
        if hls_ts_options is not None:
            if hls_ts_options:
                cmd_args.append("-hls_ts_options")
        if hls_vtt_options is not None:
            if hls_vtt_options:
                cmd_args.append("-hls_vtt_options")
        if hls_wrap is not None:
            if hls_wrap:
                cmd_args.append("-hls_wrap")
        if hls_allow_cache is not None:
            if hls_allow_cache:
                cmd_args.append("-hls_allow_cache")
        if hls_base_url is not None:
            if hls_base_url:
                cmd_args.append("-hls_base_url")
        if hls_segment_size is not None:
            if hls_segment_size:
                cmd_args.append("-hls_segment_size")
        if hls_enc is not None:
            if hls_enc:
                cmd_args.append("-hls_enc")
        if hls_enc_key is not None:
            if hls_enc_key:
                cmd_args.append("-hls_enc_key")
        if hls_enc_key_url is not None:
            if hls_enc_key_url:
                cmd_args.append("-hls_enc_key_url")
        if hls_enc_iv is not None:
            if hls_enc_iv:
                cmd_args.append("-hls_enc_iv")
        if hls_segment_type is not None:
            if hls_segment_type:
                cmd_args.append("-hls_segment_type")
        if hls_flags is not None:
            if hls_flags:
                cmd_args.append("-hls_flags")
        if use_localtime is not None:
            if use_localtime:
                cmd_args.append("-use_localtime")
        if strftime is not None:
            if strftime:
                cmd_args.append("-strftime")
        if strftime_mkdir is not None:
            if strftime_mkdir:
                cmd_args.append("-strftime_mkdir")
        if method is not None:
            if method:
                cmd_args.append("-method")
        if http_user_agent is not None:
            if http_user_agent:
                cmd_args.append("-http_user_agent")
        if var_stream_map is not None:
            if var_stream_map:
                cmd_args.append("-var_stream_map")
        if cc_stream_map is not None:
            if cc_stream_map:
                cmd_args.append("-cc_stream_map")
        if master_pl_name is not None:
            if master_pl_name:
                cmd_args.append("-master_pl_name")
        if http_persistent is not None:
            if http_persistent:
                cmd_args.append("-http_persistent")
        if timeout is not None:
            if timeout:
                cmd_args.append("-timeout")
        if ignore_io_errors is not None:
            if ignore_io_errors:
                cmd_args.append("-ignore_io_errors")
        if headers is not None:
            if headers:
                cmd_args.append("-headers")
        if update is not None:
            if update:
                cmd_args.append("-update")
        if frame_pts is not None:
            if frame_pts:
                cmd_args.append("-frame_pts")
        if atomic_writing is not None:
            if atomic_writing:
                cmd_args.append("-atomic_writing")
        if protocol_opts is not None:
            if protocol_opts:
                cmd_args.append("-protocol_opts")
        if movflags is not None:
            if movflags:
                cmd_args.append("-movflags")
        if moov_size is not None:
            if moov_size:
                cmd_args.append("-moov_size")
        if rtpflags is not None:
            if rtpflags:
                cmd_args.append("-rtpflags")
        if skip_iods is not None:
            if skip_iods:
                cmd_args.append("-skip_iods")
        if frag_duration is not None:
            if frag_duration:
                cmd_args.append("-frag_duration")
        if frag_size is not None:
            if frag_size:
                cmd_args.append("-frag_size")
        if ism_lookahead is not None:
            if ism_lookahead:
                cmd_args.append("-ism_lookahead")
        if brand is not None:
            if brand:
                cmd_args.append("-brand")
        if use_editlist is not None:
            if use_editlist:
                cmd_args.append("-use_editlist")
        if fragment_index is not None:
            if fragment_index:
                cmd_args.append("-fragment_index")
        if mov_gamma is not None:
            if mov_gamma:
                cmd_args.append("-mov_gamma")
        if frag_interleave is not None:
            if frag_interleave:
                cmd_args.append("-frag_interleave")
        if encryption_key is not None:
            if encryption_key:
                cmd_args.append("-encryption_key")
        if encryption_kid is not None:
            if encryption_kid:
                cmd_args.append("-encryption_kid")
        if write_tmcd is not None:
            if write_tmcd:
                cmd_args.append("-write_tmcd")
        if write_prft is not None:
            if write_prft:
                cmd_args.append("-write_prft")
        if empty_hdlr_name is not None:
            if empty_hdlr_name:
                cmd_args.append("-empty_hdlr_name")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_latm_loas_muxer_avoptions(
        hash: bool | None = None,
        dash: bool | None = None,
        live: bool | None = None,
        allow_raw_vfw: bool | None = None,
        flipped_raw_rgb: bool | None = None,
        write_crc32: bool | None = None,
        default_mode: bool | None = None,
        movflags: bool | None = None,
        moov_size: bool | None = None,
        rtpflags: bool | None = None,
        skip_iods: bool | None = None,
        frag_duration: bool | None = None,
        frag_size: bool | None = None,
        ism_lookahead: bool | None = None,
        brand: bool | None = None,
        use_editlist: bool | None = None,
        fragment_index: bool | None = None,
        mov_gamma: bool | None = None,
        frag_interleave: bool | None = None,
        encryption_key: bool | None = None,
        encryption_kid: bool | None = None,
        write_tmcd: bool | None = None,
        write_prft: bool | None = None,
        empty_hdlr_name: bool | None = None,
        id3v2_version: bool | None = None,
        write_id3v1: bool | None = None,
        write_xing: bool | None = None,
        muxrate: bool | None = None,
        preload: bool | None = None,
    ) -> str:
        """LATM/LOAS muxer AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if hash is not None:
            if hash:
                cmd_args.append("-hash")
        if dash is not None:
            if dash:
                cmd_args.append("-dash")
        if live is not None:
            if live:
                cmd_args.append("-live")
        if allow_raw_vfw is not None:
            if allow_raw_vfw:
                cmd_args.append("-allow_raw_vfw")
        if flipped_raw_rgb is not None:
            if flipped_raw_rgb:
                cmd_args.append("-flipped_raw_rgb")
        if write_crc32 is not None:
            if write_crc32:
                cmd_args.append("-write_crc32")
        if default_mode is not None:
            if default_mode:
                cmd_args.append("-default_mode")
        if movflags is not None:
            if movflags:
                cmd_args.append("-movflags")
        if moov_size is not None:
            if moov_size:
                cmd_args.append("-moov_size")
        if rtpflags is not None:
            if rtpflags:
                cmd_args.append("-rtpflags")
        if skip_iods is not None:
            if skip_iods:
                cmd_args.append("-skip_iods")
        if frag_duration is not None:
            if frag_duration:
                cmd_args.append("-frag_duration")
        if frag_size is not None:
            if frag_size:
                cmd_args.append("-frag_size")
        if ism_lookahead is not None:
            if ism_lookahead:
                cmd_args.append("-ism_lookahead")
        if brand is not None:
            if brand:
                cmd_args.append("-brand")
        if use_editlist is not None:
            if use_editlist:
                cmd_args.append("-use_editlist")
        if fragment_index is not None:
            if fragment_index:
                cmd_args.append("-fragment_index")
        if mov_gamma is not None:
            if mov_gamma:
                cmd_args.append("-mov_gamma")
        if frag_interleave is not None:
            if frag_interleave:
                cmd_args.append("-frag_interleave")
        if encryption_key is not None:
            if encryption_key:
                cmd_args.append("-encryption_key")
        if encryption_kid is not None:
            if encryption_kid:
                cmd_args.append("-encryption_kid")
        if write_tmcd is not None:
            if write_tmcd:
                cmd_args.append("-write_tmcd")
        if write_prft is not None:
            if write_prft:
                cmd_args.append("-write_prft")
        if empty_hdlr_name is not None:
            if empty_hdlr_name:
                cmd_args.append("-empty_hdlr_name")
        if id3v2_version is not None:
            if id3v2_version:
                cmd_args.append("-id3v2_version")
        if write_id3v1 is not None:
            if write_id3v1:
                cmd_args.append("-write_id3v1")
        if write_xing is not None:
            if write_xing:
                cmd_args.append("-write_xing")
        if muxrate is not None:
            if muxrate:
                cmd_args.append("-muxrate")
        if preload is not None:
            if preload:
                cmd_args.append("-preload")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_mpegts_muxer_avoptions(
        mpegts_start_pid: bool | None = None,
        mpegts_m2ts_mode: bool | None = None,
        muxrate: bool | None = None,
        pes_payload_size: bool | None = None,
        mpegts_flags: bool | None = None,
        mpegts_copyts: bool | None = None,
        tables_version: bool | None = None,
        pcr_period: bool | None = None,
        pat_period: bool | None = None,
        sdt_period: bool | None = None,
        boundary_tag: bool | None = None,
    ) -> str:
        """MPEGTS muxer AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if mpegts_start_pid is not None:
            if mpegts_start_pid:
                cmd_args.append("-mpegts_start_pid")
        if mpegts_m2ts_mode is not None:
            if mpegts_m2ts_mode:
                cmd_args.append("-mpegts_m2ts_mode")
        if muxrate is not None:
            if muxrate:
                cmd_args.append("-muxrate")
        if pes_payload_size is not None:
            if pes_payload_size:
                cmd_args.append("-pes_payload_size")
        if mpegts_flags is not None:
            if mpegts_flags:
                cmd_args.append("-mpegts_flags")
        if mpegts_copyts is not None:
            if mpegts_copyts:
                cmd_args.append("-mpegts_copyts")
        if tables_version is not None:
            if tables_version:
                cmd_args.append("-tables_version")
        if pcr_period is not None:
            if pcr_period:
                cmd_args.append("-pcr_period")
        if pat_period is not None:
            if pat_period:
                cmd_args.append("-pat_period")
        if sdt_period is not None:
            if sdt_period:
                cmd_args.append("-sdt_period")
        if boundary_tag is not None:
            if boundary_tag:
                cmd_args.append("-boundary_tag")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_mxf_muxer_avoptions(
        signal_standard: bool | None = None,
        d10_channelcount: bool | None = None,
    ) -> str:
        """MXF muxer AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if signal_standard is not None:
            if signal_standard:
                cmd_args.append("-signal_standard")
        if d10_channelcount is not None:
            if d10_channelcount:
                cmd_args.append("-d10_channelcount")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_mxf_opatom_muxer_avoptions(
        signal_standard: bool | None = None,
        syncpoints: bool | None = None,
        write_index: bool | None = None,
    ) -> str:
        """MXF-OPAtom muxer AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if signal_standard is not None:
            if signal_standard:
                cmd_args.append("-signal_standard")
        if syncpoints is not None:
            if syncpoints:
                cmd_args.append("-syncpoints")
        if write_index is not None:
            if write_index:
                cmd_args.append("-write_index")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_ogg_audio_muxer_avoptions(
        serial_offset: bool | None = None,
        oggpagesize: bool | None = None,
        pagesize: bool | None = None,
        page_duration: bool | None = None,
    ) -> str:
        """Ogg audio muxer AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if serial_offset is not None:
            if serial_offset:
                cmd_args.append("-serial_offset")
        if oggpagesize is not None:
            if oggpagesize:
                cmd_args.append("-oggpagesize")
        if pagesize is not None:
            if pagesize:
                cmd_args.append("-pagesize")
        if page_duration is not None:
            if page_duration:
                cmd_args.append("-page_duration")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_ogg_muxer_avoptions(
        serial_offset: bool | None = None,
        oggpagesize: bool | None = None,
        pagesize: bool | None = None,
        page_duration: bool | None = None,
    ) -> str:
        """Ogg muxer AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if serial_offset is not None:
            if serial_offset:
                cmd_args.append("-serial_offset")
        if oggpagesize is not None:
            if oggpagesize:
                cmd_args.append("-oggpagesize")
        if pagesize is not None:
            if pagesize:
                cmd_args.append("-pagesize")
        if page_duration is not None:
            if page_duration:
                cmd_args.append("-page_duration")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_ogg_video_muxer_avoptions(
        serial_offset: bool | None = None,
        oggpagesize: bool | None = None,
        pagesize: bool | None = None,
        page_duration: bool | None = None,
    ) -> str:
        """Ogg video muxer AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if serial_offset is not None:
            if serial_offset:
                cmd_args.append("-serial_offset")
        if oggpagesize is not None:
            if oggpagesize:
                cmd_args.append("-oggpagesize")
        if pagesize is not None:
            if pagesize:
                cmd_args.append("-pagesize")
        if page_duration is not None:
            if page_duration:
                cmd_args.append("-page_duration")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_ogg_opus_muxer_avoptions(
        serial_offset: bool | None = None,
        oggpagesize: bool | None = None,
        pagesize: bool | None = None,
        page_duration: bool | None = None,
        movflags: bool | None = None,
        moov_size: bool | None = None,
        rtpflags: bool | None = None,
        skip_iods: bool | None = None,
        frag_duration: bool | None = None,
        frag_size: bool | None = None,
        ism_lookahead: bool | None = None,
        brand: bool | None = None,
        use_editlist: bool | None = None,
        fragment_index: bool | None = None,
        mov_gamma: bool | None = None,
        frag_interleave: bool | None = None,
        encryption_key: bool | None = None,
        encryption_kid: bool | None = None,
        write_tmcd: bool | None = None,
        write_prft: bool | None = None,
        empty_hdlr_name: bool | None = None,
    ) -> str:
        """Ogg Opus muxer AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if serial_offset is not None:
            if serial_offset:
                cmd_args.append("-serial_offset")
        if oggpagesize is not None:
            if oggpagesize:
                cmd_args.append("-oggpagesize")
        if pagesize is not None:
            if pagesize:
                cmd_args.append("-pagesize")
        if page_duration is not None:
            if page_duration:
                cmd_args.append("-page_duration")
        if movflags is not None:
            if movflags:
                cmd_args.append("-movflags")
        if moov_size is not None:
            if moov_size:
                cmd_args.append("-moov_size")
        if rtpflags is not None:
            if rtpflags:
                cmd_args.append("-rtpflags")
        if skip_iods is not None:
            if skip_iods:
                cmd_args.append("-skip_iods")
        if frag_duration is not None:
            if frag_duration:
                cmd_args.append("-frag_duration")
        if frag_size is not None:
            if frag_size:
                cmd_args.append("-frag_size")
        if ism_lookahead is not None:
            if ism_lookahead:
                cmd_args.append("-ism_lookahead")
        if brand is not None:
            if brand:
                cmd_args.append("-brand")
        if use_editlist is not None:
            if use_editlist:
                cmd_args.append("-use_editlist")
        if fragment_index is not None:
            if fragment_index:
                cmd_args.append("-fragment_index")
        if mov_gamma is not None:
            if mov_gamma:
                cmd_args.append("-mov_gamma")
        if frag_interleave is not None:
            if frag_interleave:
                cmd_args.append("-frag_interleave")
        if encryption_key is not None:
            if encryption_key:
                cmd_args.append("-encryption_key")
        if encryption_kid is not None:
            if encryption_kid:
                cmd_args.append("-encryption_kid")
        if write_tmcd is not None:
            if write_tmcd:
                cmd_args.append("-write_tmcd")
        if write_prft is not None:
            if write_prft:
                cmd_args.append("-write_prft")
        if empty_hdlr_name is not None:
            if empty_hdlr_name:
                cmd_args.append("-empty_hdlr_name")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_rtp_muxer_avoptions(
        rtpflags: bool | None = None,
        payload_type: bool | None = None,
        ssrc: bool | None = None,
        cname: bool | None = None,
        seq: bool | None = None,
    ) -> str:
        """RTP muxer AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if rtpflags is not None:
            if rtpflags:
                cmd_args.append("-rtpflags")
        if payload_type is not None:
            if payload_type:
                cmd_args.append("-payload_type")
        if ssrc is not None:
            if ssrc:
                cmd_args.append("-ssrc")
        if cname is not None:
            if cname:
                cmd_args.append("-cname")
        if seq is not None:
            if seq:
                cmd_args.append("-seq")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_rtsp_muxer_avoptions(
        initial_pause: bool | None = None,
        rtpflags: bool | None = None,
        rtsp_transport: bool | None = None,
        rtsp_flags: bool | None = None,
        min_port: bool | None = None,
        max_port: bool | None = None,
        listen_timeout: bool | None = None,
        timeout: bool | None = None,
        stimeout: bool | None = None,
        buffer_size: bool | None = None,
        pkt_size: bool | None = None,
        user_agent: bool | None = None,
        reference_stream: bool | None = None,
        segment_format: bool | None = None,
        segment_list: bool | None = None,
        segment_time: bool | None = None,
        segment_times: bool | None = None,
        segment_frames: bool | None = None,
        segment_wrap: bool | None = None,
        strftime: bool | None = None,
        increment_tc: bool | None = None,
        reset_timestamps: bool | None = None,
        initial_offset: bool | None = None,
        window_size: bool | None = None,
        lookahead_count: bool | None = None,
        remove_at_exit: bool | None = None,
    ) -> str:
        """RTSP muxer AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if initial_pause is not None:
            if initial_pause:
                cmd_args.append("-initial_pause")
        if rtpflags is not None:
            if rtpflags:
                cmd_args.append("-rtpflags")
        if rtsp_transport is not None:
            if rtsp_transport:
                cmd_args.append("-rtsp_transport")
        if rtsp_flags is not None:
            if rtsp_flags:
                cmd_args.append("-rtsp_flags")
        if min_port is not None:
            if min_port:
                cmd_args.append("-min_port")
        if max_port is not None:
            if max_port:
                cmd_args.append("-max_port")
        if listen_timeout is not None:
            if listen_timeout:
                cmd_args.append("-listen_timeout")
        if timeout is not None:
            if timeout:
                cmd_args.append("-timeout")
        if stimeout is not None:
            if stimeout:
                cmd_args.append("-stimeout")
        if buffer_size is not None:
            if buffer_size:
                cmd_args.append("-buffer_size")
        if pkt_size is not None:
            if pkt_size:
                cmd_args.append("-pkt_size")
        if user_agent is not None:
            if user_agent:
                cmd_args.append("-user_agent")
        if reference_stream is not None:
            if reference_stream:
                cmd_args.append("-reference_stream")
        if segment_format is not None:
            if segment_format:
                cmd_args.append("-segment_format")
        if segment_list is not None:
            if segment_list:
                cmd_args.append("-segment_list")
        if segment_time is not None:
            if segment_time:
                cmd_args.append("-segment_time")
        if segment_times is not None:
            if segment_times:
                cmd_args.append("-segment_times")
        if segment_frames is not None:
            if segment_frames:
                cmd_args.append("-segment_frames")
        if segment_wrap is not None:
            if segment_wrap:
                cmd_args.append("-segment_wrap")
        if strftime is not None:
            if strftime:
                cmd_args.append("-strftime")
        if increment_tc is not None:
            if increment_tc:
                cmd_args.append("-increment_tc")
        if reset_timestamps is not None:
            if reset_timestamps:
                cmd_args.append("-reset_timestamps")
        if initial_offset is not None:
            if initial_offset:
                cmd_args.append("-initial_offset")
        if window_size is not None:
            if window_size:
                cmd_args.append("-window_size")
        if lookahead_count is not None:
            if lookahead_count:
                cmd_args.append("-lookahead_count")
        if remove_at_exit is not None:
            if remove_at_exit:
                cmd_args.append("-remove_at_exit")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_ogg_speex_muxer_avoptions(
        serial_offset: bool | None = None,
        oggpagesize: bool | None = None,
        pagesize: bool | None = None,
        page_duration: bool | None = None,
        spdif_flags: bool | None = None,
        dtshd_rate: bool | None = None,
        hash: bool | None = None,
    ) -> str:
        """Ogg Speex muxer AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if serial_offset is not None:
            if serial_offset:
                cmd_args.append("-serial_offset")
        if oggpagesize is not None:
            if oggpagesize:
                cmd_args.append("-oggpagesize")
        if pagesize is not None:
            if pagesize:
                cmd_args.append("-pagesize")
        if page_duration is not None:
            if page_duration:
                cmd_args.append("-page_duration")
        if spdif_flags is not None:
            if spdif_flags:
                cmd_args.append("-spdif_flags")
        if dtshd_rate is not None:
            if dtshd_rate:
                cmd_args.append("-dtshd_rate")
        if hash is not None:
            if hash:
                cmd_args.append("-hash")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_tee_muxer_avoptions(
        use_fifo: bool | None = None,
        fifo_options: bool | None = None,
        movflags: bool | None = None,
        moov_size: bool | None = None,
        rtpflags: bool | None = None,
        skip_iods: bool | None = None,
        frag_duration: bool | None = None,
        frag_size: bool | None = None,
        ism_lookahead: bool | None = None,
        brand: bool | None = None,
        use_editlist: bool | None = None,
        fragment_index: bool | None = None,
        mov_gamma: bool | None = None,
        frag_interleave: bool | None = None,
        encryption_key: bool | None = None,
        encryption_kid: bool | None = None,
        write_tmcd: bool | None = None,
        write_prft: bool | None = None,
        empty_hdlr_name: bool | None = None,
    ) -> str:
        """Tee muxer AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if use_fifo is not None:
            if use_fifo:
                cmd_args.append("-use_fifo")
        if fifo_options is not None:
            if fifo_options:
                cmd_args.append("-fifo_options")
        if movflags is not None:
            if movflags:
                cmd_args.append("-movflags")
        if moov_size is not None:
            if moov_size:
                cmd_args.append("-moov_size")
        if rtpflags is not None:
            if rtpflags:
                cmd_args.append("-rtpflags")
        if skip_iods is not None:
            if skip_iods:
                cmd_args.append("-skip_iods")
        if frag_duration is not None:
            if frag_duration:
                cmd_args.append("-frag_duration")
        if frag_size is not None:
            if frag_size:
                cmd_args.append("-frag_size")
        if ism_lookahead is not None:
            if ism_lookahead:
                cmd_args.append("-ism_lookahead")
        if brand is not None:
            if brand:
                cmd_args.append("-brand")
        if use_editlist is not None:
            if use_editlist:
                cmd_args.append("-use_editlist")
        if fragment_index is not None:
            if fragment_index:
                cmd_args.append("-fragment_index")
        if mov_gamma is not None:
            if mov_gamma:
                cmd_args.append("-mov_gamma")
        if frag_interleave is not None:
            if frag_interleave:
                cmd_args.append("-frag_interleave")
        if encryption_key is not None:
            if encryption_key:
                cmd_args.append("-encryption_key")
        if encryption_kid is not None:
            if encryption_kid:
                cmd_args.append("-encryption_kid")
        if write_tmcd is not None:
            if write_tmcd:
                cmd_args.append("-write_tmcd")
        if write_prft is not None:
            if write_prft:
                cmd_args.append("-write_prft")
        if empty_hdlr_name is not None:
            if empty_hdlr_name:
                cmd_args.append("-empty_hdlr_name")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_wav_muxer_avoptions(
        write_bext: bool | None = None,
        write_peak: bool | None = None,
        rf64: bool | None = None,
        peak_block_size: bool | None = None,
        peak_format: bool | None = None,
        peak_ppv: bool | None = None,
        dash: bool | None = None,
        live: bool | None = None,
        allow_raw_vfw: bool | None = None,
        flipped_raw_rgb: bool | None = None,
        write_crc32: bool | None = None,
        default_mode: bool | None = None,
    ) -> str:
        """WAV muxer AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if write_bext is not None:
            if write_bext:
                cmd_args.append("-write_bext")
        if write_peak is not None:
            if write_peak:
                cmd_args.append("-write_peak")
        if rf64 is not None:
            if rf64:
                cmd_args.append("-rf64")
        if peak_block_size is not None:
            if peak_block_size:
                cmd_args.append("-peak_block_size")
        if peak_format is not None:
            if peak_format:
                cmd_args.append("-peak_format")
        if peak_ppv is not None:
            if peak_ppv:
                cmd_args.append("-peak_ppv")
        if dash is not None:
            if dash:
                cmd_args.append("-dash")
        if live is not None:
            if live:
                cmd_args.append("-live")
        if allow_raw_vfw is not None:
            if allow_raw_vfw:
                cmd_args.append("-allow_raw_vfw")
        if flipped_raw_rgb is not None:
            if flipped_raw_rgb:
                cmd_args.append("-flipped_raw_rgb")
        if write_crc32 is not None:
            if write_crc32:
                cmd_args.append("-write_crc32")
        if default_mode is not None:
            if default_mode:
                cmd_args.append("-default_mode")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_webm_dash_manifest_muxer_avoptions(
        adaptation_sets: bool | None = None,
        live: bool | None = None,
        utc_timing_url: bool | None = None,
    ) -> str:
        """WebM DASH Manifest muxer AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if adaptation_sets is not None:
            if adaptation_sets:
                cmd_args.append("-adaptation_sets")
        if live is not None:
            if live:
                cmd_args.append("-live")
        if utc_timing_url is not None:
            if utc_timing_url:
                cmd_args.append("-utc_timing_url")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_webm_chunk_muxer_avoptions(
        header: bool | None = None,
        method: bool | None = None,
    ) -> str:
        """WebM Chunk Muxer AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if header is not None:
            if header:
                cmd_args.append("-header")
        if method is not None:
            if method:
                cmd_args.append("-method")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_webp_muxer_avoptions(
        loop: bool | None = None,
        algorithm: bool | None = None,
        fp_format: bool | None = None,
        window_size: bool | None = None,
        window_title: bool | None = None,
        driver: bool | None = None,
        antialias: bool | None = None,
        charset: bool | None = None,
        color: bool | None = None,
        list_drivers: bool | None = None,
        list_dither: bool | None = None,
        xoffset: bool | None = None,
        yoffset: bool | None = None,
        background: bool | None = None,
        no_window: bool | None = None,
    ) -> str:
        """WebP muxer AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if loop is not None:
            if loop:
                cmd_args.append("-loop")
        if algorithm is not None:
            if algorithm:
                cmd_args.append("-algorithm")
        if fp_format is not None:
            if fp_format:
                cmd_args.append("-fp_format")
        if window_size is not None:
            if window_size:
                cmd_args.append("-window_size")
        if window_title is not None:
            if window_title:
                cmd_args.append("-window_title")
        if driver is not None:
            if driver:
                cmd_args.append("-driver")
        if antialias is not None:
            if antialias:
                cmd_args.append("-antialias")
        if charset is not None:
            if charset:
                cmd_args.append("-charset")
        if color is not None:
            if color:
                cmd_args.append("-color")
        if list_drivers is not None:
            if list_drivers:
                cmd_args.append("-list_drivers")
        if list_dither is not None:
            if list_dither:
                cmd_args.append("-list_dither")
        if xoffset is not None:
            if xoffset:
                cmd_args.append("-xoffset")
        if yoffset is not None:
            if yoffset:
                cmd_args.append("-yoffset")
        if background is not None:
            if background:
                cmd_args.append("-background")
        if no_window is not None:
            if no_window:
                cmd_args.append("-no_window")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_pulseaudio_outdev_avoptions(
        server: bool | None = None,
        name: bool | None = None,
        stream_name: bool | None = None,
        device: bool | None = None,
        buffer_size: bool | None = None,
        buffer_duration: bool | None = None,
        prebuf: bool | None = None,
        minreq: bool | None = None,
        window_title: bool | None = None,
        window_size: bool | None = None,
        window_x: bool | None = None,
        window_y: bool | None = None,
        display_name: bool | None = None,
        window_id: bool | None = None,
        aa_fixed_key: bool | None = None,
        raw_packet_size: bool | None = None,
    ) -> str:
        """PulseAudio outdev AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if server is not None:
            if server:
                cmd_args.append("-server")
        if name is not None:
            if name:
                cmd_args.append("-name")
        if stream_name is not None:
            if stream_name:
                cmd_args.append("-stream_name")
        if device is not None:
            if device:
                cmd_args.append("-device")
        if buffer_size is not None:
            if buffer_size:
                cmd_args.append("-buffer_size")
        if buffer_duration is not None:
            if buffer_duration:
                cmd_args.append("-buffer_duration")
        if prebuf is not None:
            if prebuf:
                cmd_args.append("-prebuf")
        if minreq is not None:
            if minreq:
                cmd_args.append("-minreq")
        if window_title is not None:
            if window_title:
                cmd_args.append("-window_title")
        if window_size is not None:
            if window_size:
                cmd_args.append("-window_size")
        if window_x is not None:
            if window_x:
                cmd_args.append("-window_x")
        if window_y is not None:
            if window_y:
                cmd_args.append("-window_y")
        if display_name is not None:
            if display_name:
                cmd_args.append("-display_name")
        if window_id is not None:
            if window_id:
                cmd_args.append("-window_id")
        if aa_fixed_key is not None:
            if aa_fixed_key:
                cmd_args.append("-aa_fixed_key")
        if raw_packet_size is not None:
            if raw_packet_size:
                cmd_args.append("-raw_packet_size")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_artworx_data_format_demuxer_avoptions(
        linespeed: bool | None = None,
        video_size: bool | None = None,
        framerate: bool | None = None,
    ) -> str:
        """Artworx Data Format demuxer AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if linespeed is not None:
            if linespeed:
                cmd_args.append("-linespeed")
        if video_size is not None:
            if video_size:
                cmd_args.append("-video_size")
        if framerate is not None:
            if framerate:
                cmd_args.append("-framerate")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_apng_demuxer_avoptions(
        ignore_loop: bool | None = None,
        max_fps: bool | None = None,
        default_fps: bool | None = None,
        sample_rate: bool | None = None,
        subfps: bool | None = None,
        no_resync_search: bool | None = None,
        export_xmp: bool | None = None,
        framerate: bool | None = None,
        use_odml: bool | None = None,
        raw_packet_size: bool | None = None,
    ) -> str:
        """APNG demuxer AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if ignore_loop is not None:
            if ignore_loop:
                cmd_args.append("-ignore_loop")
        if max_fps is not None:
            if max_fps:
                cmd_args.append("-max_fps")
        if default_fps is not None:
            if default_fps:
                cmd_args.append("-default_fps")
        if sample_rate is not None:
            if sample_rate:
                cmd_args.append("-sample_rate")
        if subfps is not None:
            if subfps:
                cmd_args.append("-subfps")
        if no_resync_search is not None:
            if no_resync_search:
                cmd_args.append("-no_resync_search")
        if export_xmp is not None:
            if export_xmp:
                cmd_args.append("-export_xmp")
        if framerate is not None:
            if framerate:
                cmd_args.append("-framerate")
        if use_odml is not None:
            if use_odml:
                cmd_args.append("-use_odml")
        if raw_packet_size is not None:
            if raw_packet_size:
                cmd_args.append("-raw_packet_size")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_binary_text_demuxer_avoptions(
        linespeed: bool | None = None,
        video_size: bool | None = None,
        framerate: bool | None = None,
        raw_packet_size: bool | None = None,
    ) -> str:
        """Binary text demuxer AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if linespeed is not None:
            if linespeed:
                cmd_args.append("-linespeed")
        if video_size is not None:
            if video_size:
                cmd_args.append("-video_size")
        if framerate is not None:
            if framerate:
                cmd_args.append("-framerate")
        if raw_packet_size is not None:
            if raw_packet_size:
                cmd_args.append("-raw_packet_size")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_cdxl_demuxer_avoptions(
        sample_rate: bool | None = None,
        frame_rate: bool | None = None,
        mode: bool | None = None,
        safe: bool | None = None,
        auto_convert: bool | None = None,
        raw_packet_size: bool | None = None,
        framerate: bool | None = None,
    ) -> str:
        """CDXL demuxer AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if sample_rate is not None:
            if sample_rate:
                cmd_args.append("-sample_rate")
        if frame_rate is not None:
            if frame_rate:
                cmd_args.append("-frame_rate")
        if mode is not None:
            if mode:
                cmd_args.append("-mode")
        if safe is not None:
            if safe:
                cmd_args.append("-safe")
        if auto_convert is not None:
            if auto_convert:
                cmd_args.append("-auto_convert")
        if raw_packet_size is not None:
            if raw_packet_size:
                cmd_args.append("-raw_packet_size")
        if framerate is not None:
            if framerate:
                cmd_args.append("-framerate")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_fits_demuxer_avoptions(
        framerate: bool | None = None,
        raw_packet_size: bool | None = None,
        flv_metadata: bool | None = None,
        missing_streams: bool | None = None,
        code_size: bool | None = None,
        sample_rate: bool | None = None,
        bit_rate: bool | None = None,
    ) -> str:
        """FITS demuxer AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if framerate is not None:
            if framerate:
                cmd_args.append("-framerate")
        if raw_packet_size is not None:
            if raw_packet_size:
                cmd_args.append("-raw_packet_size")
        if flv_metadata is not None:
            if flv_metadata:
                cmd_args.append("-flv_metadata")
        if missing_streams is not None:
            if missing_streams:
                cmd_args.append("-missing_streams")
        if code_size is not None:
            if code_size:
                cmd_args.append("-code_size")
        if sample_rate is not None:
            if sample_rate:
                cmd_args.append("-sample_rate")
        if bit_rate is not None:
            if bit_rate:
                cmd_args.append("-bit_rate")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_gif_demuxer_avoptions(
        min_delay: bool | None = None,
        max_gif_delay: bool | None = None,
        default_delay: bool | None = None,
        ignore_loop: bool | None = None,
        sample_rate: bool | None = None,
        framerate: bool | None = None,
        raw_packet_size: bool | None = None,
        live_start_index: bool | None = None,
        max_reload: bool | None = None,
        http_persistent: bool | None = None,
        http_multiple: bool | None = None,
        http_seekable: bool | None = None,
        linespeed: bool | None = None,
        video_size: bool | None = None,
        pattern_type: bool | None = None,
        start_number: bool | None = None,
        ts_from_file: bool | None = None,
        pixel_format: bool | None = None,
        loop: bool | None = None,
        frame_size: bool | None = None,
        flv_metadata: bool | None = None,
        missing_streams: bool | None = None,
        subfps: bool | None = None,
        ignore_editlist: bool | None = None,
        ignore_chapters: bool | None = None,
        use_mfra_for: bool | None = None,
        export_all: bool | None = None,
        export_xmp: bool | None = None,
        activation_bytes: bool | None = None,
        audible_key: bool | None = None,
        audible_iv: bool | None = None,
        decryption_key: bool | None = None,
        enable_drefs: bool | None = None,
        usetoc: bool | None = None,
        resync_size: bool | None = None,
        fix_teletext_pts: bool | None = None,
        ts_packetsize: bool | None = None,
        scan_all_pmts: bool | None = None,
        skip_unknown_pmt: bool | None = None,
        compute_pcr: bool | None = None,
    ) -> str:
        """GIF demuxer AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if min_delay is not None:
            if min_delay:
                cmd_args.append("-min_delay")
        if max_gif_delay is not None:
            if max_gif_delay:
                cmd_args.append("-max_gif_delay")
        if default_delay is not None:
            if default_delay:
                cmd_args.append("-default_delay")
        if ignore_loop is not None:
            if ignore_loop:
                cmd_args.append("-ignore_loop")
        if sample_rate is not None:
            if sample_rate:
                cmd_args.append("-sample_rate")
        if framerate is not None:
            if framerate:
                cmd_args.append("-framerate")
        if raw_packet_size is not None:
            if raw_packet_size:
                cmd_args.append("-raw_packet_size")
        if live_start_index is not None:
            if live_start_index:
                cmd_args.append("-live_start_index")
        if max_reload is not None:
            if max_reload:
                cmd_args.append("-max_reload")
        if http_persistent is not None:
            if http_persistent:
                cmd_args.append("-http_persistent")
        if http_multiple is not None:
            if http_multiple:
                cmd_args.append("-http_multiple")
        if http_seekable is not None:
            if http_seekable:
                cmd_args.append("-http_seekable")
        if linespeed is not None:
            if linespeed:
                cmd_args.append("-linespeed")
        if video_size is not None:
            if video_size:
                cmd_args.append("-video_size")
        if pattern_type is not None:
            if pattern_type:
                cmd_args.append("-pattern_type")
        if start_number is not None:
            if start_number:
                cmd_args.append("-start_number")
        if ts_from_file is not None:
            if ts_from_file:
                cmd_args.append("-ts_from_file")
        if pixel_format is not None:
            if pixel_format:
                cmd_args.append("-pixel_format")
        if loop is not None:
            if loop:
                cmd_args.append("-loop")
        if frame_size is not None:
            if frame_size:
                cmd_args.append("-frame_size")
        if flv_metadata is not None:
            if flv_metadata:
                cmd_args.append("-flv_metadata")
        if missing_streams is not None:
            if missing_streams:
                cmd_args.append("-missing_streams")
        if subfps is not None:
            if subfps:
                cmd_args.append("-subfps")
        if ignore_editlist is not None:
            if ignore_editlist:
                cmd_args.append("-ignore_editlist")
        if ignore_chapters is not None:
            if ignore_chapters:
                cmd_args.append("-ignore_chapters")
        if use_mfra_for is not None:
            if use_mfra_for:
                cmd_args.append("-use_mfra_for")
        if export_all is not None:
            if export_all:
                cmd_args.append("-export_all")
        if export_xmp is not None:
            if export_xmp:
                cmd_args.append("-export_xmp")
        if activation_bytes is not None:
            if activation_bytes:
                cmd_args.append("-activation_bytes")
        if audible_key is not None:
            if audible_key:
                cmd_args.append("-audible_key")
        if audible_iv is not None:
            if audible_iv:
                cmd_args.append("-audible_iv")
        if decryption_key is not None:
            if decryption_key:
                cmd_args.append("-decryption_key")
        if enable_drefs is not None:
            if enable_drefs:
                cmd_args.append("-enable_drefs")
        if usetoc is not None:
            if usetoc:
                cmd_args.append("-usetoc")
        if resync_size is not None:
            if resync_size:
                cmd_args.append("-resync_size")
        if fix_teletext_pts is not None:
            if fix_teletext_pts:
                cmd_args.append("-fix_teletext_pts")
        if ts_packetsize is not None:
            if ts_packetsize:
                cmd_args.append("-ts_packetsize")
        if scan_all_pmts is not None:
            if scan_all_pmts:
                cmd_args.append("-scan_all_pmts")
        if skip_unknown_pmt is not None:
            if skip_unknown_pmt:
                cmd_args.append("-skip_unknown_pmt")
        if compute_pcr is not None:
            if compute_pcr:
                cmd_args.append("-compute_pcr")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_mpjpeg_demuxer_avoptions(
        eia608_extract: bool | None = None,
        framerate: bool | None = None,
        sample_rate: bool | None = None,
        channels: bool | None = None,
        video_size: bool | None = None,
        pixel_format: bool | None = None,
    ) -> str:
        """MPJPEG demuxer AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if eia608_extract is not None:
            if eia608_extract:
                cmd_args.append("-eia608_extract")
        if framerate is not None:
            if framerate:
                cmd_args.append("-framerate")
        if sample_rate is not None:
            if sample_rate:
                cmd_args.append("-sample_rate")
        if channels is not None:
            if channels:
                cmd_args.append("-channels")
        if video_size is not None:
            if video_size:
                cmd_args.append("-video_size")
        if pixel_format is not None:
            if pixel_format:
                cmd_args.append("-pixel_format")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_rtp_demuxer_avoptions(
        rtp_flags: bool | None = None,
        listen_timeout: bool | None = None,
        buffer_size: bool | None = None,
        pkt_size: bool | None = None,
    ) -> str:
        """RTP demuxer AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if rtp_flags is not None:
            if rtp_flags:
                cmd_args.append("-rtp_flags")
        if listen_timeout is not None:
            if listen_timeout:
                cmd_args.append("-listen_timeout")
        if buffer_size is not None:
            if buffer_size:
                cmd_args.append("-buffer_size")
        if pkt_size is not None:
            if pkt_size:
                cmd_args.append("-pkt_size")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_rtsp_demuxer_avoptions(
        initial_pause: bool | None = None,
        rtpflags: bool | None = None,
        rtsp_transport: bool | None = None,
        rtsp_flags: bool | None = None,
        min_port: bool | None = None,
        max_port: bool | None = None,
        listen_timeout: bool | None = None,
        timeout: bool | None = None,
        stimeout: bool | None = None,
        buffer_size: bool | None = None,
        pkt_size: bool | None = None,
        user_agent: bool | None = None,
        raw_packet_size: bool | None = None,
        sample_rate: bool | None = None,
        frame_size: bool | None = None,
        max_file_size: bool | None = None,
    ) -> str:
        """RTSP demuxer AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if initial_pause is not None:
            if initial_pause:
                cmd_args.append("-initial_pause")
        if rtpflags is not None:
            if rtpflags:
                cmd_args.append("-rtpflags")
        if rtsp_transport is not None:
            if rtsp_transport:
                cmd_args.append("-rtsp_transport")
        if rtsp_flags is not None:
            if rtsp_flags:
                cmd_args.append("-rtsp_flags")
        if min_port is not None:
            if min_port:
                cmd_args.append("-min_port")
        if max_port is not None:
            if max_port:
                cmd_args.append("-max_port")
        if listen_timeout is not None:
            if listen_timeout:
                cmd_args.append("-listen_timeout")
        if timeout is not None:
            if timeout:
                cmd_args.append("-timeout")
        if stimeout is not None:
            if stimeout:
                cmd_args.append("-stimeout")
        if buffer_size is not None:
            if buffer_size:
                cmd_args.append("-buffer_size")
        if pkt_size is not None:
            if pkt_size:
                cmd_args.append("-pkt_size")
        if user_agent is not None:
            if user_agent:
                cmd_args.append("-user_agent")
        if raw_packet_size is not None:
            if raw_packet_size:
                cmd_args.append("-raw_packet_size")
        if sample_rate is not None:
            if sample_rate:
                cmd_args.append("-sample_rate")
        if frame_size is not None:
            if frame_size:
                cmd_args.append("-frame_size")
        if max_file_size is not None:
            if max_file_size:
                cmd_args.append("-max_file_size")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_sdp_demuxer_avoptions(
        sdp_flags: bool | None = None,
        listen_timeout: bool | None = None,
        buffer_size: bool | None = None,
        pkt_size: bool | None = None,
        framerate: bool | None = None,
        raw_packet_size: bool | None = None,
        sample_rate: bool | None = None,
        channels: bool | None = None,
        start_time: bool | None = None,
    ) -> str:
        """SDP demuxer AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if sdp_flags is not None:
            if sdp_flags:
                cmd_args.append("-sdp_flags")
        if listen_timeout is not None:
            if listen_timeout:
                cmd_args.append("-listen_timeout")
        if buffer_size is not None:
            if buffer_size:
                cmd_args.append("-buffer_size")
        if pkt_size is not None:
            if pkt_size:
                cmd_args.append("-pkt_size")
        if framerate is not None:
            if framerate:
                cmd_args.append("-framerate")
        if raw_packet_size is not None:
            if raw_packet_size:
                cmd_args.append("-raw_packet_size")
        if sample_rate is not None:
            if sample_rate:
                cmd_args.append("-sample_rate")
        if channels is not None:
            if channels:
                cmd_args.append("-channels")
        if start_time is not None:
            if start_time:
                cmd_args.append("-start_time")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_tty_demuxer_avoptions(
        chars_per_frame: bool | None = None,
        video_size: bool | None = None,
        framerate: bool | None = None,
        raw_packet_size: bool | None = None,
        sub_name: bool | None = None,
        max_size: bool | None = None,
    ) -> str:
        """TTY demuxer AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if chars_per_frame is not None:
            if chars_per_frame:
                cmd_args.append("-chars_per_frame")
        if video_size is not None:
            if video_size:
                cmd_args.append("-video_size")
        if framerate is not None:
            if framerate:
                cmd_args.append("-framerate")
        if raw_packet_size is not None:
            if raw_packet_size:
                cmd_args.append("-raw_packet_size")
        if sub_name is not None:
            if sub_name:
                cmd_args.append("-sub_name")
        if max_size is not None:
            if max_size:
                cmd_args.append("-max_size")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_wav_demuxer_avoptions(
        ignore_length: bool | None = None,
        max_size: bool | None = None,
    ) -> str:
        """WAV demuxer AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if ignore_length is not None:
            if ignore_length:
                cmd_args.append("-ignore_length")
        if max_size is not None:
            if max_size:
                cmd_args.append("-max_size")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_webm_dash_manifest_demuxer_avoptions(
        live: bool | None = None,
        bandwidth: bool | None = None,
    ) -> str:
        """WebM DASH Manifest demuxer AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if live is not None:
            if live:
                cmd_args.append("-live")
        if bandwidth is not None:
            if bandwidth:
                cmd_args.append("-bandwidth")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_webvtt_demuxer_avoptions(
        kind: bool | None = None,
        raw_packet_size: bool | None = None,
        linespeed: bool | None = None,
        video_size: bool | None = None,
        framerate: bool | None = None,
        frame_size: bool | None = None,
        pixel_format: bool | None = None,
        loop: bool | None = None,
    ) -> str:
        """WebVTT demuxer AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if kind is not None:
            if kind:
                cmd_args.append("-kind")
        if raw_packet_size is not None:
            if raw_packet_size:
                cmd_args.append("-raw_packet_size")
        if linespeed is not None:
            if linespeed:
                cmd_args.append("-linespeed")
        if video_size is not None:
            if video_size:
                cmd_args.append("-video_size")
        if framerate is not None:
            if framerate:
                cmd_args.append("-framerate")
        if frame_size is not None:
            if frame_size:
                cmd_args.append("-frame_size")
        if pixel_format is not None:
            if pixel_format:
                cmd_args.append("-pixel_format")
        if loop is not None:
            if loop:
                cmd_args.append("-loop")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_game_music_emu_demuxer_avoptions(
        track_index: bool | None = None,
        sample_rate: bool | None = None,
        max_size: bool | None = None,
        layout: bool | None = None,
        subsong: bool | None = None,
    ) -> str:
        """Game Music Emu demuxer AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if track_index is not None:
            if track_index:
                cmd_args.append("-track_index")
        if sample_rate is not None:
            if sample_rate:
                cmd_args.append("-sample_rate")
        if max_size is not None:
            if max_size:
                cmd_args.append("-max_size")
        if layout is not None:
            if layout:
                cmd_args.append("-layout")
        if subsong is not None:
            if subsong:
                cmd_args.append("-subsong")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_alsa_indev_avoptions(
        sample_rate: bool | None = None,
        channels: bool | None = None,
        framerate: bool | None = None,
        dvtype: bool | None = None,
        dvbuffer: bool | None = None,
        dvguid: bool | None = None,
    ) -> str:
        """ALSA indev AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if sample_rate is not None:
            if sample_rate:
                cmd_args.append("-sample_rate")
        if channels is not None:
            if channels:
                cmd_args.append("-channels")
        if framerate is not None:
            if framerate:
                cmd_args.append("-framerate")
        if dvtype is not None:
            if dvtype:
                cmd_args.append("-dvtype")
        if dvbuffer is not None:
            if dvbuffer:
                cmd_args.append("-dvbuffer")
        if dvguid is not None:
            if dvguid:
                cmd_args.append("-dvguid")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_jack_indev_avoptions(
        channels: bool | None = None,
        device: bool | None = None,
        format: bool | None = None,
        format_modifier: bool | None = None,
        crtc_id: bool | None = None,
        plane_id: bool | None = None,
        framerate: bool | None = None,
        graph: bool | None = None,
        graph_file: bool | None = None,
        dumpgraph: bool | None = None,
        sample_rate: bool | None = None,
        sample_size: bool | None = None,
        list_devices: bool | None = None,
    ) -> str:
        """JACK indev AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if channels is not None:
            if channels:
                cmd_args.append("-channels")
        if device is not None:
            if device:
                cmd_args.append("-device")
        if format is not None:
            if format:
                cmd_args.append("-format")
        if format_modifier is not None:
            if format_modifier:
                cmd_args.append("-format_modifier")
        if crtc_id is not None:
            if crtc_id:
                cmd_args.append("-crtc_id")
        if plane_id is not None:
            if plane_id:
                cmd_args.append("-plane_id")
        if framerate is not None:
            if framerate:
                cmd_args.append("-framerate")
        if graph is not None:
            if graph:
                cmd_args.append("-graph")
        if graph_file is not None:
            if graph_file:
                cmd_args.append("-graph_file")
        if dumpgraph is not None:
            if dumpgraph:
                cmd_args.append("-dumpgraph")
        if sample_rate is not None:
            if sample_rate:
                cmd_args.append("-sample_rate")
        if sample_size is not None:
            if sample_size:
                cmd_args.append("-sample_size")
        if list_devices is not None:
            if list_devices:
                cmd_args.append("-list_devices")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_oss_indev_avoptions(
        sample_rate: bool | None = None,
        channels: bool | None = None,
    ) -> str:
        """OSS indev AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if sample_rate is not None:
            if sample_rate:
                cmd_args.append("-sample_rate")
        if channels is not None:
            if channels:
                cmd_args.append("-channels")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_pulse_indev_avoptions(
        server: bool | None = None,
        name: bool | None = None,
        stream_name: bool | None = None,
        sample_rate: bool | None = None,
        channels: bool | None = None,
        frame_size: bool | None = None,
        fragment_size: bool | None = None,
        wallclock: bool | None = None,
        standard: bool | None = None,
        channel: bool | None = None,
        video_size: bool | None = None,
        pixel_format: bool | None = None,
        input_format: bool | None = None,
        framerate: bool | None = None,
        list_formats: bool | None = None,
        list_standards: bool | None = None,
        timestamps: bool | None = None,
        ts: bool | None = None,
        use_libv4l2: bool | None = None,
        window_id: bool | None = None,
        x: bool | None = None,
        y: bool | None = None,
        grab_x: bool | None = None,
        grab_y: bool | None = None,
        draw_mouse: bool | None = None,
        follow_mouse: bool | None = None,
        show_region: bool | None = None,
        region_border: bool | None = None,
        select_region: bool | None = None,
        speed: bool | None = None,
        paranoia_mode: bool | None = None,
    ) -> str:
        """Pulse indev AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if server is not None:
            if server:
                cmd_args.append("-server")
        if name is not None:
            if name:
                cmd_args.append("-name")
        if stream_name is not None:
            if stream_name:
                cmd_args.append("-stream_name")
        if sample_rate is not None:
            if sample_rate:
                cmd_args.append("-sample_rate")
        if channels is not None:
            if channels:
                cmd_args.append("-channels")
        if frame_size is not None:
            if frame_size:
                cmd_args.append("-frame_size")
        if fragment_size is not None:
            if fragment_size:
                cmd_args.append("-fragment_size")
        if wallclock is not None:
            if wallclock:
                cmd_args.append("-wallclock")
        if standard is not None:
            if standard:
                cmd_args.append("-standard")
        if channel is not None:
            if channel:
                cmd_args.append("-channel")
        if video_size is not None:
            if video_size:
                cmd_args.append("-video_size")
        if pixel_format is not None:
            if pixel_format:
                cmd_args.append("-pixel_format")
        if input_format is not None:
            if input_format:
                cmd_args.append("-input_format")
        if framerate is not None:
            if framerate:
                cmd_args.append("-framerate")
        if list_formats is not None:
            if list_formats:
                cmd_args.append("-list_formats")
        if list_standards is not None:
            if list_standards:
                cmd_args.append("-list_standards")
        if timestamps is not None:
            if timestamps:
                cmd_args.append("-timestamps")
        if ts is not None:
            if ts:
                cmd_args.append("-ts")
        if use_libv4l2 is not None:
            if use_libv4l2:
                cmd_args.append("-use_libv4l2")
        if window_id is not None:
            if window_id:
                cmd_args.append("-window_id")
        if x is not None:
            if x:
                cmd_args.append("-x")
        if y is not None:
            if y:
                cmd_args.append("-y")
        if grab_x is not None:
            if grab_x:
                cmd_args.append("-grab_x")
        if grab_y is not None:
            if grab_y:
                cmd_args.append("-grab_y")
        if draw_mouse is not None:
            if draw_mouse:
                cmd_args.append("-draw_mouse")
        if follow_mouse is not None:
            if follow_mouse:
                cmd_args.append("-follow_mouse")
        if show_region is not None:
            if show_region:
                cmd_args.append("-show_region")
        if region_border is not None:
            if region_border:
                cmd_args.append("-region_border")
        if select_region is not None:
            if select_region:
                cmd_args.append("-select_region")
        if speed is not None:
            if speed:
                cmd_args.append("-speed")
        if paranoia_mode is not None:
            if paranoia_mode:
                cmd_args.append("-paranoia_mode")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_swscaler_avoptions(
        sws_flags: bool | None = None,
        srcw: bool | None = None,
        srch: bool | None = None,
        dstw: bool | None = None,
        dsth: bool | None = None,
        src_format: bool | None = None,
        dst_format: bool | None = None,
        src_range: bool | None = None,
        dst_range: bool | None = None,
        param0: bool | None = None,
        param1: bool | None = None,
        src_v_chr_pos: bool | None = None,
        src_h_chr_pos: bool | None = None,
        dst_v_chr_pos: bool | None = None,
        dst_h_chr_pos: bool | None = None,
        sws_dither: bool | None = None,
        gamma: bool | None = None,
        alphablend: bool | None = None,
    ) -> str:
        """SWScaler AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if sws_flags is not None:
            if sws_flags:
                cmd_args.append("-sws_flags")
        if srcw is not None:
            if srcw:
                cmd_args.append("-srcw")
        if srch is not None:
            if srch:
                cmd_args.append("-srch")
        if dstw is not None:
            if dstw:
                cmd_args.append("-dstw")
        if dsth is not None:
            if dsth:
                cmd_args.append("-dsth")
        if src_format is not None:
            if src_format:
                cmd_args.append("-src_format")
        if dst_format is not None:
            if dst_format:
                cmd_args.append("-dst_format")
        if src_range is not None:
            if src_range:
                cmd_args.append("-src_range")
        if dst_range is not None:
            if dst_range:
                cmd_args.append("-dst_range")
        if param0 is not None:
            if param0:
                cmd_args.append("-param0")
        if param1 is not None:
            if param1:
                cmd_args.append("-param1")
        if src_v_chr_pos is not None:
            if src_v_chr_pos:
                cmd_args.append("-src_v_chr_pos")
        if src_h_chr_pos is not None:
            if src_h_chr_pos:
                cmd_args.append("-src_h_chr_pos")
        if dst_v_chr_pos is not None:
            if dst_v_chr_pos:
                cmd_args.append("-dst_v_chr_pos")
        if dst_h_chr_pos is not None:
            if dst_h_chr_pos:
                cmd_args.append("-dst_h_chr_pos")
        if sws_dither is not None:
            if sws_dither:
                cmd_args.append("-sws_dither")
        if gamma is not None:
            if gamma:
                cmd_args.append("-gamma")
        if alphablend is not None:
            if alphablend:
                cmd_args.append("-alphablend")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_swresampler_avoptions(
        ich: bool | None = None,
        in_channel_count: bool | None = None,
        och: bool | None = None,
        uch: bool | None = None,
        isr: bool | None = None,
        in_sample_rate: bool | None = None,
        osr: bool | None = None,
        out_sample_rate: bool | None = None,
        isf: bool | None = None,
        in_sample_fmt: bool | None = None,
        osf: bool | None = None,
        out_sample_fmt: bool | None = None,
        tsf: bool | None = None,
        icl: bool | None = None,
        ocl: bool | None = None,
        clev: bool | None = None,
        center_mix_level: bool | None = None,
        slev: bool | None = None,
        lfe_mix_level: bool | None = None,
        rmvol: bool | None = None,
        rematrix_volume: bool | None = None,
        rematrix_maxval: bool | None = None,
        flags: bool | None = None,
        swr_flags: bool | None = None,
        dither_scale: bool | None = None,
        dither_method: bool | None = None,
        filter_size: bool | None = None,
        phase_shift: bool | None = None,
        linear_interp: bool | None = None,
        exact_rational: bool | None = None,
        cutoff: bool | None = None,
        resample_cutoff: bool | None = None,
        resampler: bool | None = None,
        precision: bool | None = None,
        cheby: bool | None = None,
        min_comp: bool | None = None,
        min_hard_comp: bool | None = None,
        comp_duration: bool | None = None,
        max_soft_comp: bool | None = None,
        async_: bool | None = None,
        first_pts: bool | None = None,
        matrix_encoding: bool | None = None,
        filter_type: bool | None = None,
        kaiser_beta: bool | None = None,
    ) -> str:
        """SWResampler AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if ich is not None:
            if ich:
                cmd_args.append("-ich")
        if in_channel_count is not None:
            if in_channel_count:
                cmd_args.append("-in_channel_count")
        if och is not None:
            if och:
                cmd_args.append("-och")
        if uch is not None:
            if uch:
                cmd_args.append("-uch")
        if isr is not None:
            if isr:
                cmd_args.append("-isr")
        if in_sample_rate is not None:
            if in_sample_rate:
                cmd_args.append("-in_sample_rate")
        if osr is not None:
            if osr:
                cmd_args.append("-osr")
        if out_sample_rate is not None:
            if out_sample_rate:
                cmd_args.append("-out_sample_rate")
        if isf is not None:
            if isf:
                cmd_args.append("-isf")
        if in_sample_fmt is not None:
            if in_sample_fmt:
                cmd_args.append("-in_sample_fmt")
        if osf is not None:
            if osf:
                cmd_args.append("-osf")
        if out_sample_fmt is not None:
            if out_sample_fmt:
                cmd_args.append("-out_sample_fmt")
        if tsf is not None:
            if tsf:
                cmd_args.append("-tsf")
        if icl is not None:
            if icl:
                cmd_args.append("-icl")
        if ocl is not None:
            if ocl:
                cmd_args.append("-ocl")
        if clev is not None:
            if clev:
                cmd_args.append("-clev")
        if center_mix_level is not None:
            if center_mix_level:
                cmd_args.append("-center_mix_level")
        if slev is not None:
            if slev:
                cmd_args.append("-slev")
        if lfe_mix_level is not None:
            if lfe_mix_level:
                cmd_args.append("-lfe_mix_level")
        if rmvol is not None:
            if rmvol:
                cmd_args.append("-rmvol")
        if rematrix_volume is not None:
            if rematrix_volume:
                cmd_args.append("-rematrix_volume")
        if rematrix_maxval is not None:
            if rematrix_maxval:
                cmd_args.append("-rematrix_maxval")
        if flags is not None:
            if flags:
                cmd_args.append("-flags")
        if swr_flags is not None:
            if swr_flags:
                cmd_args.append("-swr_flags")
        if dither_scale is not None:
            if dither_scale:
                cmd_args.append("-dither_scale")
        if dither_method is not None:
            if dither_method:
                cmd_args.append("-dither_method")
        if filter_size is not None:
            if filter_size:
                cmd_args.append("-filter_size")
        if phase_shift is not None:
            if phase_shift:
                cmd_args.append("-phase_shift")
        if linear_interp is not None:
            if linear_interp:
                cmd_args.append("-linear_interp")
        if exact_rational is not None:
            if exact_rational:
                cmd_args.append("-exact_rational")
        if cutoff is not None:
            if cutoff:
                cmd_args.append("-cutoff")
        if resample_cutoff is not None:
            if resample_cutoff:
                cmd_args.append("-resample_cutoff")
        if resampler is not None:
            if resampler:
                cmd_args.append("-resampler")
        if precision is not None:
            if precision:
                cmd_args.append("-precision")
        if cheby is not None:
            if cheby:
                cmd_args.append("-cheby")
        if min_comp is not None:
            if min_comp:
                cmd_args.append("-min_comp")
        if min_hard_comp is not None:
            if min_hard_comp:
                cmd_args.append("-min_hard_comp")
        if comp_duration is not None:
            if comp_duration:
                cmd_args.append("-comp_duration")
        if max_soft_comp is not None:
            if max_soft_comp:
                cmd_args.append("-max_soft_comp")
        if async_ is not None:
            if async_:
                cmd_args.append("-async")
        if first_pts is not None:
            if first_pts:
                cmd_args.append("-first_pts")
        if matrix_encoding is not None:
            if matrix_encoding:
                cmd_args.append("-matrix_encoding")
        if filter_type is not None:
            if filter_type:
                cmd_args.append("-filter_type")
        if kaiser_beta is not None:
            if kaiser_beta:
                cmd_args.append("-kaiser_beta")
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def ffmpeg_avdct_avoptions(
        dct: bool | None = None,
        idct: bool | None = None,
        td: bool | None = None,
        color_primaries: bool | None = None,
        color_range: bool | None = None,
        tick_rate: bool | None = None,
        delete_padding: bool | None = None,
        freq: bool | None = None,
        remove: bool | None = None,
        pass_types: bool | None = None,
        remove_types: bool | None = None,
        aud: bool | None = None,
        video_format: bool | None = None,
        colour_primaries: bool | None = None,
        crop_left: bool | None = None,
        crop_right: bool | None = None,
        crop_top: bool | None = None,
        crop_bottom: bool | None = None,
        sei_user_data: bool | None = None,
        delete_filler: bool | None = None,
        rotate: bool | None = None,
        flip: bool | None = None,
        level: bool | None = None,
        texture: bool | None = None,
        frame_rate: bool | None = None,
        amount: bool | None = None,
        dropamount: bool | None = None,
        gain: bool | None = None,
        nb_out_samples: bool | None = None,
        n: bool | None = None,
        pad: bool | None = None,
        p: bool | None = None,
        r: bool | None = None,
        color_trc: bool | None = None,
        colorspace: bool | None = None,
        ts: bool | None = None,
        pts: bool | None = None,
        dts: bool | None = None,
        color_space: bool | None = None,
    ) -> str:
        """AVDCT AVOptions options for ffmpeg"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if dct is not None:
            if dct:
                cmd_args.append("-dct")
        if idct is not None:
            if idct:
                cmd_args.append("-idct")
        if td is not None:
            if td:
                cmd_args.append("-td")
        if color_primaries is not None:
            if color_primaries:
                cmd_args.append("-color_primaries")
        if color_range is not None:
            if color_range:
                cmd_args.append("-color_range")
        if tick_rate is not None:
            if tick_rate:
                cmd_args.append("-tick_rate")
        if delete_padding is not None:
            if delete_padding:
                cmd_args.append("-delete_padding")
        if freq is not None:
            if freq:
                cmd_args.append("-freq")
        if remove is not None:
            if remove:
                cmd_args.append("-remove")
        if pass_types is not None:
            if pass_types:
                cmd_args.append("-pass_types")
        if remove_types is not None:
            if remove_types:
                cmd_args.append("-remove_types")
        if aud is not None:
            if aud:
                cmd_args.append("-aud")
        if video_format is not None:
            if video_format:
                cmd_args.append("-video_format")
        if colour_primaries is not None:
            if colour_primaries:
                cmd_args.append("-colour_primaries")
        if crop_left is not None:
            if crop_left:
                cmd_args.append("-crop_left")
        if crop_right is not None:
            if crop_right:
                cmd_args.append("-crop_right")
        if crop_top is not None:
            if crop_top:
                cmd_args.append("-crop_top")
        if crop_bottom is not None:
            if crop_bottom:
                cmd_args.append("-crop_bottom")
        if sei_user_data is not None:
            if sei_user_data:
                cmd_args.append("-sei_user_data")
        if delete_filler is not None:
            if delete_filler:
                cmd_args.append("-delete_filler")
        if rotate is not None:
            if rotate:
                cmd_args.append("-rotate")
        if flip is not None:
            if flip:
                cmd_args.append("-flip")
        if level is not None:
            if level:
                cmd_args.append("-level")
        if texture is not None:
            if texture:
                cmd_args.append("-texture")
        if frame_rate is not None:
            if frame_rate:
                cmd_args.append("-frame_rate")
        if amount is not None:
            if amount:
                cmd_args.append("-amount")
        if dropamount is not None:
            if dropamount:
                cmd_args.append("-dropamount")
        if gain is not None:
            if gain:
                cmd_args.append("-gain")
        if nb_out_samples is not None:
            if nb_out_samples:
                cmd_args.append("-nb_out_samples")
        if n is not None:
            if n:
                cmd_args.append("-n")
        if pad is not None:
            if pad:
                cmd_args.append("-pad")
        if p is not None:
            if p:
                cmd_args.append("-p")
        if r is not None:
            if r:
                cmd_args.append("-r")
        if color_trc is not None:
            if color_trc:
                cmd_args.append("-color_trc")
        if colorspace is not None:
            if colorspace:
                cmd_args.append("-colorspace")
        if ts is not None:
            if ts:
                cmd_args.append("-ts")
        if pts is not None:
            if pts:
                cmd_args.append("-pts")
        if dts is not None:
            if dts:
                cmd_args.append("-dts")
        if color_space is not None:
            if color_space:
                cmd_args.append("-color_space")
        return await backend.run_subcommand("", cmd_args)

