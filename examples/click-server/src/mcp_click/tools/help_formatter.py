"""help_formatter tools for click."""

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
    """Register help_formatter tools with the server."""

    @server.tool()
    async def help_formatter_dedent(
    ) -> str:
        """Decreases the indentation."""
        # Instance method: formatting.HelpFormatter.dedent
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "formatting")
        cls = getattr(mod, "HelpFormatter")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "dedent")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "dedent")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            instance = _get_or_create_instance(mod, "HelpFormatter", **init_kwargs)
            result = getattr(instance, "dedent")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def help_formatter_getvalue(
    ) -> str:
        """Returns the buffer contents."""
        # Instance method: formatting.HelpFormatter.getvalue
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "formatting")
        cls = getattr(mod, "HelpFormatter")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "getvalue")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "getvalue")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            instance = _get_or_create_instance(mod, "HelpFormatter", **init_kwargs)
            result = getattr(instance, "getvalue")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def help_formatter_indent(
    ) -> str:
        """Increases the indentation."""
        # Instance method: formatting.HelpFormatter.indent
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "formatting")
        cls = getattr(mod, "HelpFormatter")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "indent")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "indent")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            instance = _get_or_create_instance(mod, "HelpFormatter", **init_kwargs)
            result = getattr(instance, "indent")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def help_formatter_indentation(
    ) -> str:
        """A context manager that increases the indentation."""
        # Instance method: formatting.HelpFormatter.indentation
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "formatting")
        cls = getattr(mod, "HelpFormatter")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "indentation")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "indentation")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            instance = _get_or_create_instance(mod, "HelpFormatter", **init_kwargs)
            result = getattr(instance, "indentation")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def help_formatter_section(
        name: str,
    ) -> str:
        """Helpful context manager that writes a paragraph, a heading,"""
        # Instance method: formatting.HelpFormatter.section
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "formatting")
        cls = getattr(mod, "HelpFormatter")
        kwargs = {}
        kwargs["name"] = name
        method_attr = inspect.getattr_static(cls, "section")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "section")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            instance = _get_or_create_instance(mod, "HelpFormatter", **init_kwargs)
            result = getattr(instance, "section")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def help_formatter_write(
        string: str,
    ) -> str:
        """Writes a unicode string into the internal buffer."""
        # Instance method: formatting.HelpFormatter.write
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "formatting")
        cls = getattr(mod, "HelpFormatter")
        kwargs = {}
        kwargs["string"] = string
        method_attr = inspect.getattr_static(cls, "write")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "write")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            instance = _get_or_create_instance(mod, "HelpFormatter", **init_kwargs)
            result = getattr(instance, "write")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def help_formatter_write_dl(
        rows: str,
        col_max: int | None = 30,
        col_spacing: int | None = 2,
    ) -> str:
        """Writes a definition list into the buffer.  This is how options"""
        # Instance method: formatting.HelpFormatter.write_dl
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "formatting")
        cls = getattr(mod, "HelpFormatter")
        kwargs = {}
        kwargs["rows"] = rows
        if col_max is not None:
            kwargs["col_max"] = col_max
        if col_spacing is not None:
            kwargs["col_spacing"] = col_spacing
        method_attr = inspect.getattr_static(cls, "write_dl")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "write_dl")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            instance = _get_or_create_instance(mod, "HelpFormatter", **init_kwargs)
            result = getattr(instance, "write_dl")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def help_formatter_write_heading(
        heading: str,
    ) -> str:
        """Writes a heading into the buffer."""
        # Instance method: formatting.HelpFormatter.write_heading
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "formatting")
        cls = getattr(mod, "HelpFormatter")
        kwargs = {}
        kwargs["heading"] = heading
        method_attr = inspect.getattr_static(cls, "write_heading")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "write_heading")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            instance = _get_or_create_instance(mod, "HelpFormatter", **init_kwargs)
            result = getattr(instance, "write_heading")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def help_formatter_write_paragraph(
    ) -> str:
        """Writes a paragraph into the buffer."""
        # Instance method: formatting.HelpFormatter.write_paragraph
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "formatting")
        cls = getattr(mod, "HelpFormatter")
        kwargs = {}
        method_attr = inspect.getattr_static(cls, "write_paragraph")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "write_paragraph")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            instance = _get_or_create_instance(mod, "HelpFormatter", **init_kwargs)
            result = getattr(instance, "write_paragraph")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def help_formatter_write_text(
        text: str,
    ) -> str:
        """Writes re-indented text into the buffer.  This rewraps and"""
        # Instance method: formatting.HelpFormatter.write_text
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "formatting")
        cls = getattr(mod, "HelpFormatter")
        kwargs = {}
        kwargs["text"] = text
        method_attr = inspect.getattr_static(cls, "write_text")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "write_text")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            instance = _get_or_create_instance(mod, "HelpFormatter", **init_kwargs)
            result = getattr(instance, "write_text")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

    @server.tool()
    async def help_formatter_write_usage(
        prog: str,
        args: str | None = "",
        prefix: str | None = None,
    ) -> str:
        """Writes a usage line into the buffer."""
        # Instance method: formatting.HelpFormatter.write_usage
        _setup_import_path("/tmp/click/src/click")
        mod = _load_source_module("/tmp/click/src/click", "formatting")
        cls = getattr(mod, "HelpFormatter")
        kwargs = {}
        kwargs["prog"] = prog
        if args is not None:
            kwargs["args"] = args
        if prefix is not None:
            kwargs["prefix"] = prefix
        method_attr = inspect.getattr_static(cls, "write_usage")
        if isinstance(method_attr, (staticmethod, classmethod)):
            # Static/class method — call directly on the class
            result = getattr(cls, "write_usage")(**kwargs)
        else:
            # Instance method — auto-instantiate the class
            init_kwargs = {}
            instance = _get_or_create_instance(mod, "HelpFormatter", **init_kwargs)
            result = getattr(instance, "write_usage")(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return str(result) if result is not None else "OK"

