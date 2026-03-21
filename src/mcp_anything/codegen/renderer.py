"""Jinja2 template renderer with Python-specific filters."""

import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape


def _safe_identifier(value: str) -> str:
    """Ensure a string is a valid Python identifier.

    Strips non-alphanumeric characters, prefixes leading digits with
    ``p_``, and collapses reserved words with a trailing underscore.
    """
    import keyword

    s = re.sub(r"[^a-zA-Z0-9_]", "_", value)
    s = re.sub(r"_+", "_", s).strip("_")
    if not s:
        return "param"
    if s[0].isdigit():
        s = f"p_{s}"
    if keyword.iskeyword(s):
        s = f"{s}_"
    return s


def _snake_case(value: str) -> str:
    """Convert string to snake_case."""
    s = re.sub(r"[^a-zA-Z0-9]", "_", value)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s)
    s = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", s)
    return re.sub(r"_+", "_", s).strip("_").lower()


def _pascal_case(value: str) -> str:
    """Convert string to PascalCase."""
    return "".join(word.capitalize() for word in _snake_case(value).split("_"))


def _kebab_case(value: str) -> str:
    """Convert string to kebab-case."""
    return _snake_case(value).replace("_", "-")


_SAFE_TYPES = {"str", "int", "float", "bool", "list", "dict", "None"}

def _python_type(type_str: str) -> str:
    """Map type strings to safe Python built-in type annotations.

    Only emits types that need no imports. Unknown/complex types from
    the target project (Callable, TokenList, etc.) are mapped to str
    since MCP tool arguments arrive as JSON primitives.
    """
    mapping = {
        "string": "str",
        "integer": "int",
        "float": "float",
        "boolean": "bool",
        "number": "float",
        "array": "list",
        "object": "dict",
        "dict": "dict",
        "list": "list",
        "any": "str",
        "none": "None",
        "null": "None",
        "bytes": "str",
        "path": "str",
    }
    result = mapping.get(type_str.lower())
    if result:
        return result
    # If it's already a safe built-in type, use it
    if type_str in _SAFE_TYPES:
        return type_str
    # Unknown/complex type → default to str (safe, no imports needed)
    return "str"


def _default_value(param) -> str:
    """Generate a Python default value expression.

    Always returns None for optional parameters so that only explicitly
    provided values are sent to the backend.  This avoids conflicts where
    an API rejects mutually-exclusive query params that both carry their
    OpenAPI-spec defaults (e.g. GitHub's type + affiliation).
    """
    if not param.required:
        return "None"
    return ""


def _safe_docstring(value: str) -> str:
    """Sanitize a string for use inside triple-quoted Python docstrings.

    Escapes backslashes and triple quotes so the generated code is always valid.
    """
    if not value:
        return value
    # Escape backslashes first, then triple quotes
    value = value.replace("\\", "\\\\")
    value = value.replace('"""', '\\"\\"\\"')
    # Strip to single line — multi-line docstrings from source code
    # can break generated template formatting
    first_line = value.split("\n")[0].strip()
    return first_line


def _param_model_name(param) -> str:
    """Generate a PascalCase Pydantic model name for a param with nested properties."""
    return _pascal_case(param.name) + "Input"


def _has_properties(param) -> bool:
    """Check if a param has nested properties (for Jinja2 test)."""
    return bool(getattr(param, "properties", None))


def create_jinja_env() -> Environment:
    """Create a configured Jinja2 environment for code generation."""
    templates_dir = Path(__file__).parent / "templates"
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape([]),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )

    env.filters["safe_identifier"] = _safe_identifier
    env.filters["snake_case"] = _snake_case
    env.filters["pascal_case"] = _pascal_case
    env.filters["kebab_case"] = _kebab_case
    env.filters["python_type"] = _python_type
    env.filters["default_value"] = _default_value
    env.filters["safe_docstring"] = _safe_docstring
    env.filters["param_model_name"] = _param_model_name
    env.tests["has_properties"] = _has_properties

    return env
