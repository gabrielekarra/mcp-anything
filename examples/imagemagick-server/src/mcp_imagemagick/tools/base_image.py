"""base_image tools for imagemagick."""

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
    """Register base_image tools with the server."""

    @server.tool()
    async def base_image_adaptive_blur(
        radius: str | None = "0.0",
        sigma: str | None = "0.0",
        channel: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Adaptively blurs the image by decreasing Gaussian as the operator"""
        # Instance method: image.BaseImage.adaptive_blur
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if radius is not None:
            kwargs["radius"] = radius
        if sigma is not None:
            kwargs["sigma"] = sigma
        if channel is not None:
            kwargs["channel"] = channel
        method_attr = inspect.getattr_static(cls, "adaptive_blur")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "adaptive_blur")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "adaptive_blur")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_adaptive_resize(
        columns: str | None = None,
        rows: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Adaptively resize image by applying Mesh interpolation."""
        # Instance method: image.BaseImage.adaptive_resize
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if columns is not None:
            kwargs["columns"] = columns
        if rows is not None:
            kwargs["rows"] = rows
        method_attr = inspect.getattr_static(cls, "adaptive_resize")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "adaptive_resize")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "adaptive_resize")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_adaptive_sharpen(
        radius: str | None = "0.0",
        sigma: str | None = "0.0",
        channel: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Adaptively sharpens the image by sharpening more intensely near"""
        # Instance method: image.BaseImage.adaptive_sharpen
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if radius is not None:
            kwargs["radius"] = radius
        if sigma is not None:
            kwargs["sigma"] = sigma
        if channel is not None:
            kwargs["channel"] = channel
        method_attr = inspect.getattr_static(cls, "adaptive_sharpen")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "adaptive_sharpen")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "adaptive_sharpen")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_adaptive_threshold(
        width: str,
        height: str,
        offset: str | None = "0.0",
        init_wand: str | None = None,
    ) -> str:
        """Applies threshold for each pixel based on neighboring pixel values."""
        # Instance method: image.BaseImage.adaptive_threshold
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        kwargs["width"] = width
        kwargs["height"] = height
        if offset is not None:
            kwargs["offset"] = offset
        method_attr = inspect.getattr_static(cls, "adaptive_threshold")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "adaptive_threshold")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "adaptive_threshold")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_affine(
        sx: str | None = "1",
        rx: str | None = "0",
        ry: str | None = "0",
        sy: str | None = "1",
        tx: str | None = "0",
        ty: str | None = "0",
        init_wand: str | None = None,
    ) -> str:
        """Transforms an image by applying an affine matrix."""
        # Instance method: image.BaseImage.affine
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if sx is not None:
            kwargs["sx"] = sx
        if rx is not None:
            kwargs["rx"] = rx
        if ry is not None:
            kwargs["ry"] = ry
        if sy is not None:
            kwargs["sy"] = sy
        if tx is not None:
            kwargs["tx"] = tx
        if ty is not None:
            kwargs["ty"] = ty
        method_attr = inspect.getattr_static(cls, "affine")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "affine")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "affine")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_alpha_channel(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`bool`) Get state of image alpha channel."""
        # Instance method: image.BaseImage.alpha_channel
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "alpha_channel")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "alpha_channel")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "alpha_channel")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_animation(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`bool`) Whether the image is animation or not."""
        # Instance method: image.BaseImage.animation
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "animation")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "animation")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "animation")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_annotate(
        text: str,
        drawing_wand: str,
        left: str | None = "0",
        baseline: str | None = "0",
        angle: str | None = "0",
        init_wand: str | None = None,
    ) -> str:
        """Draws text on an image. This method differs from :meth:`caption()`"""
        # Instance method: image.BaseImage.annotate
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        kwargs["text"] = text
        kwargs["drawing_wand"] = drawing_wand
        if left is not None:
            kwargs["left"] = left
        if baseline is not None:
            kwargs["baseline"] = baseline
        if angle is not None:
            kwargs["angle"] = angle
        method_attr = inspect.getattr_static(cls, "annotate")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "annotate")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "annotate")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_antialias(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`bool`) If vectors & fonts will use anti-aliasing."""
        # Instance method: image.BaseImage.antialias
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "antialias")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "antialias")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "antialias")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_auto_gamma(
        init_wand: str | None = None,
    ) -> str:
        """Adjust the gamma level of an image."""
        # Instance method: image.BaseImage.auto_gamma
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "auto_gamma")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "auto_gamma")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "auto_gamma")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_auto_level(
        init_wand: str | None = None,
    ) -> str:
        """Scale the minimum and maximum values to a full quantum range."""
        # Instance method: image.BaseImage.auto_level
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "auto_level")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "auto_level")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "auto_level")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_auto_orient(
        init_wand: str | None = None,
    ) -> str:
        """Adjusts an image so that its orientation is suitable"""
        # Instance method: image.BaseImage.auto_orient
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "auto_orient")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "auto_orient")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "auto_orient")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_auto_threshold(
        method: str | None = "kapur",
        init_wand: str | None = None,
    ) -> str:
        """Automatically performs threshold method to reduce grayscale data"""
        # Instance method: image.BaseImage.auto_threshold
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if method is not None:
            kwargs["method"] = method
        method_attr = inspect.getattr_static(cls, "auto_threshold")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "auto_threshold")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "auto_threshold")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_background_color(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`wand.color.Color`) The image background color."""
        # Instance method: image.BaseImage.background_color
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "background_color")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "background_color")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "background_color")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_bilateral_blur(
        width: str | None = "1.0",
        height: str | None = None,
        intensity: str | None = None,
        spatial: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Noise-reducing Gaussian distrbution filter. Preserves edges by"""
        # Instance method: image.BaseImage.bilateral_blur
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if width is not None:
            kwargs["width"] = width
        if height is not None:
            kwargs["height"] = height
        if intensity is not None:
            kwargs["intensity"] = intensity
        if spatial is not None:
            kwargs["spatial"] = spatial
        method_attr = inspect.getattr_static(cls, "bilateral_blur")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "bilateral_blur")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "bilateral_blur")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_black_threshold(
        threshold: str,
        init_wand: str | None = None,
    ) -> str:
        """Forces all pixels above a given color as black. Leaves pixels"""
        # Instance method: image.BaseImage.black_threshold
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        kwargs["threshold"] = threshold
        method_attr = inspect.getattr_static(cls, "black_threshold")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "black_threshold")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "black_threshold")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_blue_primary(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`tuple`) The chromatic blue primary point for the image."""
        # Instance method: image.BaseImage.blue_primary
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "blue_primary")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "blue_primary")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "blue_primary")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_blue_shift(
        factor: str | None = "1.5",
        init_wand: str | None = None,
    ) -> str:
        """Mutes colors of the image by shifting blue values."""
        # Instance method: image.BaseImage.blue_shift
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if factor is not None:
            kwargs["factor"] = factor
        method_attr = inspect.getattr_static(cls, "blue_shift")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "blue_shift")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "blue_shift")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_blur(
        radius: str | None = "0.0",
        sigma: str | None = "0.0",
        channel: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Blurs the image.  Convolve the image with a gaussian operator"""
        # Instance method: image.BaseImage.blur
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if radius is not None:
            kwargs["radius"] = radius
        if sigma is not None:
            kwargs["sigma"] = sigma
        if channel is not None:
            kwargs["channel"] = channel
        method_attr = inspect.getattr_static(cls, "blur")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "blur")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "blur")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_border(
        color: str,
        width: str,
        height: str,
        compose: str | None = "copy",
        init_wand: str | None = None,
    ) -> str:
        """Surrounds the image with a border."""
        # Instance method: image.BaseImage.border
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        kwargs["color"] = color
        kwargs["width"] = width
        kwargs["height"] = height
        if compose is not None:
            kwargs["compose"] = compose
        method_attr = inspect.getattr_static(cls, "border")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "border")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "border")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_border_color(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`wand.color.Color`) The image border color. Used for"""
        # Instance method: image.BaseImage.border_color
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "border_color")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "border_color")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "border_color")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_brightness_contrast(
        brightness: str | None = "0.0",
        contrast: str | None = "0.0",
        channel: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Converts ``brightness`` & ``contrast`` parameters into a slope &"""
        # Instance method: image.BaseImage.brightness_contrast
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if brightness is not None:
            kwargs["brightness"] = brightness
        if contrast is not None:
            kwargs["contrast"] = contrast
        if channel is not None:
            kwargs["channel"] = channel
        method_attr = inspect.getattr_static(cls, "brightness_contrast")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "brightness_contrast")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "brightness_contrast")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_canny(
        radius: str | None = "0.0",
        sigma: str | None = "1.0",
        lower_percent: str | None = "0.1",
        upper_percent: str | None = "0.3",
        init_wand: str | None = None,
    ) -> str:
        """Detect edges by leveraging a multi-stage Canny algorithm."""
        # Instance method: image.BaseImage.canny
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if radius is not None:
            kwargs["radius"] = radius
        if sigma is not None:
            kwargs["sigma"] = sigma
        if lower_percent is not None:
            kwargs["lower_percent"] = lower_percent
        if upper_percent is not None:
            kwargs["upper_percent"] = upper_percent
        method_attr = inspect.getattr_static(cls, "canny")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "canny")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "canny")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_caption(
        text: str,
        left: str | None = "0",
        top: str | None = "0",
        width: str | None = None,
        height: str | None = None,
        font: str | None = None,
        gravity: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Writes a caption ``text`` into the position."""
        # Instance method: image.BaseImage.caption
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        kwargs["text"] = text
        if left is not None:
            kwargs["left"] = left
        if top is not None:
            kwargs["top"] = top
        if width is not None:
            kwargs["width"] = width
        if height is not None:
            kwargs["height"] = height
        if font is not None:
            kwargs["font"] = font
        if gravity is not None:
            kwargs["gravity"] = gravity
        method_attr = inspect.getattr_static(cls, "caption")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "caption")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "caption")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_cdl(
        ccc: str,
        init_wand: str | None = None,
    ) -> str:
        """Alias for :meth:`color_decision_list`."""
        # Instance method: image.BaseImage.cdl
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        kwargs["ccc"] = ccc
        method_attr = inspect.getattr_static(cls, "cdl")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "cdl")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "cdl")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_charcoal(
        radius: str,
        sigma: str,
        init_wand: str | None = None,
    ) -> str:
        """Transform an image into a simulated charcoal drawing."""
        # Instance method: image.BaseImage.charcoal
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        kwargs["radius"] = radius
        kwargs["sigma"] = sigma
        method_attr = inspect.getattr_static(cls, "charcoal")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "charcoal")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "charcoal")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_chop(
        width: str | None = None,
        height: str | None = None,
        x: str | None = None,
        y: str | None = None,
        gravity: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Removes a region of an image, and reduces the image size"""
        # Instance method: image.BaseImage.chop
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if width is not None:
            kwargs["width"] = width
        if height is not None:
            kwargs["height"] = height
        if x is not None:
            kwargs["x"] = x
        if y is not None:
            kwargs["y"] = y
        if gravity is not None:
            kwargs["gravity"] = gravity
        method_attr = inspect.getattr_static(cls, "chop")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "chop")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "chop")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_clahe(
        width: str,
        height: str,
        number_bins: str,
        clip_limit: str,
        init_wand: str | None = None,
    ) -> str:
        """Contrast limited adaptive histogram equalization."""
        # Instance method: image.BaseImage.clahe
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        kwargs["width"] = width
        kwargs["height"] = height
        kwargs["number_bins"] = number_bins
        kwargs["clip_limit"] = clip_limit
        method_attr = inspect.getattr_static(cls, "clahe")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "clahe")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "clahe")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_clamp(
        channel: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Restrict color values between 0 and quantum range. This is useful"""
        # Instance method: image.BaseImage.clamp
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if channel is not None:
            kwargs["channel"] = channel
        method_attr = inspect.getattr_static(cls, "clamp")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "clamp")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "clamp")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_clone(
        init_wand: str | None = None,
    ) -> str:
        """Clones the image. It is equivalent to call :class:`Image` with"""
        # Instance method: image.BaseImage.clone
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "clone")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "clone")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "clone")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_clut(
        image: str,
        method: str | None = "undefined",
        channel: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Replace color values by referencing another image as a Color"""
        # Instance method: image.BaseImage.clut
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        kwargs["image"] = image
        if method is not None:
            kwargs["method"] = method
        if channel is not None:
            kwargs["channel"] = channel
        method_attr = inspect.getattr_static(cls, "clut")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "clut")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "clut")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_coalesce(
        init_wand: str | None = None,
    ) -> str:
        """Rebuilds image sequence with each frame size the same as first"""
        # Instance method: image.BaseImage.coalesce
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "coalesce")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "coalesce")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "coalesce")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_color_decision_list(
        ccc: str,
        init_wand: str | None = None,
    ) -> str:
        """Applies color correction from a Color Correction Collection (CCC)"""
        # Instance method: image.BaseImage.color_decision_list
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        kwargs["ccc"] = ccc
        method_attr = inspect.getattr_static(cls, "color_decision_list")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "color_decision_list")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "color_decision_list")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_color_map(
        index: str,
        color: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Get & Set a color at a palette index. If ``color`` is given,"""
        # Instance method: image.BaseImage.color_map
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        kwargs["index"] = index
        if color is not None:
            kwargs["color"] = color
        method_attr = inspect.getattr_static(cls, "color_map")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "color_map")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "color_map")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_color_matrix(
        matrix: str,
        init_wand: str | None = None,
    ) -> str:
        """Adjust color values by applying a matrix transform per pixel."""
        # Instance method: image.BaseImage.color_matrix
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        kwargs["matrix"] = matrix
        method_attr = inspect.getattr_static(cls, "color_matrix")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "color_matrix")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "color_matrix")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_color_threshold(
        start: str | None = None,
        stop: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Forces all pixels in color range to white, and all other pixels to"""
        # Instance method: image.BaseImage.color_threshold
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if start is not None:
            kwargs["start"] = start
        if stop is not None:
            kwargs["stop"] = stop
        method_attr = inspect.getattr_static(cls, "color_threshold")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "color_threshold")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "color_threshold")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_colorize(
        color: str | None = None,
        alpha: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Blends a given fill color over the image. The amount of blend is"""
        # Instance method: image.BaseImage.colorize
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if color is not None:
            kwargs["color"] = color
        if alpha is not None:
            kwargs["alpha"] = alpha
        method_attr = inspect.getattr_static(cls, "colorize")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "colorize")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "colorize")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_colors(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`numbers.Integral`) Count of unique colors used within the"""
        # Instance method: image.BaseImage.colors
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "colors")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "colors")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "colors")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_colorspace(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`str`) The image colorspace."""
        # Instance method: image.BaseImage.colorspace
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "colorspace")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "colorspace")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "colorspace")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_combine(
        channel: str | None = "rgb_channels",
        colorspace: str | None = "rgb",
        init_wand: str | None = None,
    ) -> str:
        """Creates an image where each color channel is assigned by a grayscale"""
        # Instance method: image.BaseImage.combine
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if channel is not None:
            kwargs["channel"] = channel
        if colorspace is not None:
            kwargs["colorspace"] = colorspace
        method_attr = inspect.getattr_static(cls, "combine")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "combine")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "combine")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_compare(
        image: str,
        metric: str | None = "undefined",
        highlight: str | None = None,
        lowlight: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Compares an image with another, and returns a reconstructed"""
        # Instance method: image.BaseImage.compare
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        kwargs["image"] = image
        if metric is not None:
            kwargs["metric"] = metric
        if highlight is not None:
            kwargs["highlight"] = highlight
        if lowlight is not None:
            kwargs["lowlight"] = lowlight
        method_attr = inspect.getattr_static(cls, "compare")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "compare")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "compare")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_complex(
        operator: str | None = "undefined",
        snr: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Performs `complex`_ mathematics against two images in a sequence,"""
        # Instance method: image.BaseImage.complex
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if operator is not None:
            kwargs["operator"] = operator
        if snr is not None:
            kwargs["snr"] = snr
        method_attr = inspect.getattr_static(cls, "complex")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "complex")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "complex")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_compose(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`str`) The type of image compose."""
        # Instance method: image.BaseImage.compose
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "compose")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "compose")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "compose")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_composite(
        image: str,
        left: str | None = None,
        top: str | None = None,
        operator: str | None = "over",
        arguments: str | None = None,
        gravity: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Places the supplied ``image`` over the current image, with the top"""
        # Instance method: image.BaseImage.composite
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        kwargs["image"] = image
        if left is not None:
            kwargs["left"] = left
        if top is not None:
            kwargs["top"] = top
        if operator is not None:
            kwargs["operator"] = operator
        if arguments is not None:
            kwargs["arguments"] = arguments
        if gravity is not None:
            kwargs["gravity"] = gravity
        method_attr = inspect.getattr_static(cls, "composite")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "composite")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "composite")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_composite_channel(
        channel: str,
        image: str,
        operator: str,
        left: str | None = None,
        top: str | None = None,
        arguments: str | None = None,
        gravity: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Composite two images using the particular ``channel``."""
        # Instance method: image.BaseImage.composite_channel
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        kwargs["channel"] = channel
        kwargs["image"] = image
        kwargs["operator"] = operator
        if left is not None:
            kwargs["left"] = left
        if top is not None:
            kwargs["top"] = top
        if arguments is not None:
            kwargs["arguments"] = arguments
        if gravity is not None:
            kwargs["gravity"] = gravity
        method_attr = inspect.getattr_static(cls, "composite_channel")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "composite_channel")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "composite_channel")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_compression(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`str`) The type of image compression."""
        # Instance method: image.BaseImage.compression
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "compression")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "compression")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "compression")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_compression_quality(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`numbers.Integral`) Compression quality of this image."""
        # Instance method: image.BaseImage.compression_quality
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "compression_quality")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "compression_quality")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "compression_quality")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_concat(
        stacked: str | None = "False",
        init_wand: str | None = None,
    ) -> str:
        """Concatenates images in stack into a single image. Left-to-right"""
        # Instance method: image.BaseImage.concat
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if stacked is not None:
            kwargs["stacked"] = stacked
        method_attr = inspect.getattr_static(cls, "concat")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "concat")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "concat")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_connected_components(
        init_wand: str | None = None,
    ) -> str:
        """Evaluates binary image, and groups connected pixels into objects."""
        # Instance method: image.BaseImage.connected_components
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "connected_components")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "connected_components")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "connected_components")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_contrast(
        sharpen: str | None = "True",
        init_wand: str | None = None,
    ) -> str:
        """Enhances the difference between lighter & darker values of the"""
        # Instance method: image.BaseImage.contrast
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if sharpen is not None:
            kwargs["sharpen"] = sharpen
        method_attr = inspect.getattr_static(cls, "contrast")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "contrast")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "contrast")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_contrast_stretch(
        black_point: str | None = "0.0",
        white_point: str | None = None,
        channel: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Enhance contrast of image by adjusting the span of the available"""
        # Instance method: image.BaseImage.contrast_stretch
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if black_point is not None:
            kwargs["black_point"] = black_point
        if white_point is not None:
            kwargs["white_point"] = white_point
        if channel is not None:
            kwargs["channel"] = channel
        method_attr = inspect.getattr_static(cls, "contrast_stretch")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "contrast_stretch")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "contrast_stretch")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_convex_hull(
        background: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Find the smallest convex polygon, and returns a list of points."""
        # Instance method: image.BaseImage.convex_hull
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if background is not None:
            kwargs["background"] = background
        method_attr = inspect.getattr_static(cls, "convex_hull")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "convex_hull")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "convex_hull")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_cycle_color_map(
        offset: str | None = "1",
        init_wand: str | None = None,
    ) -> str:
        """Shift the image color-map by a given offset."""
        # Instance method: image.BaseImage.cycle_color_map
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if offset is not None:
            kwargs["offset"] = offset
        method_attr = inspect.getattr_static(cls, "cycle_color_map")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "cycle_color_map")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "cycle_color_map")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_decipher(
        passphrase: str,
        init_wand: str | None = None,
    ) -> str:
        """Decrypt ciphered pixels into original values."""
        # Instance method: image.BaseImage.decipher
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        kwargs["passphrase"] = passphrase
        method_attr = inspect.getattr_static(cls, "decipher")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "decipher")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "decipher")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_deconstruct(
        init_wand: str | None = None,
    ) -> str:
        """Iterates over internal image stack, and adjust each frame size to"""
        # Instance method: image.BaseImage.deconstruct
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "deconstruct")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "deconstruct")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "deconstruct")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_delay(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`numbers.Integral`) The number of ticks between frames."""
        # Instance method: image.BaseImage.delay
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "delay")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "delay")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "delay")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_depth(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`numbers.Integral`) The depth of this image."""
        # Instance method: image.BaseImage.depth
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "depth")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "depth")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "depth")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_deskew(
        threshold: str,
        init_wand: str | None = None,
    ) -> str:
        """Attempts to remove skew artifacts common with most"""
        # Instance method: image.BaseImage.deskew
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        kwargs["threshold"] = threshold
        method_attr = inspect.getattr_static(cls, "deskew")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "deskew")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "deskew")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_despeckle(
        init_wand: str | None = None,
    ) -> str:
        """Applies filter to reduce noise in image."""
        # Instance method: image.BaseImage.despeckle
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "despeckle")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "despeckle")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "despeckle")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_dispose(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`str`) Controls how the image data is"""
        # Instance method: image.BaseImage.dispose
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "dispose")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "dispose")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "dispose")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_distort(
        method: str,
        arguments: str,
        best_fit: str | None = "False",
        filter: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Distorts an image using various distorting methods."""
        # Instance method: image.BaseImage.distort
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        kwargs["method"] = method
        kwargs["arguments"] = arguments
        if best_fit is not None:
            kwargs["best_fit"] = best_fit
        if filter is not None:
            kwargs["filter"] = filter
        method_attr = inspect.getattr_static(cls, "distort")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "distort")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "distort")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_edge(
        radius: str | None = "0.0",
        init_wand: str | None = None,
    ) -> str:
        """Applies convolution filter to detect edges."""
        # Instance method: image.BaseImage.edge
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if radius is not None:
            kwargs["radius"] = radius
        method_attr = inspect.getattr_static(cls, "edge")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "edge")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "edge")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_emboss(
        radius: str | None = "0.0",
        sigma: str | None = "0.0",
        init_wand: str | None = None,
    ) -> str:
        """Applies convolution filter against Gaussians filter."""
        # Instance method: image.BaseImage.emboss
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if radius is not None:
            kwargs["radius"] = radius
        if sigma is not None:
            kwargs["sigma"] = sigma
        method_attr = inspect.getattr_static(cls, "emboss")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "emboss")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "emboss")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_encipher(
        passphrase: str,
        init_wand: str | None = None,
    ) -> str:
        """Encrypt plain pixels into ciphered values."""
        # Instance method: image.BaseImage.encipher
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        kwargs["passphrase"] = passphrase
        method_attr = inspect.getattr_static(cls, "encipher")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "encipher")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "encipher")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_enhance(
        init_wand: str | None = None,
    ) -> str:
        """Applies digital filter to reduce noise."""
        # Instance method: image.BaseImage.enhance
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "enhance")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "enhance")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "enhance")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_equalize(
        channel: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Equalizes the image histogram"""
        # Instance method: image.BaseImage.equalize
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if channel is not None:
            kwargs["channel"] = channel
        method_attr = inspect.getattr_static(cls, "equalize")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "equalize")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "equalize")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_evaluate(
        operator: str | None = None,
        value: str | None = "0.0",
        channel: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Apply arithmetic, relational, or logical expression to an image."""
        # Instance method: image.BaseImage.evaluate
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if operator is not None:
            kwargs["operator"] = operator
        if value is not None:
            kwargs["value"] = value
        if channel is not None:
            kwargs["channel"] = channel
        method_attr = inspect.getattr_static(cls, "evaluate")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "evaluate")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "evaluate")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_evaluate_images(
        operator: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Create a new image by applying arithmetic operation between all"""
        # Instance method: image.BaseImage.evaluate_images
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if operator is not None:
            kwargs["operator"] = operator
        method_attr = inspect.getattr_static(cls, "evaluate_images")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "evaluate_images")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "evaluate_images")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_export_pixels(
        x: str | None = "0",
        y: str | None = "0",
        width: str | None = None,
        height: str | None = None,
        channel_map: str | None = "RGBA",
        storage: str | None = "char",
        init_wand: str | None = None,
    ) -> str:
        """Export pixel data from a raster image to"""
        # Instance method: image.BaseImage.export_pixels
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if x is not None:
            kwargs["x"] = x
        if y is not None:
            kwargs["y"] = y
        if width is not None:
            kwargs["width"] = width
        if height is not None:
            kwargs["height"] = height
        if channel_map is not None:
            kwargs["channel_map"] = channel_map
        if storage is not None:
            kwargs["storage"] = storage
        method_attr = inspect.getattr_static(cls, "export_pixels")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "export_pixels")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "export_pixels")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_extent(
        width: str | None = None,
        height: str | None = None,
        x: str | None = None,
        y: str | None = None,
        gravity: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Adjust the canvas size of the image. Use ``x`` & ``y`` to offset"""
        # Instance method: image.BaseImage.extent
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if width is not None:
            kwargs["width"] = width
        if height is not None:
            kwargs["height"] = height
        if x is not None:
            kwargs["x"] = x
        if y is not None:
            kwargs["y"] = y
        if gravity is not None:
            kwargs["gravity"] = gravity
        method_attr = inspect.getattr_static(cls, "extent")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "extent")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "extent")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_fft(
        magnitude: str | None = "True",
        init_wand: str | None = None,
    ) -> str:
        """Alias for :meth:`forward_fourier_transform`."""
        # Instance method: image.BaseImage.fft
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if magnitude is not None:
            kwargs["magnitude"] = magnitude
        method_attr = inspect.getattr_static(cls, "fft")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "fft")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "fft")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_flip(
        init_wand: str | None = None,
    ) -> str:
        """Creates a vertical mirror image by reflecting the pixels around"""
        # Instance method: image.BaseImage.flip
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "flip")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "flip")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "flip")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_floodfill(
        fill: str | None = "none",
        fuzz: str | None = "0.1",
        bordercolor: str | None = None,
        x: str | None = "0",
        y: str | None = "0",
        invert: str | None = "False",
        channel: str | None = "default_channels",
        init_wand: str | None = None,
    ) -> str:
        """Changes pixel value to ``fill`` color at (``x``, ``y``) coordinate,"""
        # Instance method: image.BaseImage.floodfill
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if fill is not None:
            kwargs["fill"] = fill
        if fuzz is not None:
            kwargs["fuzz"] = fuzz
        if bordercolor is not None:
            kwargs["bordercolor"] = bordercolor
        if x is not None:
            kwargs["x"] = x
        if y is not None:
            kwargs["y"] = y
        if invert is not None:
            kwargs["invert"] = invert
        if channel is not None:
            kwargs["channel"] = channel
        method_attr = inspect.getattr_static(cls, "floodfill")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "floodfill")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "floodfill")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_flop(
        init_wand: str | None = None,
    ) -> str:
        """Creates a horizontal mirror image by reflecting the pixels around"""
        # Instance method: image.BaseImage.flop
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "flop")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "flop")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "flop")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_font(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`wand.font.Font`) The current font options."""
        # Instance method: image.BaseImage.font
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "font")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "font")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "font")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_font_antialias(
        init_wand: str | None = None,
    ) -> str:
        """.. deprecated:: 0.5.0"""
        # Instance method: image.BaseImage.font_antialias
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "font_antialias")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "font_antialias")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "font_antialias")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_font_color(
        init_wand: str | None = None,
    ) -> str:
        """Font color"""
        # Instance method: image.BaseImage.font_color
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "font_color")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "font_color")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "font_color")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_font_path(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`str`) The path of the current font."""
        # Instance method: image.BaseImage.font_path
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "font_path")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "font_path")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "font_path")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_font_size(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`numbers.Real`) The font size.  It also can be set."""
        # Instance method: image.BaseImage.font_size
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "font_size")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "font_size")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "font_size")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_format(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`str`) The image format."""
        # Instance method: image.BaseImage.format
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "format")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "format")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "format")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_forward_fourier_transform(
        magnitude: str | None = "True",
        init_wand: str | None = None,
    ) -> str:
        """Performs a discrete Fourier transform. The image stack is replaced"""
        # Instance method: image.BaseImage.forward_fourier_transform
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if magnitude is not None:
            kwargs["magnitude"] = magnitude
        method_attr = inspect.getattr_static(cls, "forward_fourier_transform")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "forward_fourier_transform")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "forward_fourier_transform")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_frame(
        matte: str | None = None,
        width: str | None = "1",
        height: str | None = "1",
        inner_bevel: str | None = "0",
        outer_bevel: str | None = "0",
        compose: str | None = "over",
        init_wand: str | None = None,
    ) -> str:
        """Creates a bordered frame around image."""
        # Instance method: image.BaseImage.frame
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if matte is not None:
            kwargs["matte"] = matte
        if width is not None:
            kwargs["width"] = width
        if height is not None:
            kwargs["height"] = height
        if inner_bevel is not None:
            kwargs["inner_bevel"] = inner_bevel
        if outer_bevel is not None:
            kwargs["outer_bevel"] = outer_bevel
        if compose is not None:
            kwargs["compose"] = compose
        method_attr = inspect.getattr_static(cls, "frame")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "frame")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "frame")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_function(
        function: str,
        arguments: str,
        channel: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Apply an arithmetic, relational, or logical expression to an image."""
        # Instance method: image.BaseImage.function
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        kwargs["function"] = function
        kwargs["arguments"] = arguments
        if channel is not None:
            kwargs["channel"] = channel
        method_attr = inspect.getattr_static(cls, "function")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "function")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "function")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_fuzz(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`numbers.Real`) The normalized real number between ``0.0``"""
        # Instance method: image.BaseImage.fuzz
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "fuzz")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "fuzz")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "fuzz")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_fx(
        expression: str,
        channel: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Manipulate each pixel of an image by given expression."""
        # Instance method: image.BaseImage.fx
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        kwargs["expression"] = expression
        if channel is not None:
            kwargs["channel"] = channel
        method_attr = inspect.getattr_static(cls, "fx")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "fx")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "fx")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_gamma(
        adjustment_value: str | None = "1.0",
        channel: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Gamma correct image."""
        # Instance method: image.BaseImage.gamma
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if adjustment_value is not None:
            kwargs["adjustment_value"] = adjustment_value
        if channel is not None:
            kwargs["channel"] = channel
        method_attr = inspect.getattr_static(cls, "gamma")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "gamma")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "gamma")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_gaussian_blur(
        radius: str | None = "0.0",
        sigma: str | None = "0.0",
        channel: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Blurs the image.  We convolve the image with a gaussian operator"""
        # Instance method: image.BaseImage.gaussian_blur
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if radius is not None:
            kwargs["radius"] = radius
        if sigma is not None:
            kwargs["sigma"] = sigma
        if channel is not None:
            kwargs["channel"] = channel
        method_attr = inspect.getattr_static(cls, "gaussian_blur")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "gaussian_blur")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "gaussian_blur")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_get_image_distortion(
        image: str,
        metric: str | None = "undefined",
        init_wand: str | None = None,
    ) -> str:
        """Compares two images, and return the specified distortion metric."""
        # Instance method: image.BaseImage.get_image_distortion
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        kwargs["image"] = image
        if metric is not None:
            kwargs["metric"] = metric
        method_attr = inspect.getattr_static(cls, "get_image_distortion")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "get_image_distortion")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "get_image_distortion")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_gravity(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`str`) The text placement gravity used when"""
        # Instance method: image.BaseImage.gravity
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "gravity")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "gravity")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "gravity")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_green_primary(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`tuple`) The chromatic green primary point for the image."""
        # Instance method: image.BaseImage.green_primary
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "green_primary")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "green_primary")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "green_primary")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_hald_clut(
        image: str,
        channel: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Replace color values by referencing a Higher And Lower Dimension"""
        # Instance method: image.BaseImage.hald_clut
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        kwargs["image"] = image
        if channel is not None:
            kwargs["channel"] = channel
        method_attr = inspect.getattr_static(cls, "hald_clut")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "hald_clut")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "hald_clut")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_height(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`numbers.Integral`) The height of this image."""
        # Instance method: image.BaseImage.height
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "height")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "height")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "height")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_histogram(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`HistogramDict`) The mapping that represents the histogram."""
        # Instance method: image.BaseImage.histogram
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "histogram")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "histogram")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "histogram")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_hough_lines(
        width: str,
        height: str | None = None,
        threshold: str | None = "40",
        init_wand: str | None = None,
    ) -> str:
        """Identify lines within an image. Use :meth:`canny` to reduce image"""
        # Instance method: image.BaseImage.hough_lines
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        kwargs["width"] = width
        if height is not None:
            kwargs["height"] = height
        if threshold is not None:
            kwargs["threshold"] = threshold
        method_attr = inspect.getattr_static(cls, "hough_lines")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "hough_lines")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "hough_lines")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_ift(
        phase: str,
        magnitude: str | None = "True",
        init_wand: str | None = None,
    ) -> str:
        """Alias for :meth:`inverse_fourier_transform`."""
        # Instance method: image.BaseImage.ift
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        kwargs["phase"] = phase
        if magnitude is not None:
            kwargs["magnitude"] = magnitude
        method_attr = inspect.getattr_static(cls, "ift")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "ift")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "ift")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_implode(
        amount: str | None = "0.0",
        method: str | None = "undefined",
        init_wand: str | None = None,
    ) -> str:
        """Creates a "imploding" effect by pulling pixels towards the center"""
        # Instance method: image.BaseImage.implode
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if amount is not None:
            kwargs["amount"] = amount
        if method is not None:
            kwargs["method"] = method
        method_attr = inspect.getattr_static(cls, "implode")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "implode")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "implode")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_import_pixels(
        x: str | None = "0",
        y: str | None = "0",
        width: str | None = None,
        height: str | None = None,
        channel_map: str | None = "RGB",
        storage: str | None = "char",
        data: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Import pixel data from a byte-string to"""
        # Instance method: image.BaseImage.import_pixels
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if x is not None:
            kwargs["x"] = x
        if y is not None:
            kwargs["y"] = y
        if width is not None:
            kwargs["width"] = width
        if height is not None:
            kwargs["height"] = height
        if channel_map is not None:
            kwargs["channel_map"] = channel_map
        if storage is not None:
            kwargs["storage"] = storage
        if data is not None:
            kwargs["data"] = data
        method_attr = inspect.getattr_static(cls, "import_pixels")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "import_pixels")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "import_pixels")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_interlace_scheme(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`str`) The interlace used by the image."""
        # Instance method: image.BaseImage.interlace_scheme
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "interlace_scheme")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "interlace_scheme")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "interlace_scheme")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_interpolate_method(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`str`) The interpolation method of the image."""
        # Instance method: image.BaseImage.interpolate_method
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "interpolate_method")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "interpolate_method")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "interpolate_method")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_inverse_fourier_transform(
        phase: str,
        magnitude: str | None = "True",
        init_wand: str | None = None,
    ) -> str:
        """Applies the inverse of a discrete Fourier transform. The image stack"""
        # Instance method: image.BaseImage.inverse_fourier_transform
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        kwargs["phase"] = phase
        if magnitude is not None:
            kwargs["magnitude"] = magnitude
        method_attr = inspect.getattr_static(cls, "inverse_fourier_transform")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "inverse_fourier_transform")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "inverse_fourier_transform")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_iterator_first(
        init_wand: str | None = None,
    ) -> str:
        """Sets the internal image-stack iterator to the first image."""
        # Instance method: image.BaseImage.iterator_first
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "iterator_first")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "iterator_first")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "iterator_first")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_iterator_get(
        init_wand: str | None = None,
    ) -> str:
        """Returns the position of the internal image-stack index."""
        # Instance method: image.BaseImage.iterator_get
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "iterator_get")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "iterator_get")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "iterator_get")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_iterator_last(
        init_wand: str | None = None,
    ) -> str:
        """Sets the internal image-stack iterator to the last image."""
        # Instance method: image.BaseImage.iterator_last
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "iterator_last")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "iterator_last")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "iterator_last")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_iterator_length(
        init_wand: str | None = None,
    ) -> str:
        """Get the count of images in the image-stack."""
        # Instance method: image.BaseImage.iterator_length
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "iterator_length")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "iterator_length")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "iterator_length")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_iterator_next(
        init_wand: str | None = None,
    ) -> str:
        """Steps the image-stack index forward by one"""
        # Instance method: image.BaseImage.iterator_next
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "iterator_next")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "iterator_next")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "iterator_next")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_iterator_previous(
        init_wand: str | None = None,
    ) -> str:
        """Steps the image-stack index back by one."""
        # Instance method: image.BaseImage.iterator_previous
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "iterator_previous")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "iterator_previous")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "iterator_previous")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_iterator_reset(
        init_wand: str | None = None,
    ) -> str:
        """Reset internal image-stack iterator. Useful for iterating over the"""
        # Instance method: image.BaseImage.iterator_reset
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "iterator_reset")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "iterator_reset")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "iterator_reset")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_iterator_set(
        index: str,
        init_wand: str | None = None,
    ) -> str:
        """Sets the index of the internal image-stack."""
        # Instance method: image.BaseImage.iterator_set
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        kwargs["index"] = index
        method_attr = inspect.getattr_static(cls, "iterator_set")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "iterator_set")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "iterator_set")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_kmeans(
        number_colors: str | None = None,
        max_iterations: str | None = "100",
        tolerance: str | None = "0.01",
        init_wand: str | None = None,
    ) -> str:
        """Reduces the number of colors in an image by applying the K-means"""
        # Instance method: image.BaseImage.kmeans
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if number_colors is not None:
            kwargs["number_colors"] = number_colors
        if max_iterations is not None:
            kwargs["max_iterations"] = max_iterations
        if tolerance is not None:
            kwargs["tolerance"] = tolerance
        method_attr = inspect.getattr_static(cls, "kmeans")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "kmeans")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "kmeans")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_kurtosis(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`numbers.Real`) The kurtosis of the image."""
        # Instance method: image.BaseImage.kurtosis
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "kurtosis")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "kurtosis")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "kurtosis")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_kurtosis_channel(
        channel: str | None = "default_channels",
        init_wand: str | None = None,
    ) -> str:
        """Calculates the kurtosis and skewness of the image."""
        # Instance method: image.BaseImage.kurtosis_channel
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if channel is not None:
            kwargs["channel"] = channel
        method_attr = inspect.getattr_static(cls, "kurtosis_channel")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "kurtosis_channel")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "kurtosis_channel")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_kuwahara(
        radius: str | None = "1.0",
        sigma: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Edge preserving noise reduction filter."""
        # Instance method: image.BaseImage.kuwahara
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if radius is not None:
            kwargs["radius"] = radius
        if sigma is not None:
            kwargs["sigma"] = sigma
        method_attr = inspect.getattr_static(cls, "kuwahara")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "kuwahara")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "kuwahara")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_label(
        text: str,
        left: str | None = None,
        top: str | None = None,
        font: str | None = None,
        gravity: str | None = None,
        background_color: str | None = "transparent",
        init_wand: str | None = None,
    ) -> str:
        """Writes a label ``text`` into the position on top of the existing"""
        # Instance method: image.BaseImage.label
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        kwargs["text"] = text
        if left is not None:
            kwargs["left"] = left
        if top is not None:
            kwargs["top"] = top
        if font is not None:
            kwargs["font"] = font
        if gravity is not None:
            kwargs["gravity"] = gravity
        if background_color is not None:
            kwargs["background_color"] = background_color
        method_attr = inspect.getattr_static(cls, "label")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "label")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "label")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_length_of_bytes(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`numbers.Integral`) The original size, in bytes,"""
        # Instance method: image.BaseImage.length_of_bytes
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "length_of_bytes")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "length_of_bytes")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "length_of_bytes")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_level(
        black: str | None = "0.0",
        white: str | None = None,
        gamma: str | None = "1.0",
        channel: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Adjusts the levels of an image by scaling the colors falling"""
        # Instance method: image.BaseImage.level
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if black is not None:
            kwargs["black"] = black
        if white is not None:
            kwargs["white"] = white
        if gamma is not None:
            kwargs["gamma"] = gamma
        if channel is not None:
            kwargs["channel"] = channel
        method_attr = inspect.getattr_static(cls, "level")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "level")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "level")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_level_colors(
        black_color: str,
        white_color: str,
        channel: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Maps given colors to "black" & "white" values."""
        # Instance method: image.BaseImage.level_colors
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        kwargs["black_color"] = black_color
        kwargs["white_color"] = white_color
        if channel is not None:
            kwargs["channel"] = channel
        method_attr = inspect.getattr_static(cls, "level_colors")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "level_colors")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "level_colors")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_levelize(
        black: str | None = "0.0",
        white: str | None = None,
        gamma: str | None = "1.0",
        channel: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Reverse of :meth:`level()`, this method compresses the range of"""
        # Instance method: image.BaseImage.levelize
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if black is not None:
            kwargs["black"] = black
        if white is not None:
            kwargs["white"] = white
        if gamma is not None:
            kwargs["gamma"] = gamma
        if channel is not None:
            kwargs["channel"] = channel
        method_attr = inspect.getattr_static(cls, "levelize")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "levelize")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "levelize")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_levelize_colors(
        black_color: str,
        white_color: str,
        channel: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Reverse of :meth:`level_colors()`, and creates a de-contrasting"""
        # Instance method: image.BaseImage.levelize_colors
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        kwargs["black_color"] = black_color
        kwargs["white_color"] = white_color
        if channel is not None:
            kwargs["channel"] = channel
        method_attr = inspect.getattr_static(cls, "levelize_colors")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "levelize_colors")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "levelize_colors")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_linear_stretch(
        black_point: str | None = "0.0",
        white_point: str | None = "1.0",
        init_wand: str | None = None,
    ) -> str:
        """Enhance saturation intensity of an image."""
        # Instance method: image.BaseImage.linear_stretch
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if black_point is not None:
            kwargs["black_point"] = black_point
        if white_point is not None:
            kwargs["white_point"] = white_point
        method_attr = inspect.getattr_static(cls, "linear_stretch")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "linear_stretch")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "linear_stretch")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_liquid_rescale(
        width: str,
        height: str,
        delta_x: str | None = "1",
        rigidity: str | None = "0",
        init_wand: str | None = None,
    ) -> str:
        """Rescales the image with `seam carving`_, also known as"""
        # Instance method: image.BaseImage.liquid_rescale
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        kwargs["width"] = width
        kwargs["height"] = height
        if delta_x is not None:
            kwargs["delta_x"] = delta_x
        if rigidity is not None:
            kwargs["rigidity"] = rigidity
        method_attr = inspect.getattr_static(cls, "liquid_rescale")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "liquid_rescale")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "liquid_rescale")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_local_contrast(
        radius: str | None = "10",
        strength: str | None = "12.5",
        init_wand: str | None = None,
    ) -> str:
        """Increase light-dark transitions within image."""
        # Instance method: image.BaseImage.local_contrast
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if radius is not None:
            kwargs["radius"] = radius
        if strength is not None:
            kwargs["strength"] = strength
        method_attr = inspect.getattr_static(cls, "local_contrast")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "local_contrast")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "local_contrast")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_loop(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`numbers.Integral`) Number of frame iterations."""
        # Instance method: image.BaseImage.loop
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "loop")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "loop")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "loop")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_magnify(
        init_wand: str | None = None,
    ) -> str:
        """Quickly double an image in size. This is a convenience method."""
        # Instance method: image.BaseImage.magnify
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "magnify")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "magnify")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "magnify")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_matte_color(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`wand.color.Color`) The color value of the matte channel."""
        # Instance method: image.BaseImage.matte_color
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "matte_color")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "matte_color")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "matte_color")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_maxima(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`numbers.Real`) The maximum quantum value within the image."""
        # Instance method: image.BaseImage.maxima
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "maxima")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "maxima")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "maxima")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_mean(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`numbers.Real`) The mean of the image, and have a value"""
        # Instance method: image.BaseImage.mean
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "mean")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "mean")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "mean")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_mean_channel(
        channel: str | None = "default_channels",
        init_wand: str | None = None,
    ) -> str:
        """Calculates the mean and standard deviation of the image."""
        # Instance method: image.BaseImage.mean_channel
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if channel is not None:
            kwargs["channel"] = channel
        method_attr = inspect.getattr_static(cls, "mean_channel")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "mean_channel")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "mean_channel")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_mean_shift(
        width: str,
        height: str,
        color_distance: str | None = "0.1",
        init_wand: str | None = None,
    ) -> str:
        """Recalculates pixel value by comparing neighboring pixels within a"""
        # Instance method: image.BaseImage.mean_shift
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        kwargs["width"] = width
        kwargs["height"] = height
        if color_distance is not None:
            kwargs["color_distance"] = color_distance
        method_attr = inspect.getattr_static(cls, "mean_shift")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "mean_shift")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "mean_shift")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_merge_layers(
        method: str,
        init_wand: str | None = None,
    ) -> str:
        """Composes all the image layers from the current given image onward"""
        # Instance method: image.BaseImage.merge_layers
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        kwargs["method"] = method
        method_attr = inspect.getattr_static(cls, "merge_layers")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "merge_layers")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "merge_layers")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_minima(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`numbers.Real`) The minimum quantum value within the image."""
        # Instance method: image.BaseImage.minima
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "minima")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "minima")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "minima")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_minimum_bounding_box(
        orientation: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Find the minimum bounding box within the image. Use"""
        # Instance method: image.BaseImage.minimum_bounding_box
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if orientation is not None:
            kwargs["orientation"] = orientation
        method_attr = inspect.getattr_static(cls, "minimum_bounding_box")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "minimum_bounding_box")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "minimum_bounding_box")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_mode(
        width: str,
        height: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Replace each pixel with the mathematical mode of the neighboring"""
        # Instance method: image.BaseImage.mode
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        kwargs["width"] = width
        if height is not None:
            kwargs["height"] = height
        method_attr = inspect.getattr_static(cls, "mode")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "mode")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "mode")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_modulate(
        brightness: str | None = "100.0",
        saturation: str | None = "100.0",
        hue: str | None = "100.0",
        init_wand: str | None = None,
    ) -> str:
        """Changes the brightness, saturation and hue of an image."""
        # Instance method: image.BaseImage.modulate
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if brightness is not None:
            kwargs["brightness"] = brightness
        if saturation is not None:
            kwargs["saturation"] = saturation
        if hue is not None:
            kwargs["hue"] = hue
        method_attr = inspect.getattr_static(cls, "modulate")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "modulate")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "modulate")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_morphology(
        method: str | None = None,
        kernel: str | None = None,
        iterations: str | None = "1",
        channel: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Manipulate pixels based on the shape of neighboring pixels."""
        # Instance method: image.BaseImage.morphology
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if method is not None:
            kwargs["method"] = method
        if kernel is not None:
            kwargs["kernel"] = kernel
        if iterations is not None:
            kwargs["iterations"] = iterations
        if channel is not None:
            kwargs["channel"] = channel
        method_attr = inspect.getattr_static(cls, "morphology")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "morphology")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "morphology")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_motion_blur(
        radius: str | None = "0.0",
        sigma: str | None = "0.0",
        angle: str | None = "0.0",
        channel: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Apply a Gaussian blur along an ``angle`` direction. This"""
        # Instance method: image.BaseImage.motion_blur
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if radius is not None:
            kwargs["radius"] = radius
        if sigma is not None:
            kwargs["sigma"] = sigma
        if angle is not None:
            kwargs["angle"] = angle
        if channel is not None:
            kwargs["channel"] = channel
        method_attr = inspect.getattr_static(cls, "motion_blur")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "motion_blur")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "motion_blur")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_negate(
        grayscale: str | None = "False",
        channel: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Negate the colors in the reference image."""
        # Instance method: image.BaseImage.negate
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if grayscale is not None:
            kwargs["grayscale"] = grayscale
        if channel is not None:
            kwargs["channel"] = channel
        method_attr = inspect.getattr_static(cls, "negate")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "negate")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "negate")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_noise(
        noise_type: str | None = "uniform",
        attenuate: str | None = "1.0",
        channel: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Adds noise to image."""
        # Instance method: image.BaseImage.noise
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if noise_type is not None:
            kwargs["noise_type"] = noise_type
        if attenuate is not None:
            kwargs["attenuate"] = attenuate
        if channel is not None:
            kwargs["channel"] = channel
        method_attr = inspect.getattr_static(cls, "noise")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "noise")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "noise")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_normalize(
        channel: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Normalize color channels."""
        # Instance method: image.BaseImage.normalize
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if channel is not None:
            kwargs["channel"] = channel
        method_attr = inspect.getattr_static(cls, "normalize")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "normalize")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "normalize")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_oil_paint(
        radius: str | None = "0.0",
        sigma: str | None = "0.0",
        init_wand: str | None = None,
    ) -> str:
        """Simulates an oil painting by replace each pixel with most frequent"""
        # Instance method: image.BaseImage.oil_paint
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if radius is not None:
            kwargs["radius"] = radius
        if sigma is not None:
            kwargs["sigma"] = sigma
        method_attr = inspect.getattr_static(cls, "oil_paint")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "oil_paint")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "oil_paint")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_opaque_paint(
        target: str | None = None,
        fill: str | None = None,
        fuzz: str | None = "0.0",
        invert: str | None = "False",
        channel: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Replace any color that matches ``target`` with ``fill``. Use"""
        # Instance method: image.BaseImage.opaque_paint
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if target is not None:
            kwargs["target"] = target
        if fill is not None:
            kwargs["fill"] = fill
        if fuzz is not None:
            kwargs["fuzz"] = fuzz
        if invert is not None:
            kwargs["invert"] = invert
        if channel is not None:
            kwargs["channel"] = channel
        method_attr = inspect.getattr_static(cls, "opaque_paint")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "opaque_paint")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "opaque_paint")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_optimize_layers(
        init_wand: str | None = None,
    ) -> str:
        """Attempts to crop each frame to the smallest image without altering"""
        # Instance method: image.BaseImage.optimize_layers
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "optimize_layers")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "optimize_layers")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "optimize_layers")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_optimize_transparency(
        init_wand: str | None = None,
    ) -> str:
        """Iterates over frames, and sets transparent values for each"""
        # Instance method: image.BaseImage.optimize_transparency
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "optimize_transparency")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "optimize_transparency")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "optimize_transparency")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_ordered_dither(
        threshold_map: str | None = "threshold",
        channel: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Executes a ordered-based dither operations based on predetermined"""
        # Instance method: image.BaseImage.ordered_dither
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if threshold_map is not None:
            kwargs["threshold_map"] = threshold_map
        if channel is not None:
            kwargs["channel"] = channel
        method_attr = inspect.getattr_static(cls, "ordered_dither")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "ordered_dither")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "ordered_dither")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_orientation(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`str`) The image orientation.  It's a string from"""
        # Instance method: image.BaseImage.orientation
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "orientation")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "orientation")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "orientation")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_page(
        init_wand: str | None = None,
    ) -> str:
        """The dimensions and offset of this Wand's page as a 4-tuple:"""
        # Instance method: image.BaseImage.page
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "page")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "page")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "page")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_page_height(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`numbers.Integral`) The height of the page for this wand."""
        # Instance method: image.BaseImage.page_height
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "page_height")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "page_height")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "page_height")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_page_width(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`numbers.Integral`) The width of the page for this wand."""
        # Instance method: image.BaseImage.page_width
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "page_width")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "page_width")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "page_width")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_page_x(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`numbers.Integral`) The X-offset of the page for this wand."""
        # Instance method: image.BaseImage.page_x
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "page_x")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "page_x")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "page_x")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_page_y(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`numbers.Integral`) The Y-offset of the page for this wand."""
        # Instance method: image.BaseImage.page_y
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "page_y")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "page_y")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "page_y")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_parse_meta_geometry(
        geometry: str,
        init_wand: str | None = None,
    ) -> str:
        """Helper method to translate geometry format, and calculate"""
        # Instance method: image.BaseImage.parse_meta_geometry
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        kwargs["geometry"] = geometry
        method_attr = inspect.getattr_static(cls, "parse_meta_geometry")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "parse_meta_geometry")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "parse_meta_geometry")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_percent_escape(
        string_format: str,
        init_wand: str | None = None,
    ) -> str:
        """Convenience method that expands ImageMagick's `Percent Escape`_"""
        # Instance method: image.BaseImage.percent_escape
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        kwargs["string_format"] = string_format
        method_attr = inspect.getattr_static(cls, "percent_escape")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "percent_escape")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "percent_escape")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_polaroid(
        angle: str | None = "0.0",
        caption: str | None = None,
        font: str | None = None,
        method: str | None = "undefined",
        init_wand: str | None = None,
    ) -> str:
        """Creates a special effect simulating a Polaroid photo."""
        # Instance method: image.BaseImage.polaroid
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if angle is not None:
            kwargs["angle"] = angle
        if caption is not None:
            kwargs["caption"] = caption
        if font is not None:
            kwargs["font"] = font
        if method is not None:
            kwargs["method"] = method
        method_attr = inspect.getattr_static(cls, "polaroid")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "polaroid")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "polaroid")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_polynomial(
        arguments: str,
        init_wand: str | None = None,
    ) -> str:
        """Replace image with the sum of all images in a sequence by"""
        # Instance method: image.BaseImage.polynomial
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        kwargs["arguments"] = arguments
        method_attr = inspect.getattr_static(cls, "polynomial")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "polynomial")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "polynomial")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_posterize(
        levels: str | None = None,
        dither: str | None = "no",
        init_wand: str | None = None,
    ) -> str:
        """Reduce color levels per channel."""
        # Instance method: image.BaseImage.posterize
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if levels is not None:
            kwargs["levels"] = levels
        if dither is not None:
            kwargs["dither"] = dither
        method_attr = inspect.getattr_static(cls, "posterize")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "posterize")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "posterize")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_quantize(
        number_colors: str,
        colorspace_type: str | None = "undefined",
        treedepth: str | None = "0",
        dither: str | None = "False",
        measure_error: str | None = "False",
        init_wand: str | None = None,
    ) -> str:
        """`quantize` analyzes the colors within a sequence of images and"""
        # Instance method: image.BaseImage.quantize
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        kwargs["number_colors"] = number_colors
        if colorspace_type is not None:
            kwargs["colorspace_type"] = colorspace_type
        if treedepth is not None:
            kwargs["treedepth"] = treedepth
        if dither is not None:
            kwargs["dither"] = dither
        if measure_error is not None:
            kwargs["measure_error"] = measure_error
        method_attr = inspect.getattr_static(cls, "quantize")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "quantize")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "quantize")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_quantum_range(
        init_wand: str | None = None,
    ) -> str:
        """(`:class:`numbers.Integral`) The maximum value of a color"""
        # Instance method: image.BaseImage.quantum_range
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "quantum_range")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "quantum_range")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "quantum_range")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_random_threshold(
        low: str | None = "0.0",
        high: str | None = "1.0",
        channel: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Performs a random dither to force a pixel into a binary black &"""
        # Instance method: image.BaseImage.random_threshold
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if low is not None:
            kwargs["low"] = low
        if high is not None:
            kwargs["high"] = high
        if channel is not None:
            kwargs["channel"] = channel
        method_attr = inspect.getattr_static(cls, "random_threshold")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "random_threshold")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "random_threshold")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_range_channel(
        channel: str | None = "default_channels",
        init_wand: str | None = None,
    ) -> str:
        """Calculate the minimum and maximum of quantum values in image."""
        # Instance method: image.BaseImage.range_channel
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if channel is not None:
            kwargs["channel"] = channel
        method_attr = inspect.getattr_static(cls, "range_channel")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "range_channel")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "range_channel")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_range_threshold(
        low_black: str | None = "0.0",
        low_white: str | None = None,
        high_white: str | None = None,
        high_black: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Applies soft & hard thresholding."""
        # Instance method: image.BaseImage.range_threshold
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if low_black is not None:
            kwargs["low_black"] = low_black
        if low_white is not None:
            kwargs["low_white"] = low_white
        if high_white is not None:
            kwargs["high_white"] = high_white
        if high_black is not None:
            kwargs["high_black"] = high_black
        method_attr = inspect.getattr_static(cls, "range_threshold")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "range_threshold")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "range_threshold")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_read_mask(
        clip_mask: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Sets the read mask where the gray values of the clip mask"""
        # Instance method: image.BaseImage.read_mask
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if clip_mask is not None:
            kwargs["clip_mask"] = clip_mask
        method_attr = inspect.getattr_static(cls, "read_mask")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "read_mask")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "read_mask")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_red_primary(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`tuple`) The chromatic red primary point for the image."""
        # Instance method: image.BaseImage.red_primary
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "red_primary")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "red_primary")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "red_primary")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_region(
        width: str | None = None,
        height: str | None = None,
        x: str | None = None,
        y: str | None = None,
        gravity: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Extract an area of the image. This is the same as :meth:`crop`,"""
        # Instance method: image.BaseImage.region
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if width is not None:
            kwargs["width"] = width
        if height is not None:
            kwargs["height"] = height
        if x is not None:
            kwargs["x"] = x
        if y is not None:
            kwargs["y"] = y
        if gravity is not None:
            kwargs["gravity"] = gravity
        method_attr = inspect.getattr_static(cls, "region")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "region")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "region")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_remap(
        affinity: str | None = None,
        method: str | None = "no",
        init_wand: str | None = None,
    ) -> str:
        """Rebuild image palette with closest color from given affinity image."""
        # Instance method: image.BaseImage.remap
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if affinity is not None:
            kwargs["affinity"] = affinity
        if method is not None:
            kwargs["method"] = method
        method_attr = inspect.getattr_static(cls, "remap")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "remap")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "remap")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_rendering_intent(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`str`) PNG rendering intent. See"""
        # Instance method: image.BaseImage.rendering_intent
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "rendering_intent")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "rendering_intent")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "rendering_intent")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_resample(
        x_res: str | None = None,
        y_res: str | None = None,
        filter: str | None = "undefined",
        blur: str | None = "1",
        init_wand: str | None = None,
    ) -> str:
        """Adjust the number of pixels in an image so that when displayed at"""
        # Instance method: image.BaseImage.resample
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if x_res is not None:
            kwargs["x_res"] = x_res
        if y_res is not None:
            kwargs["y_res"] = y_res
        if filter is not None:
            kwargs["filter"] = filter
        if blur is not None:
            kwargs["blur"] = blur
        method_attr = inspect.getattr_static(cls, "resample")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "resample")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "resample")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_reset_coords(
        init_wand: str | None = None,
    ) -> str:
        """Reset the coordinate frame of the image so to the upper-left corner"""
        # Instance method: image.BaseImage.reset_coords
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "reset_coords")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "reset_coords")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "reset_coords")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_reset_sequence(
        init_wand: str | None = None,
    ) -> str:
        """Abstract method prototype."""
        # Instance method: image.BaseImage.reset_sequence
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "reset_sequence")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "reset_sequence")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "reset_sequence")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_resize(
        width: str | None = None,
        height: str | None = None,
        filter: str | None = "undefined",
        blur: str | None = "1",
        init_wand: str | None = None,
    ) -> str:
        """Resizes the image."""
        # Instance method: image.BaseImage.resize
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if width is not None:
            kwargs["width"] = width
        if height is not None:
            kwargs["height"] = height
        if filter is not None:
            kwargs["filter"] = filter
        if blur is not None:
            kwargs["blur"] = blur
        method_attr = inspect.getattr_static(cls, "resize")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "resize")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "resize")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_resolution(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`tuple`) Resolution of this image."""
        # Instance method: image.BaseImage.resolution
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "resolution")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "resolution")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "resolution")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_roll(
        x: str | None = "0",
        y: str | None = "0",
        init_wand: str | None = None,
    ) -> str:
        """Shifts all pixels over by an X/Y offset."""
        # Instance method: image.BaseImage.roll
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if x is not None:
            kwargs["x"] = x
        if y is not None:
            kwargs["y"] = y
        method_attr = inspect.getattr_static(cls, "roll")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "roll")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "roll")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_rotate(
        degree: str,
        background: str | None = None,
        reset_coords: str | None = "True",
        init_wand: str | None = None,
    ) -> str:
        """Rotates the image right.  It takes a ``background`` color"""
        # Instance method: image.BaseImage.rotate
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        kwargs["degree"] = degree
        if background is not None:
            kwargs["background"] = background
        if reset_coords is not None:
            kwargs["reset_coords"] = reset_coords
        method_attr = inspect.getattr_static(cls, "rotate")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "rotate")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "rotate")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_rotational_blur(
        angle: str | None = "0.0",
        channel: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Blur an image in a radius around the center of an image."""
        # Instance method: image.BaseImage.rotational_blur
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if angle is not None:
            kwargs["angle"] = angle
        if channel is not None:
            kwargs["channel"] = channel
        method_attr = inspect.getattr_static(cls, "rotational_blur")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "rotational_blur")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "rotational_blur")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_sample(
        width: str | None = None,
        height: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Resizes the image by sampling the pixels.  It's basically quicker"""
        # Instance method: image.BaseImage.sample
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if width is not None:
            kwargs["width"] = width
        if height is not None:
            kwargs["height"] = height
        method_attr = inspect.getattr_static(cls, "sample")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "sample")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "sample")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_sampling_factors(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`tuple`) Factors used in sampling data streams."""
        # Instance method: image.BaseImage.sampling_factors
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "sampling_factors")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "sampling_factors")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "sampling_factors")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_scale(
        columns: str | None = "1",
        rows: str | None = "1",
        init_wand: str | None = None,
    ) -> str:
        """Increase image size by scaling each pixel value by given ``columns``"""
        # Instance method: image.BaseImage.scale
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if columns is not None:
            kwargs["columns"] = columns
        if rows is not None:
            kwargs["rows"] = rows
        method_attr = inspect.getattr_static(cls, "scale")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "scale")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "scale")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_scene(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`numbers.Integral`) The scene number of the current frame"""
        # Instance method: image.BaseImage.scene
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "scene")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "scene")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "scene")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_seed(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`numbers.Integral`) The seed for random number generator."""
        # Instance method: image.BaseImage.seed
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "seed")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "seed")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "seed")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_selective_blur(
        radius: str | None = "0.0",
        sigma: str | None = "0.0",
        threshold: str | None = "0.0",
        channel: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Blur an image within a given threshold."""
        # Instance method: image.BaseImage.selective_blur
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if radius is not None:
            kwargs["radius"] = radius
        if sigma is not None:
            kwargs["sigma"] = sigma
        if threshold is not None:
            kwargs["threshold"] = threshold
        if channel is not None:
            kwargs["channel"] = channel
        method_attr = inspect.getattr_static(cls, "selective_blur")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "selective_blur")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "selective_blur")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_sepia_tone(
        threshold: str | None = "0.8",
        init_wand: str | None = None,
    ) -> str:
        """Creates a Sepia Tone special effect similar to a darkroom chemical"""
        # Instance method: image.BaseImage.sepia_tone
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if threshold is not None:
            kwargs["threshold"] = threshold
        method_attr = inspect.getattr_static(cls, "sepia_tone")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "sepia_tone")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "sepia_tone")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_shade(
        gray: str | None = "False",
        azimuth: str | None = "0.0",
        elevation: str | None = "0.0",
        init_wand: str | None = None,
    ) -> str:
        """Creates a 3D effect by simulating a light from an"""
        # Instance method: image.BaseImage.shade
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if gray is not None:
            kwargs["gray"] = gray
        if azimuth is not None:
            kwargs["azimuth"] = azimuth
        if elevation is not None:
            kwargs["elevation"] = elevation
        method_attr = inspect.getattr_static(cls, "shade")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "shade")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "shade")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_shadow(
        alpha: str | None = "0.0",
        sigma: str | None = "0.0",
        x: str | None = "0",
        y: str | None = "0",
        init_wand: str | None = None,
    ) -> str:
        """Generates an image shadow."""
        # Instance method: image.BaseImage.shadow
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if alpha is not None:
            kwargs["alpha"] = alpha
        if sigma is not None:
            kwargs["sigma"] = sigma
        if x is not None:
            kwargs["x"] = x
        if y is not None:
            kwargs["y"] = y
        method_attr = inspect.getattr_static(cls, "shadow")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "shadow")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "shadow")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_sharpen(
        radius: str | None = "0.0",
        sigma: str | None = "0.0",
        channel: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Applies a gaussian effect to enhance the sharpness of an"""
        # Instance method: image.BaseImage.sharpen
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if radius is not None:
            kwargs["radius"] = radius
        if sigma is not None:
            kwargs["sigma"] = sigma
        if channel is not None:
            kwargs["channel"] = channel
        method_attr = inspect.getattr_static(cls, "sharpen")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "sharpen")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "sharpen")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_shave(
        columns: str | None = "0",
        rows: str | None = "0",
        init_wand: str | None = None,
    ) -> str:
        """Remove pixels from the edges."""
        # Instance method: image.BaseImage.shave
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if columns is not None:
            kwargs["columns"] = columns
        if rows is not None:
            kwargs["rows"] = rows
        method_attr = inspect.getattr_static(cls, "shave")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "shave")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "shave")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_shear(
        background: str | None = "WHITE",
        x: str | None = "0.0",
        y: str | None = "0.0",
        init_wand: str | None = None,
    ) -> str:
        """Shears the image to create a parallelogram, and fill the space"""
        # Instance method: image.BaseImage.shear
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if background is not None:
            kwargs["background"] = background
        if x is not None:
            kwargs["x"] = x
        if y is not None:
            kwargs["y"] = y
        method_attr = inspect.getattr_static(cls, "shear")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "shear")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "shear")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_sigmoidal_contrast(
        sharpen: str | None = "True",
        strength: str | None = "0.0",
        midpoint: str | None = "0.0",
        channel: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Modifies the contrast of the image by applying non-linear sigmoidal"""
        # Instance method: image.BaseImage.sigmoidal_contrast
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if sharpen is not None:
            kwargs["sharpen"] = sharpen
        if strength is not None:
            kwargs["strength"] = strength
        if midpoint is not None:
            kwargs["midpoint"] = midpoint
        if channel is not None:
            kwargs["channel"] = channel
        method_attr = inspect.getattr_static(cls, "sigmoidal_contrast")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "sigmoidal_contrast")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "sigmoidal_contrast")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_signature(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`str`) The SHA-256 message digest for the image pixel"""
        # Instance method: image.BaseImage.signature
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "signature")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "signature")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "signature")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_similarity(
        reference: str,
        threshold: str | None = "0.0",
        metric: str | None = "undefined",
        init_wand: str | None = None,
    ) -> str:
        """Scan image for best matching ``reference`` image, and"""
        # Instance method: image.BaseImage.similarity
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        kwargs["reference"] = reference
        if threshold is not None:
            kwargs["threshold"] = threshold
        if metric is not None:
            kwargs["metric"] = metric
        method_attr = inspect.getattr_static(cls, "similarity")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "similarity")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "similarity")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_size(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`tuple`) The pair of (:attr:`width`, :attr:`height`)."""
        # Instance method: image.BaseImage.size
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "size")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "size")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "size")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_sketch(
        radius: str | None = "0.0",
        sigma: str | None = "0.0",
        angle: str | None = "0.0",
        init_wand: str | None = None,
    ) -> str:
        """Simulates a pencil sketch effect. For best results, ``radius``"""
        # Instance method: image.BaseImage.sketch
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if radius is not None:
            kwargs["radius"] = radius
        if sigma is not None:
            kwargs["sigma"] = sigma
        if angle is not None:
            kwargs["angle"] = angle
        method_attr = inspect.getattr_static(cls, "sketch")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "sketch")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "sketch")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_skewness(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`numbers.Real`) The skewness of the image."""
        # Instance method: image.BaseImage.skewness
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "skewness")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "skewness")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "skewness")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_smush(
        stacked: str | None = "False",
        offset: str | None = "0",
        init_wand: str | None = None,
    ) -> str:
        """Appends all images together. Similar behavior to :meth:`concat`,"""
        # Instance method: image.BaseImage.smush
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if stacked is not None:
            kwargs["stacked"] = stacked
        if offset is not None:
            kwargs["offset"] = offset
        method_attr = inspect.getattr_static(cls, "smush")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "smush")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "smush")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_solarize(
        threshold: str | None = "0.0",
        channel: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Simulates extreme overexposure."""
        # Instance method: image.BaseImage.solarize
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if threshold is not None:
            kwargs["threshold"] = threshold
        if channel is not None:
            kwargs["channel"] = channel
        method_attr = inspect.getattr_static(cls, "solarize")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "solarize")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "solarize")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_splice(
        width: str | None = None,
        height: str | None = None,
        x: str | None = None,
        y: str | None = None,
        gravity: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Partitions image by splicing a ``width`` x ``height`` rectangle at"""
        # Instance method: image.BaseImage.splice
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if width is not None:
            kwargs["width"] = width
        if height is not None:
            kwargs["height"] = height
        if x is not None:
            kwargs["x"] = x
        if y is not None:
            kwargs["y"] = y
        if gravity is not None:
            kwargs["gravity"] = gravity
        method_attr = inspect.getattr_static(cls, "splice")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "splice")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "splice")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_spread(
        radius: str | None = "0.0",
        method: str | None = "undefined",
        init_wand: str | None = None,
    ) -> str:
        """Randomly displace pixels within a defined radius."""
        # Instance method: image.BaseImage.spread
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if radius is not None:
            kwargs["radius"] = radius
        if method is not None:
            kwargs["method"] = method
        method_attr = inspect.getattr_static(cls, "spread")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "spread")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "spread")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_standard_deviation(
        init_wand: str | None = None,
    ) -> str:
        """(:class:`numbers.Real`) The standard deviation of the image."""
        # Instance method: image.BaseImage.standard_deviation
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "standard_deviation")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "standard_deviation")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "standard_deviation")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_statistic(
        stat: str | None = "undefined",
        width: str | None = None,
        height: str | None = None,
        channel: str | None = None,
        init_wand: str | None = None,
    ) -> str:
        """Replace each pixel with the statistic results from neighboring pixel"""
        # Instance method: image.BaseImage.statistic
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        if stat is not None:
            kwargs["stat"] = stat
        if width is not None:
            kwargs["width"] = width
        if height is not None:
            kwargs["height"] = height
        if channel is not None:
            kwargs["channel"] = channel
        method_attr = inspect.getattr_static(cls, "statistic")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "statistic")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "statistic")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_stegano(
        watermark: str,
        offset: str | None = "0",
        init_wand: str | None = None,
    ) -> str:
        """Hide a digital watermark of an image within the image."""
        # Instance method: image.BaseImage.stegano
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        kwargs["watermark"] = watermark
        if offset is not None:
            kwargs["offset"] = offset
        method_attr = inspect.getattr_static(cls, "stegano")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "stegano")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "stegano")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_strip(
        init_wand: str | None = None,
    ) -> str:
        """Strips an image of all profiles and comments."""
        # Instance method: image.BaseImage.strip
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "strip")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "strip")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "strip")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def base_image_stroke_color(
        init_wand: str | None = None,
    ) -> str:
        """Stroke color"""
        # Instance method: image.BaseImage.stroke_color
        _setup_import_path("/home/gabriele/.local/lib/python3.10/site-packages/wand")
        mod = _load_source_module("/home/gabriele/.local/lib/python3.10/site-packages/wand", "image")
        cls = getattr(mod, "BaseImage")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "stroke_color")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "stroke_color")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_wand is not None:
                init_kwargs["wand"] = init_wand
            instance = _get_or_create_instance(mod, "BaseImage", **init_kwargs)
            result = getattr(instance, "stroke_color")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

