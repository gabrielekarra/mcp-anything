"""AST-based Python source code analysis.

Extracts function signatures, class definitions, decorators, docstrings,
and parameter types from Python source files to generate rich Capability objects.
"""

import ast
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from mcp_anything.models.analysis import Capability, FileInfo, IPCType, Language, ParameterSpec

# Names that indicate a function is not a public capability
SKIP_NAMES = {
    "__init__", "__repr__", "__str__", "__eq__", "__hash__", "__lt__", "__le__",
    "__gt__", "__ge__", "__len__", "__getitem__", "__setitem__", "__delitem__",
    "__contains__", "__iter__", "__next__", "__enter__", "__exit__", "__call__",
    "__new__", "__del__", "setup", "teardown", "main",
}

# Prefixes/patterns for functions that should not become tools
SKIP_PREFIXES = ("test_", "assert_", "_assert", "mock_", "fake_", "fixture_")
SKIP_SUFFIXES = ("_test", "_fixture", "_factory", "_helper")

# Names that are almost never useful as tools
SKIP_FUNCTION_NAMES = {
    "setup", "teardown", "main", "run", "cli", "app",
    "setup_logging", "configure_logging", "parse_args",
    "register", "unregister", "setup_module", "teardown_module",
    "pytest_configure", "pytest_collection_modifyitems",
}

# Functions that call sys.exit() or os._exit() are destructive — skip them
_DESTRUCTIVE_CALLS = {"sys.exit", "os._exit", "os.abort", "quit", "exit"}

# Method names too generic to be useful as standalone tools
_GENERIC_METHOD_NAMES = {
    "get", "set", "put", "post", "delete", "update", "call", "run",
    "execute", "invoke", "apply", "do", "handle", "process",
}

# Decorator patterns that mark CLI commands
CLI_COMMAND_DECORATORS = {
    "command", "group", "option", "argument",  # click
    "app.command",                              # typer
}


@dataclass
class ExtractedFunction:
    """A function extracted from AST analysis."""

    name: str
    docstring: str
    parameters: list[ParameterSpec]
    return_type: str
    decorators: list[str]
    is_method: bool
    is_private: bool
    class_name: str
    source_file: str
    line_number: int
    returns_callable: bool = False
    calls_sys_exit: bool = False


@dataclass
class ExtractedClass:
    """A class extracted from AST analysis."""

    name: str
    docstring: str
    bases: list[str]
    methods: list[ExtractedFunction]
    source_file: str


@dataclass
class ASTAnalysisResult:
    """Result of analyzing a single Python file's AST."""

    functions: list[ExtractedFunction] = field(default_factory=list)
    classes: list[ExtractedClass] = field(default_factory=list)
    cli_commands: list[ExtractedFunction] = field(default_factory=list)
    has_argparse: bool = False
    has_click: bool = False
    has_typer: bool = False
    subcommands: list[dict] = field(default_factory=list)


def _annotation_to_type(node: Optional[ast.expr]) -> str:
    """Convert an AST annotation node to a type string."""
    if node is None:
        return "string"
    if isinstance(node, ast.Constant):
        return str(node.value)
    if isinstance(node, ast.Name):
        mapping = {
            "str": "string", "int": "integer", "float": "float",
            "bool": "boolean", "list": "array", "dict": "object",
            "None": "null", "bytes": "string", "Path": "string",
        }
        return mapping.get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        return _annotation_to_type(node.attr) if isinstance(node.attr, ast.expr) else str(node.attr)
    if isinstance(node, ast.Subscript):
        base = _annotation_to_type(node.value)
        if base in ("Optional", "Union"):
            return _annotation_to_type(node.slice)
        return base
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        # X | None union syntax
        left = _annotation_to_type(node.left)
        right = _annotation_to_type(node.right)
        if right == "null":
            return left
        return left
    return "string"


def _get_default_str(node: Optional[ast.expr]) -> Optional[str]:
    """Extract a string representation of a default value.

    Only returns safe literal values. Variable references, function calls,
    and other complex expressions from the target project are replaced with
    None to avoid NameError in generated code.
    """
    if node is None:
        return None
    if isinstance(node, ast.Constant):
        if node.value is None:
            return None
        return str(node.value)
    if isinstance(node, ast.Name) and node.id == "None":
        return None
    if isinstance(node, ast.List) and not node.elts:
        return "[]"
    if isinstance(node, ast.Dict) and not node.keys:
        return "{}"
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float, bool)):
        return str(node.value)
    # Variable references, function calls, etc. → not safe to copy
    return None


def _get_decorator_names(decorators: list[ast.expr]) -> list[str]:
    """Extract decorator names from AST decorator list."""
    names = []
    for dec in decorators:
        if isinstance(dec, ast.Name):
            names.append(dec.id)
        elif isinstance(dec, ast.Attribute):
            parts = []
            node = dec
            while isinstance(node, ast.Attribute):
                parts.append(node.attr)
                node = node.value
            if isinstance(node, ast.Name):
                parts.append(node.id)
            names.append(".".join(reversed(parts)))
        elif isinstance(dec, ast.Call):
            names.extend(_get_decorator_names([dec.func]))
    return names


def _body_returns_callable(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Check if a function returns a callable (closure/function factory).

    Detects patterns like:
        def make_color(code):
            def color_func(s):
                ...
            return color_func
    """
    # Check if the function body contains a nested function definition
    has_nested_def = False
    for child in ast.walk(node):
        if child is node:
            continue
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            has_nested_def = True
            break

    if not has_nested_def:
        return False

    # Check if any return statement returns a name (likely the nested function)
    for child in ast.walk(node):
        if isinstance(child, ast.Return) and child.value is not None:
            if isinstance(child.value, ast.Name):
                return True
    return False


def _body_calls_sys_exit(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Check if a function calls sys.exit(), os._exit(), or similar."""
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        func = child.func
        # sys.exit(), os._exit(), os.abort()
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            full_name = f"{func.value.id}.{func.attr}"
            if full_name in _DESTRUCTIVE_CALLS:
                return True
        # Bare exit() or quit()
        if isinstance(func, ast.Name) and func.id in _DESTRUCTIVE_CALLS:
            return True
    return False


def _extract_click_params(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[ParameterSpec]:
    """Extract parameter info from Click decorators (@click.option, @click.argument)."""
    params: list[ParameterSpec] = []

    for dec in node.decorator_list:
        if not isinstance(dec, ast.Call):
            continue
        # Get decorator name
        func = dec.func
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            dec_name = f"{func.value.id}.{func.attr}"
        elif isinstance(func, ast.Attribute):
            dec_name = func.attr
        else:
            continue

        if dec_name not in ("click.option", "click.argument"):
            continue

        is_option = dec_name == "click.option"

        # First positional arg is the flag name(s)
        if not dec.args:
            continue
        first_arg = dec.args[0]
        if not isinstance(first_arg, ast.Constant) or not isinstance(first_arg.value, str):
            continue

        flag_str = first_arg.value

        # For boolean flags like --verbose/--no-verbose
        if is_option and "/" in flag_str:
            name = flag_str.split("/")[0].lstrip("-").replace("-", "_")
            params.append(ParameterSpec(
                name=name,
                type="boolean",
                description=_get_click_keyword(dec, "help"),
                required=False,
                default=_get_click_keyword(dec, "default"),
            ))
            continue

        # Get the param name
        if is_option:
            # Use long flag: find the --flag arg
            name = None
            for arg in dec.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    if arg.value.startswith("--"):
                        name = arg.value.lstrip("-").replace("-", "_")
                        break
            if not name:
                name = flag_str.lstrip("-").replace("-", "_")
        else:
            name = flag_str.lower().replace("-", "_")

        # Get type
        param_type = "string"
        handled = False
        for kw in dec.keywords:
            if kw.arg == "type":
                if isinstance(kw.value, ast.Name):
                    type_map = {"str": "string", "int": "integer", "float": "float", "bool": "boolean"}
                    param_type = type_map.get(kw.value.id, "string")
                elif isinstance(kw.value, ast.Attribute):
                    param_type = "string"
                # click.Choice(['a', 'b', 'c'])
                elif isinstance(kw.value, ast.Call):
                    if isinstance(kw.value.func, ast.Attribute) and kw.value.func.attr == "Choice":
                        param_type = "string"
                        if kw.value.args and isinstance(kw.value.args[0], ast.List):
                            enum_vals = []
                            for elt in kw.value.args[0].elts:
                                if isinstance(elt, ast.Constant):
                                    enum_vals.append(str(elt.value))
                            if enum_vals:
                                params.append(ParameterSpec(
                                    name=name,
                                    type="string",
                                    description=_get_click_keyword(dec, "help"),
                                    required=not is_option,
                                    default=_get_click_keyword(dec, "default"),
                                    enum_values=enum_vals,
                                ))
                                handled = True

        if handled:
            continue

        # Is it required?
        required = not is_option  # arguments are required by default
        for kw in dec.keywords:
            if kw.arg == "required" and isinstance(kw.value, ast.Constant):
                required = bool(kw.value.value)

        params.append(ParameterSpec(
            name=name,
            type=param_type,
            description=_get_click_keyword(dec, "help"),
            required=required,
            default=_get_click_keyword(dec, "default"),
        ))

    return params


def _get_click_keyword(call: ast.Call, keyword: str) -> str:
    """Extract a keyword argument value from a click decorator call."""
    for kw in call.keywords:
        if kw.arg == keyword and isinstance(kw.value, ast.Constant):
            return str(kw.value.value)
    return ""


def _extract_typer_params(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[ParameterSpec]:
    """Extract parameter info from Typer-style function signatures.

    Typer uses type annotations + default values like:
        name: str = typer.Option(..., help="Your name")
        filename: str = typer.Argument(..., help="File")
    """
    params: list[ParameterSpec] = []
    args = node.args

    num_args = len(args.args)
    num_defaults = len(args.defaults)
    first_default_idx = num_args - num_defaults

    for i, arg in enumerate(args.args):
        if arg.arg in ("self", "cls"):
            continue

        has_default = i >= first_default_idx
        default_node = args.defaults[i - first_default_idx] if has_default else None

        # Check if default is typer.Option(...) or typer.Argument(...)
        if not (has_default and isinstance(default_node, ast.Call)):
            continue
        call_func = default_node.func
        if not (isinstance(call_func, ast.Attribute) and isinstance(call_func.value, ast.Name)):
            continue
        if call_func.value.id != "typer":
            continue
        if call_func.attr not in ("Option", "Argument"):
            continue

        is_argument = call_func.attr == "Argument"

        # Type from annotation
        param_type = _annotation_to_type(arg.annotation)

        # Required if first arg is ... (Ellipsis)
        required = False
        if default_node.args:
            first = default_node.args[0]
            if isinstance(first, ast.Constant) and first.value is ...:
                required = True

        # Default value (first arg if not ...)
        default_val = ""
        if default_node.args and not required:
            first = default_node.args[0]
            if isinstance(first, ast.Constant) and first.value is not ...:
                default_val = str(first.value)

        # Help text
        help_text = ""
        for kw in default_node.keywords:
            if kw.arg == "help" and isinstance(kw.value, ast.Constant):
                help_text = str(kw.value.value)

        params.append(ParameterSpec(
            name=arg.arg,
            type=param_type,
            description=help_text,
            required=required,
            default=default_val if default_val else None,
        ))

    return params


def _extract_function(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    source_file: str,
    class_name: str = "",
) -> ExtractedFunction:
    """Extract function metadata from an AST node."""
    # Docstring
    docstring = ast.get_docstring(node) or ""

    # Parameters
    params: list[ParameterSpec] = []
    args = node.args

    # Calculate which args have defaults
    num_args = len(args.args)
    num_defaults = len(args.defaults)
    first_default_idx = num_args - num_defaults

    for i, arg in enumerate(args.args):
        if arg.arg in ("self", "cls"):
            continue

        has_default = i >= first_default_idx
        default_node = args.defaults[i - first_default_idx] if has_default else None
        default_val = _get_default_str(default_node) if has_default else None
        is_required = not has_default

        # Try to extract description from docstring
        param_desc = _extract_param_doc(docstring, arg.arg)

        # Extract enum values from Literal type hints
        enum_values = None
        if arg.annotation and isinstance(arg.annotation, ast.Subscript):
            if isinstance(arg.annotation.value, ast.Name) and arg.annotation.value.id == "Literal":
                enum_values = _extract_literal_values(arg.annotation.slice)

        params.append(
            ParameterSpec(
                name=arg.arg,
                type=_annotation_to_type(arg.annotation),
                description=param_desc,
                required=is_required,
                default=default_val,
                enum_values=enum_values,
            )
        )

    # Keyword-only args
    for i, arg in enumerate(args.kwonlyargs):
        default_node = args.kw_defaults[i]
        default_val = _get_default_str(default_node) if default_node else None
        is_required = default_node is None

        params.append(
            ParameterSpec(
                name=arg.arg,
                type=_annotation_to_type(arg.annotation),
                description=_extract_param_doc(docstring, arg.arg),
                required=is_required,
                default=default_val,
            )
        )

    # Return type
    return_type = _annotation_to_type(node.returns)

    # Decorators
    decorators = _get_decorator_names(node.decorator_list)

    # Override params with richer click/typer extraction if applicable
    has_click_decs = any(
        "click.option" in d or "click.argument" in d or "click.command" in d
        for d in decorators
    )
    if has_click_decs:
        click_params = _extract_click_params(node)
        if click_params:
            params = click_params
    else:
        # Try Typer: check if any param default is typer.Option/typer.Argument
        typer_params = _extract_typer_params(node)
        if typer_params:
            params = typer_params

    # Analyze function body for patterns that make it unsuitable as a tool
    returns_callable = _body_returns_callable(node)
    calls_sys_exit = _body_calls_sys_exit(node)

    return ExtractedFunction(
        name=node.name,
        docstring=docstring.split("\n")[0] if docstring else "",
        parameters=params,
        return_type=return_type,
        decorators=decorators,
        is_method=bool(class_name),
        is_private=node.name.startswith("_"),
        class_name=class_name,
        source_file=source_file,
        line_number=node.lineno,
        returns_callable=returns_callable,
        calls_sys_exit=calls_sys_exit,
    )


def _extract_param_doc(docstring: str, param_name: str) -> str:
    """Extract parameter description from docstring (Google/NumPy/Sphinx style)."""
    if not docstring:
        return ""

    lines = docstring.split("\n")
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Google style: param_name: description
        # Sphinx style: :param param_name: description
        if stripped.startswith(f"{param_name}:") or stripped.startswith(f"{param_name} :"):
            return stripped.split(":", 1)[1].strip()
        if stripped.startswith(f":param {param_name}:"):
            return stripped.split(":", 2)[2].strip()
        # Numpy style: param_name : type
        if stripped.startswith(f"{param_name} :"):
            # Description is on the next line
            if i + 1 < len(lines):
                return lines[i + 1].strip()

    return ""


def _extract_literal_values(node: ast.expr) -> Optional[list[str]]:
    """Extract values from Literal[...] type annotation."""
    values = []
    if isinstance(node, ast.Tuple):
        for elt in node.elts:
            if isinstance(elt, ast.Constant):
                values.append(str(elt.value))
    elif isinstance(node, ast.Constant):
        values.append(str(node.value))
    return values if values else None


def _extract_argparse_argument(node: ast.Call) -> Optional[dict]:
    """Extract argument details from an add_argument() call.

    Returns a dict with name, type, help, required, default, choices, or None
    if the call can't be parsed.
    """
    if not node.args:
        return None
    first_arg = node.args[0]
    if not isinstance(first_arg, ast.Constant) or not isinstance(first_arg.value, str):
        return None

    flag_str = first_arg.value
    is_positional = not flag_str.startswith("-")

    # Determine the parameter name
    if is_positional:
        name = flag_str.replace("-", "_")
    else:
        # Prefer long flag (--name) over short flag (-n)
        name = None
        for arg in node.args:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                if arg.value.startswith("--"):
                    name = arg.value.lstrip("-").replace("-", "_")
                    break
        if not name:
            name = flag_str.lstrip("-").replace("-", "_")

    # Extract keyword arguments
    help_text = ""
    arg_type = "string"
    default = None
    choices = None
    required = is_positional  # positional args are required by default
    action = None

    for kw in node.keywords:
        if not isinstance(kw.value, ast.Constant):
            # Handle type=int, type=str etc. (ast.Name)
            if kw.arg == "type" and isinstance(kw.value, ast.Name):
                type_map = {"str": "string", "int": "integer", "float": "float", "bool": "boolean"}
                arg_type = type_map.get(kw.value.id, "string")
            # Handle choices=[...] (ast.List)
            elif kw.arg == "choices" and isinstance(kw.value, ast.List):
                choices = []
                for elt in kw.value.elts:
                    if isinstance(elt, ast.Constant):
                        choices.append(str(elt.value))
            continue

        val = kw.value.value
        if kw.arg == "help":
            help_text = str(val)
        elif kw.arg == "default":
            default = str(val) if val is not None else None
        elif kw.arg == "required":
            required = bool(val)
        elif kw.arg == "action":
            action = str(val)

    # store_true / store_false → boolean type, not required
    if action in ("store_true", "store_false"):
        arg_type = "boolean"
        required = False
        default = "False" if action == "store_true" else "True"

    return {
        "name": name,
        "type": arg_type,
        "help": help_text,
        "required": required,
        "default": default,
        "choices": choices,
        "is_positional": is_positional,
    }


def _detect_argparse_subcommands(tree: ast.Module) -> list[dict]:
    """Detect argparse subcommand definitions and their arguments from AST.

    Tracks which variable holds each subparser result so that subsequent
    add_argument() calls can be associated with the correct subcommand.
    """
    subcommands: list[dict] = []
    # Map variable names to their subcommand index in the list
    parser_vars: dict[str, int] = {}
    # Track top-level parser variable for global arguments
    top_parser_var: Optional[str] = None
    global_arguments: list[dict] = []

    class ArgparseVisitor(ast.NodeVisitor):
        def visit_Assign(self, node: ast.Assign):
            nonlocal top_parser_var
            # Detect: parser = argparse.ArgumentParser(...)
            if (
                len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and isinstance(node.value, ast.Call)
            ):
                target_name = node.targets[0].id
                call = node.value
                # ArgumentParser() call
                if isinstance(call.func, ast.Attribute) and call.func.attr == "ArgumentParser":
                    top_parser_var = target_name
                elif isinstance(call.func, ast.Name) and call.func.id == "ArgumentParser":
                    top_parser_var = target_name

                # proc = subparsers.add_parser("name", ...)
                if isinstance(call.func, ast.Attribute) and call.func.attr == "add_parser":
                    if call.args and isinstance(call.args[0], ast.Constant):
                        cmd_name = str(call.args[0].value)
                        help_text = ""
                        for kw in call.keywords:
                            if kw.arg == "help" and isinstance(kw.value, ast.Constant):
                                help_text = str(kw.value.value)
                        subcommands.append({"name": cmd_name, "help": help_text, "arguments": []})
                        parser_vars[target_name] = len(subcommands) - 1

            self.generic_visit(node)

        def visit_Expr(self, node: ast.Expr):
            # Handle standalone calls like: subparsers.add_parser(...) without assignment
            if isinstance(node.value, ast.Call):
                call = node.value
                if isinstance(call.func, ast.Attribute) and call.func.attr == "add_parser":
                    if call.args and isinstance(call.args[0], ast.Constant):
                        cmd_name = str(call.args[0].value)
                        help_text = ""
                        for kw in call.keywords:
                            if kw.arg == "help" and isinstance(kw.value, ast.Constant):
                                help_text = str(kw.value.value)
                        subcommands.append({"name": cmd_name, "help": help_text, "arguments": []})

            self.generic_visit(node)

        def visit_Call(self, node: ast.Call):
            # var.add_argument("--flag", ...)
            if isinstance(node.func, ast.Attribute) and node.func.attr == "add_argument":
                arg_info = _extract_argparse_argument(node)
                if arg_info:
                    # Figure out which parser this belongs to
                    if isinstance(node.func.value, ast.Name):
                        var_name = node.func.value.id
                        if var_name in parser_vars:
                            idx = parser_vars[var_name]
                            subcommands[idx]["arguments"].append(arg_info)
                        elif var_name == top_parser_var:
                            global_arguments.append(arg_info)

            self.generic_visit(node)

    # We need to handle the dual nonlocal issue — use a simple approach
    # by making top_parser_var mutable via list
    ArgparseVisitor().visit(tree)

    # Attach global arguments to all subcommands that have no arguments yet
    if global_arguments and subcommands:
        for subcmd in subcommands:
            if not subcmd["arguments"]:
                # Don't copy global args — they're on the parent parser
                pass

    return subcommands


def analyze_python_file(root: Path, file_info: FileInfo) -> Optional[ASTAnalysisResult]:
    """Analyze a single Python file using AST."""
    if file_info.language != Language.PYTHON:
        return None

    try:
        source = (root / file_info.path).read_text(errors="replace")
        tree = ast.parse(source)
    except (OSError, SyntaxError):
        return None

    result = ASTAnalysisResult()

    # Check imports for framework detection
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "argparse":
                    result.has_argparse = True
                elif alias.name == "click":
                    result.has_click = True
                elif alias.name == "typer":
                    result.has_typer = True
        elif isinstance(node, ast.ImportFrom):
            if node.module == "argparse" or (node.module and node.module.startswith("argparse")):
                result.has_argparse = True
            elif node.module == "click" or (node.module and node.module.startswith("click")):
                result.has_click = True
            elif node.module == "typer" or (node.module and node.module.startswith("typer")):
                result.has_typer = True

    # Detect argparse subcommands
    if result.has_argparse:
        result.subcommands = _detect_argparse_subcommands(tree)

    # Extract top-level functions
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func = _extract_function(node, file_info.path)
            result.functions.append(func)

            # Check if it's a CLI command (click/typer decorated)
            if any(d in CLI_COMMAND_DECORATORS or "command" in d for d in func.decorators):
                result.cli_commands.append(func)

        elif isinstance(node, ast.ClassDef):
            class_doc = ast.get_docstring(node) or ""
            bases = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    bases.append(base.id)
                elif isinstance(base, ast.Attribute):
                    bases.append(base.attr)

            methods = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append(_extract_function(item, file_info.path, node.name))

            result.classes.append(
                ExtractedClass(
                    name=node.name,
                    docstring=class_doc.split("\n")[0] if class_doc else "",
                    bases=bases,
                    methods=methods,
                    source_file=file_info.path,
                )
            )

    return result


MAX_TOOLS = 200  # Cap to avoid overwhelming the server with hundreds of tools


def ast_results_to_capabilities(
    results: dict[str, ASTAnalysisResult],
    primary_ipc: Optional[IPCType],
) -> list[Capability]:
    """Convert AST analysis results into Capability objects.

    Strategy (in priority order):
    1. CLI commands (click/typer decorated functions) → tools directly
    2. Argparse subcommands → tools
    3. Public top-level functions with docstrings → tools
    4. Public methods on non-private classes with docstrings → tools

    Stops at MAX_TOOLS to avoid generating an unusable number of tools.
    """
    capabilities: list[Capability] = []
    seen_names: set[str] = set()

    for file_path, result in results.items():
        # 1. CLI commands from decorators
        for func in result.cli_commands:
            cap = _func_to_capability(func, "cli_command", primary_ipc)
            if cap.name not in seen_names:
                capabilities.append(cap)
                seen_names.add(cap.name)

        # 2. Argparse subcommands
        for subcmd in result.subcommands:
            name = subcmd["name"].replace("-", "_")
            if name not in seen_names:
                # Build parameters from extracted add_argument() calls
                arguments = subcmd.get("arguments", [])
                if arguments:
                    params = []
                    for arg in arguments:
                        params.append(
                            ParameterSpec(
                                name=arg["name"],
                                type=arg.get("type", "string"),
                                description=arg.get("help", ""),
                                required=arg.get("required", False),
                                default=arg.get("default"),
                                enum_values=arg.get("choices"),
                            )
                        )
                else:
                    # Fallback: generic args passthrough
                    params = [
                        ParameterSpec(
                            name="args",
                            type="string",
                            description=f"Arguments for {subcmd['name']}",
                            required=False,
                        )
                    ]
                capabilities.append(
                    Capability(
                        name=name,
                        description=subcmd.get("help", f"Run {subcmd['name']} command"),
                        category="cli_command",
                        parameters=params,
                        source_file=file_path,
                        ipc_type=primary_ipc,
                    )
                )
                seen_names.add(name)

        # 3. Public top-level functions (not private, not in SKIP_NAMES)
        for func in result.functions:
            if _should_skip_function(func):
                continue
            if func in result.cli_commands:
                continue

            cap = _func_to_capability(func, _categorize_function(func), primary_ipc)
            if cap.name not in seen_names:
                capabilities.append(cap)
                seen_names.add(cap.name)

        # 4. Public methods on classes
        for cls in result.classes:
            if cls.name.startswith("_"):
                continue
            # Skip test classes and mixin-only classes
            if any(b.startswith("Test") for b in cls.bases):
                continue

            # Extract __init__ params for auto-instantiation
            init_params: list[ParameterSpec] = []
            for method in cls.methods:
                if method.name == "__init__":
                    init_params = [p for p in method.parameters if p.name != "self"]
                    break

            for method in cls.methods:
                if _should_skip_function(method):
                    continue
                # Skip methods with names too generic to be useful standalone
                if method.name in _GENERIC_METHOD_NAMES:
                    continue

                cap = _func_to_capability(
                    method,
                    _snake_case(cls.name),
                    primary_ipc,
                )
                qualified_name = f"{_snake_case(cls.name)}_{method.name}"
                cap.name = qualified_name
                cap.source_class = cls.name
                cap.init_params = init_params
                if qualified_name not in seen_names:
                    capabilities.append(cap)
                    seen_names.add(qualified_name)

    # Prioritize: CLI commands first, then documented functions, then the rest
    def _priority(cap: Capability) -> tuple:
        is_cli = cap.category == "cli_command"
        has_doc = bool(cap.description and cap.description != f"Call {cap.source_function}")
        return (not is_cli, not has_doc, cap.name)

    capabilities.sort(key=_priority)

    if len(capabilities) > MAX_TOOLS:
        capabilities = capabilities[:MAX_TOOLS]

    return capabilities


def _should_skip_function(func: ExtractedFunction) -> bool:
    """Decide whether a function should be excluded from tool generation."""
    if func.is_private:
        return True
    if func.name in SKIP_NAMES or func.name in SKIP_FUNCTION_NAMES:
        return True
    if any(func.name.startswith(p) for p in SKIP_PREFIXES):
        return True
    if any(func.name.endswith(s) for s in SKIP_SUFFIXES):
        return True
    # Skip function factories that return closures — not useful as tools
    if func.returns_callable:
        return True
    # Skip functions that call sys.exit() — destructive
    if func.calls_sys_exit:
        return True
    # Skip functions with no parameters, no docstring, and a generic name
    if not func.parameters and not func.docstring and not func.decorators:
        # Keep functions whose names suggest useful actions
        action_words = {"help", "version", "info", "show", "print", "display", "list", "dump", "reset", "clear", "init", "close", "open", "connect", "disconnect"}
        name_parts = set(func.name.lower().split("_"))
        if not name_parts & action_words:
            return True
    return False


def _func_to_capability(
    func: ExtractedFunction,
    category: str,
    primary_ipc: Optional[IPCType],
) -> Capability:
    """Convert an ExtractedFunction to a Capability."""
    # Generate a readable description from the function name if no docstring
    if func.docstring:
        description = func.docstring
    else:
        readable_name = func.name.replace("_", " ")
        description = readable_name[0].upper() + readable_name[1:]

    return Capability(
        name=func.name,
        description=description,
        category=category,
        parameters=func.parameters,
        return_type=func.return_type,
        source_file=func.source_file,
        source_function=func.name,
        ipc_type=primary_ipc,
    )


def _categorize_function(func: ExtractedFunction) -> str:
    """Guess a category from function name patterns."""
    name = func.name.lower()
    prefixes = {
        "get_": "query", "list_": "query", "fetch_": "query", "search_": "query",
        "set_": "config", "update_": "config", "configure_": "config",
        "create_": "creation", "add_": "creation", "new_": "creation",
        "delete_": "management", "remove_": "management", "clear_": "management",
        "read_": "file_ops", "write_": "file_ops", "load_": "file_ops",
        "save_": "file_ops", "export_": "file_ops", "import_": "file_ops",
        "render_": "rendering", "draw_": "rendering", "paint_": "rendering",
        "convert_": "conversion", "transform_": "conversion", "parse_": "conversion",
        "run_": "execution", "execute_": "execution", "start_": "execution",
        "stop_": "execution",
        "process_": "processing",
    }
    for prefix, cat in prefixes.items():
        if name.startswith(prefix):
            return cat
    return "general"


def _snake_case(name: str) -> str:
    """Convert CamelCase to snake_case."""
    import re
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    s = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", s)
    return s.lower()
