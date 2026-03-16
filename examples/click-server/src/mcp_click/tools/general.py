"""general tools for click."""

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
    """Register general tools with the server."""

    @server.tool()
    async def run_click(
        args: str,
    ) -> str:
        """Run click with the given command-line arguments"""
        # Run CLI subcommand: 
        cmd_args: list[str] = []
        if args:
            cmd_args.extend(args.split())
        return await backend.run_subcommand("", cmd_args)

    @server.tool()
    async def augment_usage_errors(
        ctx: str,
        param: str | None = None,
    ) -> str:
        """Context manager that attaches extra information to exceptions."""
        # Call function via CLI backend: core.py::augment_usage_errors
        return await backend.run_function_as_cli(
            "core.py",
            "augment_usage_errors",
            ctx=ctx,
            param=param,
        )

    @server.tool()
    async def batch(
        iterable: str,
        batch_size: int,
    ) -> str:
        """Batch"""
        # Call function via CLI backend: core.py::batch
        return await backend.run_function_as_cli(
            "core.py",
            "batch",
            iterable=iterable,
            batch_size=batch_size,
        )

    @server.tool()
    async def clear(
    ) -> str:
        """Clears the terminal screen.  This will have the effect of clearing"""
        # Call function via CLI backend: termui.py::clear
        return await backend.run_function_as_cli(
            "termui.py",
            "clear",
        )

    @server.tool()
    async def command(
        name: str,
    ) -> str:
        """Command"""
        # Call function via CLI backend: decorators.py::command
        return await backend.run_function_as_cli(
            "decorators.py",
            "command",
            name=name,
        )

    @server.tool()
    async def confirm(
        text: str,
        default: bool | None = False,
        abort: bool | None = False,
        prompt_suffix: str | None = ": ",
        show_default: bool | None = True,
        err: bool | None = False,
    ) -> str:
        """Prompts for confirmation (yes/no question)."""
        # Call function via CLI backend: termui.py::confirm
        return await backend.run_function_as_cli(
            "termui.py",
            "confirm",
            text=text,
            default=default,
            abort=abort,
            prompt_suffix=prompt_suffix,
            show_default=show_default,
            err=err,
        )

    @server.tool()
    async def confirmation_option(
    ) -> str:
        """Add a ``--yes`` option which shows a prompt before continuing if"""
        # Call function via CLI backend: decorators.py::confirmation_option
        return await backend.run_function_as_cli(
            "decorators.py",
            "confirmation_option",
        )

    @server.tool()
    async def echo(
        message: str | None = None,
        file: str | None = None,
        nl: bool | None = True,
        err: bool | None = False,
        color: bool | None = None,
    ) -> str:
        """Print a message and newline to stdout or a file. This should be"""
        # Call function via CLI backend: utils.py::echo
        return await backend.run_function_as_cli(
            "utils.py",
            "echo",
            message=message,
            file=file,
            nl=nl,
            err=err,
            color=color,
        )

    @server.tool()
    async def echo_via_pager(
        text_or_generator: str,
        color: bool | None = None,
    ) -> str:
        """This function takes a text and shows it via an environment specific"""
        # Call function via CLI backend: termui.py::echo_via_pager
        return await backend.run_function_as_cli(
            "termui.py",
            "echo_via_pager",
            text_or_generator=text_or_generator,
            color=color,
        )

    @server.tool()
    async def edit(
        text: str,
        editor: str | None = None,
        env: str | None = None,
        require_save: bool | None = False,
        extension: str | None = ".txt",
    ) -> str:
        """Edit"""
        # Call function via CLI backend: termui.py::edit
        return await backend.run_function_as_cli(
            "termui.py",
            "edit",
            text=text,
            editor=editor,
            env=env,
            require_save=require_save,
            extension=extension,
        )

    @server.tool()
    async def format_filename(
        filename: str,
        shorten: bool | None = False,
    ) -> str:
        """Format a filename as a string for display. Ensures the filename can be"""
        # Call function via CLI backend: utils.py::format_filename
        return await backend.run_function_as_cli(
            "utils.py",
            "format_filename",
            filename=filename,
            shorten=shorten,
        )

    @server.tool()
    async def getchar(
        echo: bool | None = False,
    ) -> str:
        """Fetches a single character from the terminal and returns it.  This"""
        # Call function via CLI backend: termui.py::getchar
        return await backend.run_function_as_cli(
            "termui.py",
            "getchar",
            echo=echo,
        )

    @server.tool()
    async def group(
        name: str,
    ) -> str:
        """Group"""
        # Call function via CLI backend: decorators.py::group
        return await backend.run_function_as_cli(
            "decorators.py",
            "group",
            name=name,
        )

    @server.tool()
    async def help_option(
    ) -> str:
        """Pre-configured ``--help`` option which immediately prints the help page"""
        # Call function via CLI backend: decorators.py::help_option
        return await backend.run_function_as_cli(
            "decorators.py",
            "help_option",
        )

    @server.tool()
    async def hidden_prompt_func(
        prompt: str,
    ) -> str:
        """Hidden prompt func"""
        # Call function via CLI backend: termui.py::hidden_prompt_func
        return await backend.run_function_as_cli(
            "termui.py",
            "hidden_prompt_func",
            prompt=prompt,
        )

    @server.tool()
    async def is_ascii_encoding(
        encoding: str,
    ) -> str:
        """Checks if a given encoding is ascii."""
        # Call function via CLI backend: _compat.py::is_ascii_encoding
        return await backend.run_function_as_cli(
            "_compat.py",
            "is_ascii_encoding",
            encoding=encoding,
        )

    @server.tool()
    async def isatty(
        stream: str,
    ) -> str:
        """Isatty"""
        # Call function via CLI backend: _compat.py::isatty
        return await backend.run_function_as_cli(
            "_compat.py",
            "isatty",
            stream=stream,
        )

    @server.tool()
    async def iter_params_for_processing(
        invocation_order: str,
        declaration_order: str,
    ) -> str:
        """Returns all declared parameters in the order they should be processed."""
        # Call function via CLI backend: core.py::iter_params_for_processing
        return await backend.run_function_as_cli(
            "core.py",
            "iter_params_for_processing",
            invocation_order=invocation_order,
            declaration_order=declaration_order,
        )

    @server.tool()
    async def iter_rows(
        rows: str,
        col_count: int,
    ) -> str:
        """Iter rows"""
        # Call function via CLI backend: formatting.py::iter_rows
        return await backend.run_function_as_cli(
            "formatting.py",
            "iter_rows",
            rows=rows,
            col_count=col_count,
        )

    @server.tool()
    async def join_options(
        options: str,
    ) -> str:
        """Given a list of option strings this joins them in the most appropriate"""
        # Call function via CLI backend: formatting.py::join_options
        return await backend.run_function_as_cli(
            "formatting.py",
            "join_options",
            options=options,
        )

    @server.tool()
    async def launch(
        url: str,
        wait: bool | None = False,
        locate: bool | None = False,
    ) -> str:
        """This function launches the given URL (or filename) in the default"""
        # Call function via CLI backend: termui.py::launch
        return await backend.run_function_as_cli(
            "termui.py",
            "launch",
            url=url,
            wait=wait,
            locate=locate,
        )

    @server.tool()
    async def make_default_short_help(
        help: str,
        max_length: int | None = 45,
    ) -> str:
        """Returns a condensed version of help string."""
        # Call function via CLI backend: utils.py::make_default_short_help
        return await backend.run_function_as_cli(
            "utils.py",
            "make_default_short_help",
            help=help,
            max_length=max_length,
        )

    @server.tool()
    async def make_input_stream(
        input: str,
        charset: str,
    ) -> str:
        """Make input stream"""
        # Call function via CLI backend: testing.py::make_input_stream
        return await backend.run_function_as_cli(
            "testing.py",
            "make_input_stream",
            input=input,
            charset=charset,
        )

    @server.tool()
    async def make_str(
        value: str,
    ) -> str:
        """Converts a value into a valid string."""
        # Call function via CLI backend: utils.py::make_str
        return await backend.run_function_as_cli(
            "utils.py",
            "make_str",
            value=value,
        )

    @server.tool()
    async def measure_table(
        rows: str,
    ) -> str:
        """Measure table"""
        # Call function via CLI backend: formatting.py::measure_table
        return await backend.run_function_as_cli(
            "formatting.py",
            "measure_table",
            rows=rows,
        )

    @server.tool()
    async def open_file(
        filename: str,
        mode: str | None = "r",
        encoding: str | None = None,
        errors: str | None = "strict",
        lazy: bool | None = False,
        atomic: bool | None = False,
    ) -> str:
        """Open a file, with extra behavior to handle ``'-'`` to indicate"""
        # Call function via CLI backend: utils.py::open_file
        return await backend.run_function_as_cli(
            "utils.py",
            "open_file",
            filename=filename,
            mode=mode,
            encoding=encoding,
            errors=errors,
            lazy=lazy,
            atomic=atomic,
        )

    @server.tool()
    async def open_stream(
        filename: str,
        mode: str | None = "r",
        encoding: str | None = None,
        errors: str | None = "strict",
        atomic: bool | None = False,
    ) -> str:
        """Open stream"""
        # Call function via CLI backend: _compat.py::open_stream
        return await backend.run_function_as_cli(
            "_compat.py",
            "open_stream",
            filename=filename,
            mode=mode,
            encoding=encoding,
            errors=errors,
            atomic=atomic,
        )

    @server.tool()
    async def pager(
        generator: str,
        color: bool | None = None,
    ) -> str:
        """Decide what method to use for paging through text."""
        # Call function via CLI backend: _termui_impl.py::pager
        return await backend.run_function_as_cli(
            "_termui_impl.py",
            "pager",
            generator=generator,
            color=color,
        )

    @server.tool()
    async def pass_context(
        f: str,
    ) -> str:
        """Marks a callback as wanting to receive the current context"""
        # Call function via CLI backend: decorators.py::pass_context
        return await backend.run_function_as_cli(
            "decorators.py",
            "pass_context",
            f=f,
        )

    @server.tool()
    async def pass_obj(
        f: str,
    ) -> str:
        """Similar to :func:`pass_context`, but only pass the object on the"""
        # Call function via CLI backend: decorators.py::pass_obj
        return await backend.run_function_as_cli(
            "decorators.py",
            "pass_obj",
            f=f,
        )

    @server.tool()
    async def password_option(
    ) -> str:
        """Add a ``--password`` option which prompts for a password, hiding"""
        # Call function via CLI backend: decorators.py::password_option
        return await backend.run_function_as_cli(
            "decorators.py",
            "password_option",
        )

    @server.tool()
    async def pause(
        info: str | None = None,
        err: bool | None = False,
    ) -> str:
        """This command stops execution and waits for the user to press any"""
        # Call function via CLI backend: termui.py::pause
        return await backend.run_function_as_cli(
            "termui.py",
            "pause",
            info=info,
            err=err,
        )

    @server.tool()
    async def pop_context(
    ) -> str:
        """Removes the top level from the stack."""
        # Call function via CLI backend: globals.py::pop_context
        return await backend.run_function_as_cli(
            "globals.py",
            "pop_context",
        )

    @server.tool()
    async def progressbar(
        length: int,
        label: str | None = None,
        hidden: bool | None = False,
        show_eta: bool | None = True,
        show_percent: bool | None = None,
        show_pos: bool | None = False,
        fill_char: str | None = "#",
        empty_char: str | None = "-",
        bar_template: str | None = "%(label)s  [%(bar)s]  %(info)s",
        info_sep: str | None = "  ",
        width: int | None = 36,
        file: str | None = None,
        color: bool | None = None,
        update_min_steps: int | None = 1,
    ) -> str:
        """Progressbar"""
        # Call function via CLI backend: termui.py::progressbar
        return await backend.run_function_as_cli(
            "termui.py",
            "progressbar",
            length=length,
            label=label,
            hidden=hidden,
            show_eta=show_eta,
            show_percent=show_percent,
            show_pos=show_pos,
            fill_char=fill_char,
            empty_char=empty_char,
            bar_template=bar_template,
            info_sep=info_sep,
            width=width,
            file=file,
            color=color,
            update_min_steps=update_min_steps,
        )

    @server.tool()
    async def push_context(
        ctx: str,
    ) -> str:
        """Pushes a new context to the current stack."""
        # Call function via CLI backend: globals.py::push_context
        return await backend.run_function_as_cli(
            "globals.py",
            "push_context",
            ctx=ctx,
        )

    @server.tool()
    async def resolve_color_default(
        color: bool | None = None,
    ) -> str:
        """Internal helper to get the default value of the color flag.  If a"""
        # Call function via CLI backend: globals.py::resolve_color_default
        return await backend.run_function_as_cli(
            "globals.py",
            "resolve_color_default",
            color=color,
        )

    @server.tool()
    async def safecall(
        func: str,
    ) -> str:
        """Wraps a function so that it swallows exceptions."""
        # Call function via CLI backend: utils.py::safecall
        return await backend.run_function_as_cli(
            "utils.py",
            "safecall",
            func=func,
        )

    @server.tool()
    async def secho(
        message: str | None = None,
        file: str | None = None,
        nl: bool | None = True,
        err: bool | None = False,
        color: bool | None = None,
    ) -> str:
        """This function combines :func:`echo` and :func:`style` into one"""
        # Call function via CLI backend: termui.py::secho
        return await backend.run_function_as_cli(
            "termui.py",
            "secho",
            message=message,
            file=file,
            nl=nl,
            err=err,
            color=color,
        )

    @server.tool()
    async def shell_complete(
        cli: str,
        ctx_args: str,
        prog_name: str,
        complete_var: str,
        instruction: str,
    ) -> str:
        """Perform shell completion for the given CLI program."""
        # Call function via CLI backend: shell_completion.py::shell_complete
        return await backend.run_function_as_cli(
            "shell_completion.py",
            "shell_complete",
            cli=cli,
            ctx_args=ctx_args,
            prog_name=prog_name,
            complete_var=complete_var,
            instruction=instruction,
        )

