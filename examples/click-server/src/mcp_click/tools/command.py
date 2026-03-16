"""command tools for click."""

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
    """Register command tools with the server."""

    @server.tool()
    async def command_collect_usage_pieces(
        ctx: str,
        init_name: str | None = None,
    ) -> str:
        """Returns all the pieces that go into the usage line and returns"""
        # Instance method: core.Command.collect_usage_pieces
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Command")
        kwargs = {}
        kwargs["ctx"] = ctx
        method_attr = inspect.getattr_static(cls, "collect_usage_pieces")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "collect_usage_pieces")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_name is not None:
                init_kwargs["name"] = init_name
            instance = _get_or_create_instance(mod, "Command", **init_kwargs)
            result = getattr(instance, "collect_usage_pieces")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def command_format_epilog(
        ctx: str,
        formatter: str,
        init_name: str | None = None,
    ) -> str:
        """Writes the epilog into the formatter if it exists."""
        # Instance method: core.Command.format_epilog
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Command")
        kwargs = {}
        kwargs["ctx"] = ctx
        kwargs["formatter"] = formatter
        method_attr = inspect.getattr_static(cls, "format_epilog")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "format_epilog")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_name is not None:
                init_kwargs["name"] = init_name
            instance = _get_or_create_instance(mod, "Command", **init_kwargs)
            result = getattr(instance, "format_epilog")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def command_format_help(
        ctx: str,
        formatter: str,
        init_name: str | None = None,
    ) -> str:
        """Writes the help into the formatter if it exists."""
        # Instance method: core.Command.format_help
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Command")
        kwargs = {}
        kwargs["ctx"] = ctx
        kwargs["formatter"] = formatter
        method_attr = inspect.getattr_static(cls, "format_help")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "format_help")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_name is not None:
                init_kwargs["name"] = init_name
            instance = _get_or_create_instance(mod, "Command", **init_kwargs)
            result = getattr(instance, "format_help")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def command_format_help_text(
        ctx: str,
        formatter: str,
        init_name: str | None = None,
    ) -> str:
        """Writes the help text to the formatter if it exists."""
        # Instance method: core.Command.format_help_text
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Command")
        kwargs = {}
        kwargs["ctx"] = ctx
        kwargs["formatter"] = formatter
        method_attr = inspect.getattr_static(cls, "format_help_text")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "format_help_text")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_name is not None:
                init_kwargs["name"] = init_name
            instance = _get_or_create_instance(mod, "Command", **init_kwargs)
            result = getattr(instance, "format_help_text")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def command_format_options(
        ctx: str,
        formatter: str,
        init_name: str | None = None,
    ) -> str:
        """Writes all the options into the formatter if they exist."""
        # Instance method: core.Command.format_options
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Command")
        kwargs = {}
        kwargs["ctx"] = ctx
        kwargs["formatter"] = formatter
        method_attr = inspect.getattr_static(cls, "format_options")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "format_options")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_name is not None:
                init_kwargs["name"] = init_name
            instance = _get_or_create_instance(mod, "Command", **init_kwargs)
            result = getattr(instance, "format_options")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def command_format_usage(
        ctx: str,
        formatter: str,
        init_name: str | None = None,
    ) -> str:
        """Writes the usage line into the formatter."""
        # Instance method: core.Command.format_usage
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Command")
        kwargs = {}
        kwargs["ctx"] = ctx
        kwargs["formatter"] = formatter
        method_attr = inspect.getattr_static(cls, "format_usage")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "format_usage")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_name is not None:
                init_kwargs["name"] = init_name
            instance = _get_or_create_instance(mod, "Command", **init_kwargs)
            result = getattr(instance, "format_usage")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def command_get_help(
        ctx: str,
        init_name: str | None = None,
    ) -> str:
        """Formats the help into a string and returns it."""
        # Instance method: core.Command.get_help
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Command")
        kwargs = {}
        kwargs["ctx"] = ctx
        method_attr = inspect.getattr_static(cls, "get_help")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "get_help")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_name is not None:
                init_kwargs["name"] = init_name
            instance = _get_or_create_instance(mod, "Command", **init_kwargs)
            result = getattr(instance, "get_help")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def command_get_help_option(
        ctx: str,
        init_name: str | None = None,
    ) -> str:
        """Returns the help option object."""
        # Instance method: core.Command.get_help_option
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Command")
        kwargs = {}
        kwargs["ctx"] = ctx
        method_attr = inspect.getattr_static(cls, "get_help_option")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "get_help_option")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_name is not None:
                init_kwargs["name"] = init_name
            instance = _get_or_create_instance(mod, "Command", **init_kwargs)
            result = getattr(instance, "get_help_option")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def command_get_help_option_names(
        ctx: str,
        init_name: str | None = None,
    ) -> str:
        """Returns the names for the help option."""
        # Instance method: core.Command.get_help_option_names
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Command")
        kwargs = {}
        kwargs["ctx"] = ctx
        method_attr = inspect.getattr_static(cls, "get_help_option_names")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "get_help_option_names")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_name is not None:
                init_kwargs["name"] = init_name
            instance = _get_or_create_instance(mod, "Command", **init_kwargs)
            result = getattr(instance, "get_help_option_names")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def command_get_params(
        ctx: str,
        init_name: str | None = None,
    ) -> str:
        """Get params"""
        # Instance method: core.Command.get_params
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Command")
        kwargs = {}
        kwargs["ctx"] = ctx
        method_attr = inspect.getattr_static(cls, "get_params")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "get_params")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_name is not None:
                init_kwargs["name"] = init_name
            instance = _get_or_create_instance(mod, "Command", **init_kwargs)
            result = getattr(instance, "get_params")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def command_get_short_help_str(
        limit: int | None = 45,
        init_name: str | None = None,
    ) -> str:
        """Gets short help for the command or makes it by shortening the"""
        # Instance method: core.Command.get_short_help_str
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Command")
        kwargs = {}
        if limit is not None:
            kwargs["limit"] = limit
        method_attr = inspect.getattr_static(cls, "get_short_help_str")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "get_short_help_str")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_name is not None:
                init_kwargs["name"] = init_name
            instance = _get_or_create_instance(mod, "Command", **init_kwargs)
            result = getattr(instance, "get_short_help_str")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def command_get_usage(
        ctx: str,
        init_name: str | None = None,
    ) -> str:
        """Formats the usage line into a string and returns it."""
        # Instance method: core.Command.get_usage
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Command")
        kwargs = {}
        kwargs["ctx"] = ctx
        method_attr = inspect.getattr_static(cls, "get_usage")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "get_usage")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_name is not None:
                init_kwargs["name"] = init_name
            instance = _get_or_create_instance(mod, "Command", **init_kwargs)
            result = getattr(instance, "get_usage")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def command_make_context(
        info_name: str,
        args: list,
        parent: str | None = None,
        init_name: str | None = None,
    ) -> str:
        """This function when given an info name and arguments will kick"""
        # Instance method: core.Command.make_context
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Command")
        kwargs = {}
        kwargs["info_name"] = info_name
        kwargs["args"] = args
        if parent is not None:
            kwargs["parent"] = parent
        method_attr = inspect.getattr_static(cls, "make_context")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "make_context")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_name is not None:
                init_kwargs["name"] = init_name
            instance = _get_or_create_instance(mod, "Command", **init_kwargs)
            result = getattr(instance, "make_context")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def command_make_parser(
        ctx: str,
        init_name: str | None = None,
    ) -> str:
        """Creates the underlying option parser for this command."""
        # Instance method: core.Command.make_parser
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Command")
        kwargs = {}
        kwargs["ctx"] = ctx
        method_attr = inspect.getattr_static(cls, "make_parser")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "make_parser")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_name is not None:
                init_kwargs["name"] = init_name
            instance = _get_or_create_instance(mod, "Command", **init_kwargs)
            result = getattr(instance, "make_parser")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def command_shell_complete(
        ctx: str,
        incomplete: str,
        init_name: str | None = None,
    ) -> str:
        """Return a list of completions for the incomplete value. Looks"""
        # Instance method: core.Command.shell_complete
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Command")
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
            if init_name is not None:
                init_kwargs["name"] = init_name
            instance = _get_or_create_instance(mod, "Command", **init_kwargs)
            result = getattr(instance, "shell_complete")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def command_to_info_dict(
        ctx: str,
        init_name: str | None = None,
    ) -> str:
        """To info dict"""
        # Instance method: core.Command.to_info_dict
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Command")
        kwargs = {}
        kwargs["ctx"] = ctx
        method_attr = inspect.getattr_static(cls, "to_info_dict")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "to_info_dict")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_name is not None:
                init_kwargs["name"] = init_name
            instance = _get_or_create_instance(mod, "Command", **init_kwargs)
            result = getattr(instance, "to_info_dict")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

