"""shell_complete tools for click."""

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
    """Register shell_complete tools with the server."""

    @server.tool()
    async def shell_complete_complete(
        init_cli: str | None = None,
        init_ctx_args: str | None = None,
        init_prog_name: str | None = None,
        init_complete_var: str | None = None,
    ) -> str:
        """Produce the completion data to send back to the shell."""
        # Instance method: shell_completion.ShellComplete.complete
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "shell_completion")
        cls = getattr(mod, "ShellComplete")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "complete")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "complete")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_cli is not None:
                init_kwargs["cli"] = init_cli
            if init_ctx_args is not None:
                init_kwargs["ctx_args"] = init_ctx_args
            if init_prog_name is not None:
                init_kwargs["prog_name"] = init_prog_name
            if init_complete_var is not None:
                init_kwargs["complete_var"] = init_complete_var
            instance = _get_or_create_instance(mod, "ShellComplete", **init_kwargs)
            result = getattr(instance, "complete")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def shell_complete_format_completion(
        item: str,
        init_cli: str | None = None,
        init_ctx_args: str | None = None,
        init_prog_name: str | None = None,
        init_complete_var: str | None = None,
    ) -> str:
        """Format a completion item into the form recognized by the"""
        # Instance method: shell_completion.ShellComplete.format_completion
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "shell_completion")
        cls = getattr(mod, "ShellComplete")
        kwargs = {}
        kwargs["item"] = item
        method_attr = inspect.getattr_static(cls, "format_completion")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "format_completion")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_cli is not None:
                init_kwargs["cli"] = init_cli
            if init_ctx_args is not None:
                init_kwargs["ctx_args"] = init_ctx_args
            if init_prog_name is not None:
                init_kwargs["prog_name"] = init_prog_name
            if init_complete_var is not None:
                init_kwargs["complete_var"] = init_complete_var
            instance = _get_or_create_instance(mod, "ShellComplete", **init_kwargs)
            result = getattr(instance, "format_completion")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def shell_complete_func_name(
        init_cli: str | None = None,
        init_ctx_args: str | None = None,
        init_prog_name: str | None = None,
        init_complete_var: str | None = None,
    ) -> str:
        """The name of the shell function defined by the completion"""
        # Instance method: shell_completion.ShellComplete.func_name
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "shell_completion")
        cls = getattr(mod, "ShellComplete")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "func_name")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "func_name")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            if init_cli is not None:
                init_kwargs["cli"] = init_cli
            if init_ctx_args is not None:
                init_kwargs["ctx_args"] = init_ctx_args
            if init_prog_name is not None:
                init_kwargs["prog_name"] = init_prog_name
            if init_complete_var is not None:
                init_kwargs["complete_var"] = init_complete_var
            instance = _get_or_create_instance(mod, "ShellComplete", **init_kwargs)
            result = getattr(instance, "func_name")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

