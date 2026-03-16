"""parameter tools for click."""

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
    """Register parameter tools with the server."""

    @server.tool()
    async def parameter_add_to_parser(
        parser: str,
        ctx: str,
    ) -> str:
        """Add to parser"""
        # Instance method: core.Parameter.add_to_parser
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Parameter")
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
            instance = _get_or_create_instance(mod, "Parameter", **init_kwargs)
            result = getattr(instance, "add_to_parser")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def parameter_consume_value(
        ctx: str,
        opts: str,
    ) -> str:
        """Returns the parameter value produced by the parser."""
        # Instance method: core.Parameter.consume_value
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Parameter")
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
            instance = _get_or_create_instance(mod, "Parameter", **init_kwargs)
            result = getattr(instance, "consume_value")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def parameter_get_default(
        ctx: str,
        call: str | None = "True",
    ) -> str:
        """Get default"""
        # Instance method: core.Parameter.get_default
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Parameter")
        kwargs = {}
        kwargs["ctx"] = ctx
        if call is not None:
            kwargs["call"] = call
        method_attr = inspect.getattr_static(cls, "get_default")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "get_default")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            instance = _get_or_create_instance(mod, "Parameter", **init_kwargs)
            result = getattr(instance, "get_default")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def parameter_get_error_hint(
        ctx: str,
    ) -> str:
        """Get a stringified version of the param for use in error messages to"""
        # Instance method: core.Parameter.get_error_hint
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Parameter")
        kwargs = {}
        kwargs["ctx"] = ctx
        method_attr = inspect.getattr_static(cls, "get_error_hint")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "get_error_hint")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            instance = _get_or_create_instance(mod, "Parameter", **init_kwargs)
            result = getattr(instance, "get_error_hint")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def parameter_get_help_record(
        ctx: str,
    ) -> str:
        """Get help record"""
        # Instance method: core.Parameter.get_help_record
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Parameter")
        kwargs = {}
        kwargs["ctx"] = ctx
        method_attr = inspect.getattr_static(cls, "get_help_record")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "get_help_record")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            instance = _get_or_create_instance(mod, "Parameter", **init_kwargs)
            result = getattr(instance, "get_help_record")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def parameter_get_usage_pieces(
        ctx: str,
    ) -> str:
        """Get usage pieces"""
        # Instance method: core.Parameter.get_usage_pieces
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Parameter")
        kwargs = {}
        kwargs["ctx"] = ctx
        method_attr = inspect.getattr_static(cls, "get_usage_pieces")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "get_usage_pieces")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            instance = _get_or_create_instance(mod, "Parameter", **init_kwargs)
            result = getattr(instance, "get_usage_pieces")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def parameter_handle_parse_result(
        ctx: str,
        opts: str,
        args: list,
    ) -> str:
        """Process the value produced by the parser from user input."""
        # Instance method: core.Parameter.handle_parse_result
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Parameter")
        kwargs = {}
        kwargs["ctx"] = ctx
        kwargs["opts"] = opts
        kwargs["args"] = args
        method_attr = inspect.getattr_static(cls, "handle_parse_result")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "handle_parse_result")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            instance = _get_or_create_instance(mod, "Parameter", **init_kwargs)
            result = getattr(instance, "handle_parse_result")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def parameter_human_readable_name(
    ) -> str:
        """Returns the human readable name of this parameter.  This is the"""
        # Instance method: core.Parameter.human_readable_name
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Parameter")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "human_readable_name")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "human_readable_name")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            instance = _get_or_create_instance(mod, "Parameter", **init_kwargs)
            result = getattr(instance, "human_readable_name")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def parameter_make_metavar(
        ctx: str,
    ) -> str:
        """Make metavar"""
        # Instance method: core.Parameter.make_metavar
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Parameter")
        kwargs = {}
        kwargs["ctx"] = ctx
        method_attr = inspect.getattr_static(cls, "make_metavar")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "make_metavar")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            instance = _get_or_create_instance(mod, "Parameter", **init_kwargs)
            result = getattr(instance, "make_metavar")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def parameter_process_value(
        ctx: str,
        value: str,
    ) -> str:
        """Process the value of this parameter:"""
        # Instance method: core.Parameter.process_value
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Parameter")
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
            instance = _get_or_create_instance(mod, "Parameter", **init_kwargs)
            result = getattr(instance, "process_value")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def parameter_resolve_envvar_value(
        ctx: str,
    ) -> str:
        """Returns the value found in the environment variable(s) attached to this"""
        # Instance method: core.Parameter.resolve_envvar_value
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Parameter")
        kwargs = {}
        kwargs["ctx"] = ctx
        method_attr = inspect.getattr_static(cls, "resolve_envvar_value")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "resolve_envvar_value")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            instance = _get_or_create_instance(mod, "Parameter", **init_kwargs)
            result = getattr(instance, "resolve_envvar_value")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def parameter_shell_complete(
        ctx: str,
        incomplete: str,
    ) -> str:
        """Return a list of completions for the incomplete value. If a"""
        # Instance method: core.Parameter.shell_complete
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Parameter")
        kwargs = {}
        kwargs["ctx"] = ctx
        kwargs["incomplete"] = incomplete
        method_attr = inspect.getattr_static(cls, "shell_complete")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "shell_complete")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            instance = _get_or_create_instance(mod, "Parameter", **init_kwargs)
            result = getattr(instance, "shell_complete")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def parameter_to_info_dict(
    ) -> str:
        """Gather information that could be useful for a tool generating"""
        # Instance method: core.Parameter.to_info_dict
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Parameter")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "to_info_dict")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "to_info_dict")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            instance = _get_or_create_instance(mod, "Parameter", **init_kwargs)
            result = getattr(instance, "to_info_dict")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def parameter_value_from_envvar(
        ctx: str,
    ) -> str:
        """Process the raw environment variable string for this parameter."""
        # Instance method: core.Parameter.value_from_envvar
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Parameter")
        kwargs = {}
        kwargs["ctx"] = ctx
        method_attr = inspect.getattr_static(cls, "value_from_envvar")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "value_from_envvar")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            instance = _get_or_create_instance(mod, "Parameter", **init_kwargs)
            result = getattr(instance, "value_from_envvar")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def parameter_value_is_missing(
        value: str,
    ) -> str:
        """A value is considered missing if:"""
        # Instance method: core.Parameter.value_is_missing
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Parameter")
        kwargs = {}
        kwargs["value"] = value
        method_attr = inspect.getattr_static(cls, "value_is_missing")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "value_is_missing")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            instance = _get_or_create_instance(mod, "Parameter", **init_kwargs)
            result = getattr(instance, "value_is_missing")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

