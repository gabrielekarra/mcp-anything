"""context tools for click."""

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
    """Register context tools with the server."""

    @server.tool()
    async def context_abort(
        init_command: str | None = None,
    ) -> str:
        """Aborts the script."""
        # Instance method: core.Context.abort
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Context")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "abort")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "abort")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_command is not None:
                init_kwargs["command"] = init_command
            instance = _get_or_create_instance(mod, "Context", **init_kwargs)
            result = getattr(instance, "abort")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def context_call_on_close(
        f: str,
        init_command: str | None = None,
    ) -> str:
        """Register a function to be called when the context tears down."""
        # Instance method: core.Context.call_on_close
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Context")
        kwargs = {}
        kwargs["f"] = f
        method_attr = inspect.getattr_static(cls, "call_on_close")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "call_on_close")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_command is not None:
                init_kwargs["command"] = init_command
            instance = _get_or_create_instance(mod, "Context", **init_kwargs)
            result = getattr(instance, "call_on_close")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def context_close(
        init_command: str | None = None,
    ) -> str:
        """Invoke all close callbacks registered with"""
        # Instance method: core.Context.close
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Context")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "close")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "close")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_command is not None:
                init_kwargs["command"] = init_command
            instance = _get_or_create_instance(mod, "Context", **init_kwargs)
            result = getattr(instance, "close")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def context_command_path(
        init_command: str | None = None,
    ) -> str:
        """The computed command path.  This is used for the ``usage``"""
        # Instance method: core.Context.command_path
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Context")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "command_path")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "command_path")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_command is not None:
                init_kwargs["command"] = init_command
            instance = _get_or_create_instance(mod, "Context", **init_kwargs)
            result = getattr(instance, "command_path")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def context_ensure_object(
        object_type: str,
        init_command: str | None = None,
    ) -> str:
        """Like :meth:`find_object` but sets the innermost object to a"""
        # Instance method: core.Context.ensure_object
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Context")
        kwargs = {}
        kwargs["object_type"] = object_type
        method_attr = inspect.getattr_static(cls, "ensure_object")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "ensure_object")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_command is not None:
                init_kwargs["command"] = init_command
            instance = _get_or_create_instance(mod, "Context", **init_kwargs)
            result = getattr(instance, "ensure_object")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def context_exit(
        code: int | None = 0,
        init_command: str | None = None,
    ) -> str:
        """Exits the application with a given exit code."""
        # Instance method: core.Context.exit
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Context")
        kwargs = {}
        if code is not None:
            kwargs["code"] = code
        method_attr = inspect.getattr_static(cls, "exit")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "exit")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_command is not None:
                init_kwargs["command"] = init_command
            instance = _get_or_create_instance(mod, "Context", **init_kwargs)
            result = getattr(instance, "exit")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def context_fail(
        message: str,
        init_command: str | None = None,
    ) -> str:
        """Aborts the execution of the program with a specific error"""
        # Instance method: core.Context.fail
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Context")
        kwargs = {}
        kwargs["message"] = message
        method_attr = inspect.getattr_static(cls, "fail")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "fail")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_command is not None:
                init_kwargs["command"] = init_command
            instance = _get_or_create_instance(mod, "Context", **init_kwargs)
            result = getattr(instance, "fail")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def context_find_object(
        object_type: str,
        init_command: str | None = None,
    ) -> str:
        """Finds the closest object of a given type."""
        # Instance method: core.Context.find_object
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Context")
        kwargs = {}
        kwargs["object_type"] = object_type
        method_attr = inspect.getattr_static(cls, "find_object")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "find_object")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_command is not None:
                init_kwargs["command"] = init_command
            instance = _get_or_create_instance(mod, "Context", **init_kwargs)
            result = getattr(instance, "find_object")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def context_find_root(
        init_command: str | None = None,
    ) -> str:
        """Finds the outermost context."""
        # Instance method: core.Context.find_root
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Context")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "find_root")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "find_root")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_command is not None:
                init_kwargs["command"] = init_command
            instance = _get_or_create_instance(mod, "Context", **init_kwargs)
            result = getattr(instance, "find_root")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def context_forward(
        init_command: str | None = None,
    ) -> str:
        """Similar to :meth:`invoke` but fills in default keyword"""
        # Instance method: core.Context.forward
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Context")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "forward")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "forward")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_command is not None:
                init_kwargs["command"] = init_command
            instance = _get_or_create_instance(mod, "Context", **init_kwargs)
            result = getattr(instance, "forward")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def context_get_help(
        init_command: str | None = None,
    ) -> str:
        """Helper method to get formatted help page for the current"""
        # Instance method: core.Context.get_help
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Context")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "get_help")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "get_help")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_command is not None:
                init_kwargs["command"] = init_command
            instance = _get_or_create_instance(mod, "Context", **init_kwargs)
            result = getattr(instance, "get_help")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def context_get_parameter_source(
        name: str,
        init_command: str | None = None,
    ) -> str:
        """Get the source of a parameter. This indicates the location"""
        # Instance method: core.Context.get_parameter_source
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Context")
        kwargs = {}
        kwargs["name"] = name
        method_attr = inspect.getattr_static(cls, "get_parameter_source")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "get_parameter_source")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_command is not None:
                init_kwargs["command"] = init_command
            instance = _get_or_create_instance(mod, "Context", **init_kwargs)
            result = getattr(instance, "get_parameter_source")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def context_get_usage(
        init_command: str | None = None,
    ) -> str:
        """Helper method to get formatted usage string for the current"""
        # Instance method: core.Context.get_usage
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Context")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "get_usage")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "get_usage")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_command is not None:
                init_kwargs["command"] = init_command
            instance = _get_or_create_instance(mod, "Context", **init_kwargs)
            result = getattr(instance, "get_usage")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def context_lookup_default(
        name: str,
        call: str | None = "True",
        init_command: str | None = None,
    ) -> str:
        """Lookup default"""
        # Instance method: core.Context.lookup_default
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Context")
        kwargs = {}
        kwargs["name"] = name
        if call is not None:
            kwargs["call"] = call
        method_attr = inspect.getattr_static(cls, "lookup_default")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "lookup_default")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_command is not None:
                init_kwargs["command"] = init_command
            instance = _get_or_create_instance(mod, "Context", **init_kwargs)
            result = getattr(instance, "lookup_default")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def context_make_formatter(
        init_command: str | None = None,
    ) -> str:
        """Creates the :class:`~click.HelpFormatter` for the help and"""
        # Instance method: core.Context.make_formatter
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Context")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "make_formatter")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "make_formatter")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_command is not None:
                init_kwargs["command"] = init_command
            instance = _get_or_create_instance(mod, "Context", **init_kwargs)
            result = getattr(instance, "make_formatter")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def context_meta(
        init_command: str | None = None,
    ) -> str:
        """This is a dictionary which is shared with all the contexts"""
        # Instance method: core.Context.meta
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Context")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "meta")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "meta")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_command is not None:
                init_kwargs["command"] = init_command
            instance = _get_or_create_instance(mod, "Context", **init_kwargs)
            result = getattr(instance, "meta")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def context_protected_args(
        init_command: str | None = None,
    ) -> str:
        """Protected args"""
        # Instance method: core.Context.protected_args
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Context")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "protected_args")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "protected_args")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_command is not None:
                init_kwargs["command"] = init_command
            instance = _get_or_create_instance(mod, "Context", **init_kwargs)
            result = getattr(instance, "protected_args")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def context_scope(
        cleanup: bool | None = True,
        init_command: str | None = None,
    ) -> str:
        """This helper method can be used with the context object to promote"""
        # Instance method: core.Context.scope
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Context")
        kwargs = {}
        if cleanup is not None:
            kwargs["cleanup"] = cleanup
        method_attr = inspect.getattr_static(cls, "scope")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "scope")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_command is not None:
                init_kwargs["command"] = init_command
            instance = _get_or_create_instance(mod, "Context", **init_kwargs)
            result = getattr(instance, "scope")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def context_set_parameter_source(
        name: str,
        source: str,
        init_command: str | None = None,
    ) -> str:
        """Set the source of a parameter. This indicates the location"""
        # Instance method: core.Context.set_parameter_source
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Context")
        kwargs = {}
        kwargs["name"] = name
        kwargs["source"] = source
        method_attr = inspect.getattr_static(cls, "set_parameter_source")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "set_parameter_source")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_command is not None:
                init_kwargs["command"] = init_command
            instance = _get_or_create_instance(mod, "Context", **init_kwargs)
            result = getattr(instance, "set_parameter_source")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def context_to_info_dict(
        init_command: str | None = None,
    ) -> str:
        """Gather information that could be useful for a tool generating"""
        # Instance method: core.Context.to_info_dict
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Context")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "to_info_dict")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "to_info_dict")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_command is not None:
                init_kwargs["command"] = init_command
            instance = _get_or_create_instance(mod, "Context", **init_kwargs)
            result = getattr(instance, "to_info_dict")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def context_with_resource(
        context_manager: str,
        init_command: str | None = None,
    ) -> str:
        """Register a resource as if it were used in a ``with``"""
        # Instance method: core.Context.with_resource
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "core")
        cls = getattr(mod, "Context")
        kwargs = {}
        kwargs["context_manager"] = context_manager
        method_attr = inspect.getattr_static(cls, "with_resource")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "with_resource")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_command is not None:
                init_kwargs["command"] = init_command
            instance = _get_or_create_instance(mod, "Context", **init_kwargs)
            result = getattr(instance, "with_resource")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

