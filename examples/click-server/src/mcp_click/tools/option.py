"""option tools for click."""

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
    """Register option tools with the server."""

    @server.tool()
    async def option_add_to_parser(
        parser: str,
        ctx: str,
    ) -> str:
        """Add to parser"""
        # Instance method: core.Option.add_to_parser
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Option")
        kwargs = {}
        kwargs["parser"] = parser
        kwargs["ctx"] = ctx
        method_attr = inspect.getattr_static(cls, "add_to_parser")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "add_to_parser")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            instance = _get_or_create_instance(mod, "Option", **init_kwargs)
            result = getattr(instance, "add_to_parser")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def option_consume_value(
        ctx: str,
        opts: str,
    ) -> str:
        """For :class:`Option`, the value can be collected from an interactive prompt"""
        # Instance method: core.Option.consume_value
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Option")
        kwargs = {}
        kwargs["ctx"] = ctx
        kwargs["opts"] = opts
        method_attr = inspect.getattr_static(cls, "consume_value")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "consume_value")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            instance = _get_or_create_instance(mod, "Option", **init_kwargs)
            result = getattr(instance, "consume_value")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def option_get_error_hint(
        ctx: str,
    ) -> str:
        """Get error hint"""
        # Instance method: core.Option.get_error_hint
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Option")
        kwargs = {}
        kwargs["ctx"] = ctx
        method_attr = inspect.getattr_static(cls, "get_error_hint")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "get_error_hint")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            instance = _get_or_create_instance(mod, "Option", **init_kwargs)
            result = getattr(instance, "get_error_hint")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def option_get_help_extra(
        ctx: str,
    ) -> str:
        """Get help extra"""
        # Instance method: core.Option.get_help_extra
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Option")
        kwargs = {}
        kwargs["ctx"] = ctx
        method_attr = inspect.getattr_static(cls, "get_help_extra")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "get_help_extra")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            instance = _get_or_create_instance(mod, "Option", **init_kwargs)
            result = getattr(instance, "get_help_extra")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def option_process_value(
        ctx: str,
        value: str,
    ) -> str:
        """Process value"""
        # Instance method: core.Option.process_value
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Option")
        kwargs = {}
        kwargs["ctx"] = ctx
        kwargs["value"] = value
        method_attr = inspect.getattr_static(cls, "process_value")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "process_value")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            instance = _get_or_create_instance(mod, "Option", **init_kwargs)
            result = getattr(instance, "process_value")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def option_prompt_for_value(
        ctx: str,
    ) -> str:
        """This is an alternative flow that can be activated in the full"""
        # Instance method: core.Option.prompt_for_value
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Option")
        kwargs = {}
        kwargs["ctx"] = ctx
        method_attr = inspect.getattr_static(cls, "prompt_for_value")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "prompt_for_value")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            instance = _get_or_create_instance(mod, "Option", **init_kwargs)
            result = getattr(instance, "prompt_for_value")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def option_resolve_envvar_value(
        ctx: str,
    ) -> str:
        """:class:`Option` resolves its environment variable the same way as"""
        # Instance method: core.Option.resolve_envvar_value
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Option")
        kwargs = {}
        kwargs["ctx"] = ctx
        method_attr = inspect.getattr_static(cls, "resolve_envvar_value")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "resolve_envvar_value")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            instance = _get_or_create_instance(mod, "Option", **init_kwargs)
            result = getattr(instance, "resolve_envvar_value")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def option_to_info_dict(
    ) -> str:
        """.. versionchanged:: 8.3.0"""
        # Instance method: core.Option.to_info_dict
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Option")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "to_info_dict")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "to_info_dict")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            instance = _get_or_create_instance(mod, "Option", **init_kwargs)
            result = getattr(instance, "to_info_dict")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def option_value_from_envvar(
        ctx: str,
    ) -> str:
        """For :class:`Option`, this method processes the raw environment variable"""
        # Instance method: core.Option.value_from_envvar
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Option")
        kwargs = {}
        kwargs["ctx"] = ctx
        method_attr = inspect.getattr_static(cls, "value_from_envvar")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "value_from_envvar")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            instance = _get_or_create_instance(mod, "Option", **init_kwargs)
            result = getattr(instance, "value_from_envvar")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

