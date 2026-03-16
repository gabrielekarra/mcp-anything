"""bool_param_type tools for click."""

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
    """Register bool_param_type tools with the server."""

    @server.tool()
    async def bool_param_type_convert(
        value: str,
        param: str,
        ctx: str,
    ) -> str:
        """Convert"""
        # Instance method: types.BoolParamType.convert
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "types")
        cls = getattr(mod, "BoolParamType")
        kwargs = {}
        kwargs["value"] = value
        kwargs["param"] = param
        kwargs["ctx"] = ctx
        method_attr = inspect.getattr_static(cls, "convert")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "convert")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            instance = _get_or_create_instance(mod, "BoolParamType", **init_kwargs)
            result = getattr(instance, "convert")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def bool_param_type_str_to_bool(
        value: str,
    ) -> str:
        """Convert a string to a boolean value."""
        # Instance method: types.BoolParamType.str_to_bool
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "types")
        cls = getattr(mod, "BoolParamType")
        kwargs = {}
        kwargs["value"] = value
        method_attr = inspect.getattr_static(cls, "str_to_bool")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "str_to_bool")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            instance = _get_or_create_instance(mod, "BoolParamType", **init_kwargs)
            result = getattr(instance, "str_to_bool")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

