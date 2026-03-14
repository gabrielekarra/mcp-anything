"""AST-based Python analyzer for Flask and FastAPI route endpoints.

Extracts HTTP routes, path parameters, query parameters, and request
bodies from Flask/FastAPI source files using Python's AST module.
"""

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from mcp_anything.models.analysis import Capability, FileInfo, IPCType, Language, ParameterSpec

# HTTP method decorators
_ROUTE_METHODS = {"get", "post", "put", "delete", "patch", "head", "options"}

# Python type → MCP type
_TYPE_MAP = {
    "str": "string",
    "int": "integer",
    "float": "float",
    "bool": "boolean",
    "list": "array",
    "dict": "object",
    "List": "array",
    "Dict": "object",
    "Optional": "string",
}

# Parameters that are framework-injected, not user-provided
_SKIP_PARAMS = {
    "request", "response", "session", "db", "current_user",
    "background_tasks", "websocket",
}

# Type annotation names that indicate framework-injected dependencies
_SKIP_TYPE_ANNOTATIONS = {
    "Request", "Response", "Session", "BackgroundTasks", "WebSocket",
    "Depends", "SessionDep", "CurrentUser",
}


@dataclass
class RouteEndpoint:
    """A route extracted from Flask/FastAPI source."""

    http_method: str
    path: str
    function_name: str
    description: str
    parameters: list[ParameterSpec]
    return_type: str
    source_file: str
    framework: str  # "flask" or "fastapi"


@dataclass
class FlaskFastAPIAnalysisResult:
    """Result of analyzing Python files for Flask/FastAPI routes."""

    routes: list[RouteEndpoint] = field(default_factory=list)
    app_variable: str = ""
    framework: str = ""  # "flask" or "fastapi"
    has_blueprints: bool = False
    has_routers: bool = False


def _annotation_to_mcp_type(node: Optional[ast.expr]) -> str:
    """Convert a Python type annotation AST node to MCP type string."""
    if node is None:
        return "string"
    if isinstance(node, ast.Name):
        return _TYPE_MAP.get(node.id, "string")
    if isinstance(node, ast.Constant):
        return str(node.value)
    if isinstance(node, ast.Subscript):
        if isinstance(node.value, ast.Name):
            base = node.value.id
            if base in ("Optional", "Union"):
                return _annotation_to_mcp_type(node.slice)
            return _TYPE_MAP.get(base, "string")
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        left = _annotation_to_mcp_type(node.left)
        right = _annotation_to_mcp_type(node.right)
        return left if right == "null" else left
    return "string"


def _get_default_value(node: Optional[ast.expr]) -> Optional[str]:
    """Extract a literal default value from an AST node."""
    if node is None:
        return None
    if isinstance(node, ast.Constant):
        if node.value is None:
            return None
        return str(node.value)
    return None


def _extract_fastapi_param_info(default_node: ast.Call) -> dict:
    """Extract info from FastAPI's Query(), Path(), Body() defaults."""
    info: dict = {}
    func = default_node.func

    # Identify the FastAPI param type
    if isinstance(func, ast.Name):
        param_kind = func.id  # Query, Path, Body
    elif isinstance(func, ast.Attribute):
        param_kind = func.attr
    else:
        return info

    info["kind"] = param_kind.lower()  # "query", "path", "body"

    # First positional arg is often the default value
    if default_node.args:
        first = default_node.args[0]
        if isinstance(first, ast.Constant):
            if first.value is not ...:
                info["default"] = str(first.value)
            else:
                info["required"] = True

    # Extract keyword arguments
    for kw in default_node.keywords:
        if kw.arg == "description" and isinstance(kw.value, ast.Constant):
            info["description"] = str(kw.value.value)
        elif kw.arg == "default" and isinstance(kw.value, ast.Constant):
            if kw.value.value is not None:
                info["default"] = str(kw.value.value)
        elif kw.arg == "min_length" and isinstance(kw.value, ast.Constant):
            info["min_length"] = kw.value.value
        elif kw.arg == "max_length" and isinstance(kw.value, ast.Constant):
            info["max_length"] = kw.value.value
        elif kw.arg == "ge" and isinstance(kw.value, ast.Constant):
            info["ge"] = kw.value.value
        elif kw.arg == "le" and isinstance(kw.value, ast.Constant):
            info["le"] = kw.value.value
        elif kw.arg == "alias" and isinstance(kw.value, ast.Constant):
            info["alias"] = str(kw.value.value)

    return info


def _extract_path_params(path: str) -> set[str]:
    """Extract path parameter names from a route path.

    Handles both Flask-style <name> and FastAPI-style {name}.
    """
    params = set()
    # FastAPI: /users/{user_id}
    for match in re.finditer(r"\{(\w+)\}", path):
        params.add(match.group(1))
    # Flask: /users/<int:user_id> or /users/<user_id>
    for match in re.finditer(r"<(?:\w+:)?(\w+)>", path):
        params.add(match.group(1))
    return params


def _extract_route_decorator(
    decorator: ast.expr,
    app_vars: set[str],
    router_vars: set[str],
) -> Optional[tuple[str, str]]:
    """Extract HTTP method and path from a route decorator.

    Returns (http_method, path) or None if not a route decorator.
    """
    if not isinstance(decorator, ast.Call):
        return None

    func = decorator.func
    if not isinstance(func, ast.Attribute):
        return None
    if not isinstance(func.value, ast.Name):
        return None

    obj_name = func.value.id
    method_name = func.attr

    # Must be on a known app/router/blueprint variable
    if obj_name not in app_vars and obj_name not in router_vars:
        return None

    # @app.route("/path", methods=["GET"])
    if method_name == "route":
        if not decorator.args:
            return None
        path_arg = decorator.args[0]
        if not isinstance(path_arg, ast.Constant) or not isinstance(path_arg.value, str):
            return None
        path = path_arg.value

        # Extract methods=["GET", "POST"]
        http_method = "GET"
        for kw in decorator.keywords:
            if kw.arg == "methods" and isinstance(kw.value, ast.List):
                methods = []
                for elt in kw.value.elts:
                    if isinstance(elt, ast.Constant):
                        methods.append(str(elt.value).upper())
                if methods:
                    http_method = methods[0]  # Use first method
        return http_method, path

    # @app.get("/path"), @app.post("/path"), etc.
    if method_name in _ROUTE_METHODS:
        path = "/"
        if decorator.args:
            path_arg = decorator.args[0]
            if isinstance(path_arg, ast.Constant) and isinstance(path_arg.value, str):
                path = path_arg.value
        return method_name.upper(), path

    return None


def _extract_function_params(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    path_params: set[str],
    framework: str,
) -> list[ParameterSpec]:
    """Extract parameters from a route handler function."""
    params: list[ParameterSpec] = []
    args = node.args

    num_args = len(args.args)
    num_defaults = len(args.defaults)
    first_default_idx = num_args - num_defaults

    for i, arg in enumerate(args.args):
        name = arg.arg
        if name in ("self", "cls"):
            continue
        if name in _SKIP_PARAMS:
            continue

        has_default = i >= first_default_idx
        default_node = args.defaults[i - first_default_idx] if has_default else None

        # Skip params with dependency injection type annotations
        if arg.annotation and isinstance(arg.annotation, ast.Name):
            if arg.annotation.id in _SKIP_TYPE_ANNOTATIONS:
                continue
        # Skip params with Annotated[..., Depends(...)] or similar
        if arg.annotation and isinstance(arg.annotation, ast.Subscript):
            if isinstance(arg.annotation.value, ast.Name) and arg.annotation.value.id == "Annotated":
                # Check if any element in the subscript is a Depends() call
                slice_node = arg.annotation.slice
                if isinstance(slice_node, ast.Tuple):
                    for elt in slice_node.elts:
                        if isinstance(elt, ast.Call):
                            call_name = ""
                            if isinstance(elt.func, ast.Name):
                                call_name = elt.func.id
                            elif isinstance(elt.func, ast.Attribute):
                                call_name = elt.func.attr
                            if call_name == "Depends":
                                break
                    else:
                        pass  # No Depends found, continue processing
                    # If we found Depends, skip this param
                    if any(
                        isinstance(elt, ast.Call) and (
                            (isinstance(elt.func, ast.Name) and elt.func.id == "Depends")
                            or (isinstance(elt.func, ast.Attribute) and elt.func.attr == "Depends")
                        )
                        for elt in (slice_node.elts if isinstance(slice_node, ast.Tuple) else [])
                    ):
                        continue

        # Skip params whose default is Depends(...)
        if has_default and isinstance(default_node, ast.Call):
            dep_func = default_node.func
            if (isinstance(dep_func, ast.Name) and dep_func.id == "Depends") or \
               (isinstance(dep_func, ast.Attribute) and dep_func.attr == "Depends"):
                continue

        # Determine type
        param_type = _annotation_to_mcp_type(arg.annotation)

        # Check if it's a Pydantic model (class name as type) → body param
        is_body = False
        if arg.annotation and isinstance(arg.annotation, ast.Name):
            type_name = arg.annotation.id
            if type_name[0].isupper() and type_name not in _TYPE_MAP:
                is_body = True
                param_type = "object"

        # Check for FastAPI param annotations: Query(), Path(), Body()
        description = ""
        default_val = None
        required = True
        fastapi_kind = None

        if has_default and isinstance(default_node, ast.Call):
            func = default_node.func
            fastapi_param_names = {"Query", "Path", "Body", "Header", "Cookie", "Form"}
            is_fastapi_param = (
                (isinstance(func, ast.Name) and func.id in fastapi_param_names)
                or (isinstance(func, ast.Attribute) and func.attr in fastapi_param_names)
            )
            if is_fastapi_param:
                info = _extract_fastapi_param_info(default_node)
                fastapi_kind = info.get("kind")
                description = info.get("description", "")
                default_val = info.get("default")
                required = info.get("required", default_val is None)
                # Skip header/cookie params — not useful as MCP tool inputs
                if fastapi_kind in ("header", "cookie"):
                    continue
            else:
                default_val = _get_default_value(default_node)
                required = False
        elif has_default:
            default_val = _get_default_value(default_node)
            required = default_val is None and not has_default

        # Path parameters are always required
        if name in path_params:
            required = True

        # For Flask, skip non-path params without annotations (likely injected)
        if framework == "flask" and name not in path_params:
            # Flask doesn't do automatic query param injection from function args
            # Only path params are extracted from function signatures
            continue

        params.append(ParameterSpec(
            name=name,
            type=param_type,
            description=description,
            required=required,
            default=default_val,
        ))

    return params


def _make_description(func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Generate description from docstring or function name."""
    docstring = ast.get_docstring(func_node)
    if docstring:
        return docstring.split("\n")[0]
    # Convert function name to readable text
    name = func_node.name
    words = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
    words = words.replace("_", " ").strip()
    return words[0].upper() + words[1:] if words else name


def analyze_flask_fastapi_file(
    root: Path, file_info: FileInfo,
) -> Optional[FlaskFastAPIAnalysisResult]:
    """Analyze a Python file for Flask/FastAPI route endpoints."""
    if file_info.language != Language.PYTHON:
        return None

    try:
        source = (root / file_info.path).read_text(errors="replace")
        tree = ast.parse(source)
    except (OSError, SyntaxError):
        return None

    result = FlaskFastAPIAnalysisResult()

    # Step 1: Detect framework and find app/router variables
    app_vars: set[str] = set()
    router_vars: set[str] = set()
    router_prefixes: dict[str, str] = {}  # var_name → prefix path
    has_flask = False
    has_fastapi = False

    for node in ast.walk(tree):
        # import detection
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "flask":
                    has_flask = True
                elif alias.name == "fastapi":
                    has_fastapi = True
        elif isinstance(node, ast.ImportFrom):
            if node.module and "flask" in node.module:
                has_flask = True
            elif node.module and "fastapi" in node.module:
                has_fastapi = True

        # Variable assignment: app = Flask(...) or app = FastAPI(...)
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and isinstance(node.value, ast.Call):
                call_func = node.value.func
                func_name = ""
                if isinstance(call_func, ast.Name):
                    func_name = call_func.id
                elif isinstance(call_func, ast.Attribute):
                    func_name = call_func.attr

                if func_name in ("Flask", "FastAPI"):
                    app_vars.add(target.id)
                    if func_name == "Flask":
                        has_flask = True
                    else:
                        has_fastapi = True
                elif func_name == "Blueprint":
                    router_vars.add(target.id)
                    result.has_blueprints = True
                    has_flask = True
                elif func_name == "APIRouter":
                    router_vars.add(target.id)
                    result.has_routers = True
                    has_fastapi = True
                    # Extract prefix from APIRouter(prefix="/items")
                    for kw in node.value.keywords:
                        if kw.arg == "prefix" and isinstance(kw.value, ast.Constant):
                            router_prefixes[target.id] = str(kw.value.value).rstrip("/")
                    # Also check first positional arg
                    if node.value.args:
                        first = node.value.args[0]
                        if isinstance(first, ast.Constant) and isinstance(first.value, str):
                            router_prefixes[target.id] = str(first.value).rstrip("/")

    if not has_flask and not has_fastapi:
        return None

    result.framework = "fastapi" if has_fastapi else "flask"
    if app_vars:
        result.app_variable = next(iter(app_vars))

    # Step 2: Find route-decorated functions
    all_vars = app_vars | router_vars
    if not all_vars:
        # Common convention: try "app" and "router"
        all_vars = {"app", "router"}

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        for decorator in node.decorator_list:
            route_info = _extract_route_decorator(decorator, app_vars, router_vars)
            if not route_info:
                continue

            http_method, path = route_info

            # Prepend router prefix if the decorator is on a router variable
            if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                if isinstance(decorator.func.value, ast.Name):
                    var_name = decorator.func.value.id
                    prefix = router_prefixes.get(var_name, "")
                    if prefix:
                        path = prefix + path

            # Normalize path: Flask <param> → {param} for consistency
            normalized_path = re.sub(r"<(?:\w+:)?(\w+)>", r"{\1}", path)

            # Extract path params
            path_params = _extract_path_params(path)

            # Extract function parameters
            params = _extract_function_params(node, path_params, result.framework)

            # Generate description
            desc = _make_description(node)

            endpoint = RouteEndpoint(
                http_method=http_method,
                path=normalized_path,
                function_name=node.name,
                description=desc,
                parameters=params,
                return_type="object",
                source_file=file_info.path,
                framework=result.framework,
            )
            result.routes.append(endpoint)
            break  # Only use the first matching decorator per function

    return result if (result.routes or has_flask or has_fastapi) else None


def flask_fastapi_results_to_capabilities(
    results: dict[str, FlaskFastAPIAnalysisResult],
) -> list[Capability]:
    """Convert Flask/FastAPI analysis results into Capability objects."""
    capabilities: list[Capability] = []
    seen: set[str] = set()

    for file_path, result in results.items():
        for ep in result.routes:
            tool_name = _endpoint_to_tool_name(ep)

            if tool_name in seen:
                continue
            seen.add(tool_name)

            # Include HTTP method and path in description for design phase
            desc = f"{ep.http_method} {ep.path} - {ep.description}"

            capabilities.append(Capability(
                name=tool_name,
                description=desc,
                category="api",
                parameters=ep.parameters,
                return_type=ep.return_type,
                source_file=file_path,
                source_function=ep.function_name,
                ipc_type=IPCType.PROTOCOL,
            ))

    return capabilities


def _endpoint_to_tool_name(ep: RouteEndpoint) -> str:
    """Generate a snake_case tool name from a route endpoint."""
    path_parts = ep.path.strip("/").split("/")
    # Remove common prefixes
    if path_parts and path_parts[0] in ("api", "v1", "v2", "v3"):
        path_parts = path_parts[1:]

    clean_parts = []
    for part in path_parts:
        # {id} → by_id
        if part.startswith("{") and part.endswith("}"):
            clean_parts.append(f"by_{part[1:-1]}")
        else:
            clean_parts.append(part)

    method_prefix = ep.http_method.lower()
    path_name = "_".join(clean_parts) if clean_parts else ep.function_name

    name = f"{method_prefix}_{path_name}"
    name = re.sub(r"[^a-z0-9_]", "_", name.lower())
    name = re.sub(r"_+", "_", name).strip("_")
    return name
