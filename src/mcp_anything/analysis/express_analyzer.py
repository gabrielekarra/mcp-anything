"""Regex-based analyzer for Express.js route endpoints.

Extracts HTTP routes, path parameters, query parameters, and request
bodies from Express.js source files using regex patterns.
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from mcp_anything.models.analysis import Capability, FileInfo, IPCType, Language, ParameterSpec
from mcp_anything.analysis.route_utils import endpoint_to_tool_name, normalize_path, make_description


@dataclass
class ExpressEndpoint:
    """A route extracted from Express.js source."""

    http_method: str
    path: str
    function_name: str
    description: str
    parameters: list[ParameterSpec]
    source_file: str


@dataclass
class ExpressAnalysisResult:
    """Result of analyzing JS/TS files for Express routes."""

    routes: list[ExpressEndpoint] = field(default_factory=list)
    framework: str = "express"
    has_routers: bool = False


# Regex for route definitions: app.get('/path', handler) or router.post('/path', ...)
_ROUTE_RE = re.compile(
    r"(app|router|\w+Router|\w+)\."
    r"(get|post|put|delete|patch|all)\s*\(\s*"
    r"['\"]([^'\"]+)['\"]",
    re.IGNORECASE,
)

# Chained route pattern: router.route('/path').get(...).post(...)
_ROUTE_CHAIN_RE = re.compile(
    r"(\w+)\.route\s*\(\s*['\"]([^'\"]+)['\"]\s*\)"
)
_CHAIN_METHOD_RE = re.compile(
    r"\.(get|post|put|delete|patch)\s*\(",
    re.IGNORECASE,
)

# Regex for router mount: app.use('/prefix', router)
_ROUTER_USE_RE = re.compile(
    r"app\.use\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*(\w+)",
)

# Regex for require: const varName = require('./path')
_REQUIRE_RE = re.compile(
    r"(?:const|let|var)\s+(\w+)\s*=\s*require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)",
)

# Regex for ES module import: import varName from './path'
_IMPORT_RE = re.compile(
    r"import\s+(\w+)\s+from\s+['\"]([^'\"]+)['\"]",
)

# Regex for handler function name in route: app.get('/path', handlerName)
_HANDLER_NAME_RE = re.compile(
    r"\.(get|post|put|delete|patch)\s*\(\s*"
    r"['\"][^'\"]+['\"]\s*,\s*"
    r"(?:[\w.]+,\s*)*"  # skip middleware
    r"(\w+)\s*\)",
)

# Regex for inline handler: app.get('/path', (req, res) => { or function(req, res) {
_INLINE_HANDLER_RE = re.compile(
    r"\.(get|post|put|delete|patch)\s*\(\s*"
    r"['\"]([^'\"]+)['\"]\s*,\s*"
    r"(?:[\w.]+,\s*)*"  # skip middleware
    r"(?:async\s+)?"
    r"(?:\(\s*(?:req|request)\s*,\s*(?:res|response)|function\s*\(\s*(?:req|request)\s*,\s*(?:res|response))",
)

# Extract params from handler body: req.params.id, req.query.limit, req.body.name
_REQ_PARAM_RE = re.compile(r"req\.params\.(\w+)")
_REQ_QUERY_RE = re.compile(r"req\.query\.(\w+)")
_REQ_BODY_RE = re.compile(r"req\.body\.(\w+)")

# Destructured params: const { id } = req.params
# Optional TS type annotation before `=`: const { id }: { id: string } = req.params
_TS_TYPE_ANNOTATION = r"(?:\s*:\s*\{[^}]*\})?"
_DESTRUCTURE_PARAMS_RE = re.compile(
    r"(?:const|let|var)\s*\{([^}]+)\}" + _TS_TYPE_ANNOTATION + r"\s*=\s*req\.params"
)
_DESTRUCTURE_QUERY_RE = re.compile(
    r"(?:const|let|var)\s*\{([^}]+)\}" + _TS_TYPE_ANNOTATION + r"\s*=\s*req\.query"
)
_DESTRUCTURE_BODY_RE = re.compile(
    r"(?:const|let|var)\s*\{([^}]+)\}" + _TS_TYPE_ANNOTATION + r"\s*=\s*req\.body"
)

# ── TypeScript type-hint patterns ────────────────────────────────────────────

# `as number` / `as string` / `as boolean` cast after req.params/query access
# e.g.  req.params.id as number   or   req.query.limit as number
_TS_CAST_RE = re.compile(
    r"req\.(?:params|query|body)\.(\w+)\s+as\s+(number|string|boolean|integer|float)",
)

# parseInt / Number / parseFloat applied to a req param
# e.g.  parseInt(req.params.id)   Number(req.query.page)
_TS_PARSEINT_RE = re.compile(
    r"parseInt\s*\(\s*req\.(?:params|query)\.(\w+)",
)
_TS_PARSEFLOAT_RE = re.compile(
    r"parseFloat\s*\(\s*req\.(?:params|query)\.(\w+)",
)
_TS_NUMBER_RE = re.compile(
    r"Number\s*\(\s*req\.(?:params|query)\.(\w+)",
)

# Typed destructuring: const { id, count }: { id: string; count: number } = req.params
# Captures the whole type block and the source (params/query/body)
_TS_TYPED_DESTRUCTURE_RE = re.compile(
    r"(?:const|let|var)\s*\{[^}]+\}\s*:\s*\{([^}]+)\}\s*=\s*req\.(params|query|body)",
)

# Within the type block: `name: type`  or  `name?: type`
_TS_FIELD_TYPE_RE = re.compile(r"(\w+)\??:\s*(number|string|boolean|integer|float)")

# Request<Params, ResBody, Body, Query> generic on handler signature:
# (req: Request<{ id: string }, any, { name: string }, { page?: number }>, res) => ...
_TS_REQUEST_GENERIC_RE = re.compile(
    r"req\s*:\s*Request\s*<\s*"
    r"\{([^}]*)\}"   # group 1: Params
    r"(?:\s*,\s*[^,>]+)?"  # skip ResBody
    r"(?:\s*,\s*\{([^}]*)\})?"  # group 3: Body (optional)
    r"(?:\s*,\s*\{([^}]*)\})?"  # group 4: Query (optional)
    r"\s*>",
    re.DOTALL,
)

_TS_TYPE_MAP = {
    "number": "integer",
    "integer": "integer",
    "float": "float",
    "string": "string",
    "boolean": "boolean",
}

# routing-controllers decorators
_RC_JSON_CONTROLLER_RE = re.compile(r"@JsonController\s*\(\s*['\"]([^'\"]*)['\"]\s*\)")
_RC_METHOD_RE = re.compile(
    r"((?:\s*@[\w$]+(?:\([^)]*\))?\s*)+)\s*public\s+(\w+)\s*\((.*?)\)\s*(?::\s*[^{]+)?\{",
    re.DOTALL,
)
_RC_HTTP_DECORATOR_RE = re.compile(
    r"@(Get|Post|Put|Delete|Patch)\s*(?:\(\s*['\"]([^'\"]*)['\"]\s*\))?",
    re.IGNORECASE,
)
_RC_PARAM_RE = re.compile(r"@Param\s*\(\s*['\"]([^'\"]+)['\"]\s*\)\s*(\w+)(?:\s*:\s*([^=]+))?")
_RC_BODY_RE = re.compile(r"@Body(?:\s*\([^)]*\))?\s*(\w+)(?:\s*:\s*([^=]+))?")
_RC_QUERY_PARAM_RE = re.compile(
    r"@QueryParam\s*\(\s*['\"]([^'\"]+)['\"]\s*\)\s*(\w+)(?:\s*:\s*([^=]+))?"
)
_RC_QUERY_PARAMS_RE = re.compile(r"@QueryParams(?:\s*\([^)]*\))?\s*(\w+)(?:\s*:\s*([^=]+))?")


def _resolve_ts_types(context: str) -> dict[str, str]:
    """Scan handler context for TypeScript type hints. Returns {param_name: mcp_type}."""
    hints: dict[str, str] = {}

    # `as number/string/boolean` casts
    for m in _TS_CAST_RE.finditer(context):
        hints[m.group(1)] = _TS_TYPE_MAP.get(m.group(2), "string")

    # parseInt / parseFloat / Number wrappers
    for m in _TS_PARSEINT_RE.finditer(context):
        hints[m.group(1)] = "integer"
    for m in _TS_PARSEFLOAT_RE.finditer(context):
        hints[m.group(1)] = "float"
    for m in _TS_NUMBER_RE.finditer(context):
        hints[m.group(1)] = "integer"

    # Typed destructuring blocks
    for m in _TS_TYPED_DESTRUCTURE_RE.finditer(context):
        type_block = m.group(1)
        for field_m in _TS_FIELD_TYPE_RE.finditer(type_block):
            hints[field_m.group(1)] = _TS_TYPE_MAP.get(field_m.group(2), "string")

    # Request<Params, _, Body, Query> generic
    req_m = _TS_REQUEST_GENERIC_RE.search(context)
    if req_m:
        for block in (req_m.group(1), req_m.group(2), req_m.group(3)):
            if block:
                for field_m in _TS_FIELD_TYPE_RE.finditer(block):
                    hints[field_m.group(1)] = _TS_TYPE_MAP.get(field_m.group(2), "string")

    return hints


def _extract_params_from_context(
    source: str, route_pos: int, is_typescript: bool = False
) -> list[ParameterSpec]:
    """Extract parameters by scanning the handler body after a route definition."""
    # Look at the next ~800 chars after the route for the handler body
    context = source[route_pos:route_pos + 800]
    params: list[ParameterSpec] = []
    seen: set[str] = set()

    # Pre-compute TypeScript type hints for this handler window
    ts_types: dict[str, str] = _resolve_ts_types(context) if is_typescript else {}

    def _type_of(name: str, default: str) -> str:
        return ts_types.get(name, default)

    # Path params from req.params.X or destructured
    for match in _REQ_PARAM_RE.finditer(context):
        name = match.group(1)
        if name not in seen:
            seen.add(name)
            params.append(ParameterSpec(name=name, type=_type_of(name, "string"), required=True))
    for match in _DESTRUCTURE_PARAMS_RE.finditer(context):
        for name in re.split(r"\s*,\s*", match.group(1).strip()):
            name = name.strip().split("=")[0].strip()  # strip default value
            if name and name not in seen:
                seen.add(name)
                params.append(ParameterSpec(name=name, type=_type_of(name, "string"), required=True))

    # Query params from req.query.X or destructured
    for match in _REQ_QUERY_RE.finditer(context):
        name = match.group(1)
        if name not in seen:
            seen.add(name)
            params.append(ParameterSpec(name=name, type=_type_of(name, "string"), required=False))
    for match in _DESTRUCTURE_QUERY_RE.finditer(context):
        for name in re.split(r"\s*,\s*", match.group(1).strip()):
            name = name.strip().split("=")[0].strip()  # strip default value
            if name and name not in seen:
                seen.add(name)
                params.append(ParameterSpec(name=name, type=_type_of(name, "string"), required=False))

    # Body params from req.body.X or destructured
    for match in _REQ_BODY_RE.finditer(context):
        name = match.group(1)
        if name not in seen:
            seen.add(name)
            params.append(ParameterSpec(name=name, type=_type_of(name, "string"), required=True))
    for match in _DESTRUCTURE_BODY_RE.finditer(context):
        for name in re.split(r"\s*,\s*", match.group(1).strip()):
            name = name.strip().split("=")[0].strip()  # strip default value
            if name and name not in seen:
                seen.add(name)
                params.append(ParameterSpec(name=name, type=_type_of(name, "string"), required=True))

    return params


def _extract_path_params(path: str) -> list[ParameterSpec]:
    """Extract path parameters from Express :param syntax."""
    params = []
    for match in re.finditer(r":(\w+)", path):
        params.append(ParameterSpec(name=match.group(1), type="string", required=True))
    return params


def _extract_balanced_block(source: str, open_brace_index: int) -> str:
    """Return the text inside a balanced {...} block starting at open_brace_index."""
    depth = 0
    start = open_brace_index + 1
    for idx in range(open_brace_index, len(source)):
        char = source[idx]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[start:idx]
    return source[start:]


def _split_ts_params(signature: str) -> list[str]:
    """Split a TypeScript parameter list on top-level commas."""
    parts: list[str] = []
    current: list[str] = []
    depth_angle = depth_round = depth_curly = depth_square = 0
    for char in signature:
        if char == "<":
            depth_angle += 1
        elif char == ">":
            depth_angle = max(0, depth_angle - 1)
        elif char == "(":
            depth_round += 1
        elif char == ")":
            depth_round = max(0, depth_round - 1)
        elif char == "{":
            depth_curly += 1
        elif char == "}":
            depth_curly = max(0, depth_curly - 1)
        elif char == "[":
            depth_square += 1
        elif char == "]":
            depth_square = max(0, depth_square - 1)

        if (
            char == ","
            and depth_angle == 0
            and depth_round == 0
            and depth_curly == 0
            and depth_square == 0
        ):
            part = "".join(current).strip()
            if part:
                parts.append(part)
            current = []
            continue
        current.append(char)

    tail = "".join(current).strip()
    if tail:
        parts.append(tail)
    return parts


def _normalize_ts_type(type_name: str | None) -> str:
    """Map a TypeScript type annotation to an MCP parameter type."""
    if not type_name:
        return "string"
    cleaned = type_name.strip()
    cleaned = cleaned.split("=")[0].strip()
    cleaned = cleaned.removeprefix("Promise<").removesuffix(">")
    cleaned = cleaned.replace("| undefined", "").replace("| null", "").strip()
    bare = cleaned.split(".")[-1].strip()
    if bare.endswith("[]"):
        return "array"
    lowered = bare.lower()
    if lowered in _TS_TYPE_MAP:
        return _TS_TYPE_MAP[lowered]
    return "object"


def _extract_routing_controller_params(signature: str) -> list[ParameterSpec]:
    """Extract params from a routing-controllers method signature."""
    params: list[ParameterSpec] = []
    seen: set[str] = set()

    for part in _split_ts_params(signature):
        part = " ".join(part.split())
        if not part:
            continue

        param_match = _RC_PARAM_RE.search(part)
        if param_match:
            route_name, var_name, type_name = param_match.groups()
            if route_name not in seen:
                seen.add(route_name)
                params.append(
                    ParameterSpec(
                        name=route_name or var_name,
                        type=_normalize_ts_type(type_name),
                        required=True,
                    )
                )
            continue

        body_match = _RC_BODY_RE.search(part)
        if body_match:
            var_name, _type_name = body_match.groups()
            if var_name not in seen:
                seen.add(var_name)
                params.append(ParameterSpec(name=var_name, type="object", required=True))
            continue

        query_match = _RC_QUERY_PARAM_RE.search(part)
        if query_match:
            query_name, var_name, type_name = query_match.groups()
            if query_name not in seen:
                seen.add(query_name)
                params.append(
                    ParameterSpec(
                        name=query_name or var_name,
                        type=_normalize_ts_type(type_name),
                        required=False,
                    )
                )
            continue

        query_params_match = _RC_QUERY_PARAMS_RE.search(part)
        if query_params_match:
            var_name, _type_name = query_params_match.groups()
            if var_name not in seen:
                seen.add(var_name)
                params.append(ParameterSpec(name=var_name, type="object", required=False))

    return params


def _extract_routing_controller_routes(
    source: str,
    file_info: FileInfo,
) -> list[ExpressEndpoint]:
    """Extract routes from routing-controllers class decorators."""
    routes: list[ExpressEndpoint] = []
    for class_match in re.finditer(r"(?:export\s+)?class\s+(\w+)\s*\{", source):
        class_start = class_match.start()
        class_header = source[max(0, class_start - 500):class_start]
        controller_matches = list(_RC_JSON_CONTROLLER_RE.finditer(class_header))
        if not controller_matches:
            continue

        base_path = controller_matches[-1].group(1).rstrip("/")
        body = _extract_balanced_block(source, class_match.end() - 1)

        for method_match in _RC_METHOD_RE.finditer(body):
            decorators = method_match.group(1)
            function_name = method_match.group(2)
            signature = method_match.group(3)

            http_match = _RC_HTTP_DECORATOR_RE.search(decorators)
            if not http_match:
                continue

            http_method = http_match.group(1).upper()
            sub_path = (http_match.group(2) or "").strip()
            route_path = f"{base_path}{sub_path}" if sub_path else (base_path or "/")
            if not route_path.startswith("/"):
                route_path = "/" + route_path

            normalized = normalize_path(route_path)
            params = _extract_routing_controller_params(signature)

            routes.append(
                ExpressEndpoint(
                    http_method=http_method,
                    path=normalized,
                    function_name=function_name,
                    description=make_description(function_name),
                    parameters=params,
                    source_file=file_info.path,
                )
            )

    return routes


def build_router_mount_map(root: Path, files: list[FileInfo]) -> dict[str, str]:
    """Scan all JS/TS files to build a map of file path → mount prefix.

    Resolves cross-file router mounts by correlating require/import statements
    with app.use('/prefix', routerVar) calls.
    """
    # file_path → mount_prefix
    mount_map: dict[str, str] = {}

    for fi in files:
        if fi.language not in (Language.JAVASCRIPT, Language.TYPESCRIPT):
            continue
        try:
            source = (root / fi.path).read_text(errors="replace")
        except OSError:
            continue

        # Build var_name → resolved file path from require/import
        var_to_file: dict[str, str] = {}
        for pattern in (_REQUIRE_RE, _IMPORT_RE):
            for match in pattern.finditer(source):
                var_name = match.group(1)
                rel_path = match.group(2)
                if rel_path.startswith("."):
                    # Resolve relative to the file's directory
                    base_dir = (root / fi.path).parent
                    resolved = (base_dir / rel_path).resolve()
                    # Try common extensions
                    for ext in ("", ".js", ".ts", ".mjs"):
                        candidate = Path(str(resolved) + ext)
                        if candidate.exists():
                            resolved = candidate
                            break
                    try:
                        var_to_file[var_name] = str(resolved.relative_to(root))
                    except ValueError:
                        pass

        # Find app.use('/prefix', varName) and map to resolved file
        for match in _ROUTER_USE_RE.finditer(source):
            prefix = match.group(1).rstrip("/")
            var_name = match.group(2)
            if var_name in var_to_file:
                mount_map[var_to_file[var_name]] = prefix

    return mount_map


def analyze_express_file(
    root: Path, file_info: FileInfo,
    mount_map: dict[str, str] | None = None,
) -> Optional[ExpressAnalysisResult]:
    """Analyze a JS/TS file for Express.js route endpoints."""
    if file_info.language not in (Language.JAVASCRIPT, Language.TYPESCRIPT):
        return None

    try:
        source = (root / file_info.path).read_text(errors="replace")
    except OSError:
        return None

    has_express_reference = re.search(
        r"express|require\s*\(\s*['\"]express['\"]|from\s+['\"]express['\"]",
        source,
    )
    has_routing_controllers = "routing-controllers" in source or "@JsonController" in source

    # Must have express reference or routing-controllers decorators
    if not has_express_reference and not has_routing_controllers:
        # Could be a router file — check for Router()
        if "Router()" not in source and "router." not in source:
            return None

    result = ExpressAnalysisResult()
    is_typescript = file_info.language == Language.TYPESCRIPT

    if "Router()" in source:
        result.has_routers = True

    # Find router prefixes from local app.use() calls
    router_prefixes: dict[str, str] = {}
    for match in _ROUTER_USE_RE.finditer(source):
        prefix = match.group(1).rstrip("/")
        var_name = match.group(2)
        router_prefixes[var_name] = prefix

    # Cross-file mount prefix: if this file is mounted via app.use() in another file
    file_mount_prefix = ""
    if mount_map and file_info.path in mount_map:
        file_mount_prefix = mount_map[file_info.path]

    # Find chained routes: router.route('/path').get(...).post(...)
    for match in _ROUTE_CHAIN_RE.finditer(source):
        chain_router_var = match.group(1)
        chain_path = match.group(2)

        # Prepend router mount prefix if applicable (same-file)
        if chain_router_var in router_prefixes:
            chain_path = router_prefixes[chain_router_var] + chain_path
        elif file_mount_prefix:
            chain_path = file_mount_prefix + chain_path
        # Scan ahead for chained methods
        chain_text = source[match.end():match.end() + 1500]
        for method_match in _CHAIN_METHOD_RE.finditer(chain_text):
            http_method = method_match.group(1).upper()
            # Stop if we hit another .route( call
            preceding = chain_text[:method_match.start()]
            if ".route(" in preceding:
                break

            path_params = _extract_path_params(chain_path)
            body_params = _extract_params_from_context(source, match.end() + method_match.start(), is_typescript)

            seen_names = {p.name for p in path_params}
            all_params = list(path_params)
            for p in body_params:
                if p.name not in seen_names:
                    all_params.append(p)
                    seen_names.add(p.name)

            func_name = chain_path.strip("/").replace("/", "_").replace(":", "")
            func_name = re.sub(r"[^a-zA-Z0-9_]", "_", func_name) or "handler"

            normalized = normalize_path(chain_path)
            desc = make_description(func_name)

            endpoint = ExpressEndpoint(
                http_method=http_method,
                path=normalized,
                function_name=func_name,
                description=desc,
                parameters=all_params,
                source_file=file_info.path,
            )
            result.routes.append(endpoint)

    # Find all routes
    for match in _ROUTE_RE.finditer(source):
        router_var = match.group(1)
        http_method = match.group(2).upper()
        path = match.group(3)

        # Prepend router mount prefix if this route belongs to a mounted router
        if router_var in router_prefixes:
            path = router_prefixes[router_var] + path
        elif file_mount_prefix and router_var != "app":
            path = file_mount_prefix + path

        # Try to find handler name
        func_name = ""
        handler_match = _HANDLER_NAME_RE.search(source[match.start():match.start() + 300])
        if handler_match:
            func_name = handler_match.group(2)
        if not func_name:
            # Generate from path
            func_name = path.strip("/").replace("/", "_").replace(":", "")
            func_name = re.sub(r"[^a-zA-Z0-9_]", "_", func_name) or "handler"

        # Extract parameters from path and handler body
        path_params = _extract_path_params(path)
        body_params = _extract_params_from_context(source, match.start(), is_typescript)

        # For TypeScript: apply type hints to path params too (e.g. parseInt infers integer)
        if is_typescript:
            context = source[match.start():match.start() + 800]
            ts_types = _resolve_ts_types(context)
            for p in path_params:
                if p.name in ts_types:
                    p.type = ts_types[p.name]

        # Merge: path params first, then body params (avoiding duplicates)
        seen_names = {p.name for p in path_params}
        all_params = list(path_params)
        for p in body_params:
            if p.name not in seen_names:
                all_params.append(p)
                seen_names.add(p.name)

        normalized = normalize_path(path)
        desc = make_description(func_name)

        endpoint = ExpressEndpoint(
            http_method=http_method,
            path=normalized,
            function_name=func_name,
            description=desc,
            parameters=all_params,
            source_file=file_info.path,
        )
        result.routes.append(endpoint)

    # routing-controllers class decorators are common in TypeScript Express apps
    if is_typescript and ("JsonController" in source or "routing-controllers" in source):
        result.routes.extend(_extract_routing_controller_routes(source, file_info))

    return result if result.routes else None


def express_results_to_capabilities(
    results: dict[str, ExpressAnalysisResult],
) -> list[Capability]:
    """Convert Express analysis results into Capability objects."""
    capabilities: list[Capability] = []
    seen: set[str] = set()

    for file_path, result in results.items():
        for ep in result.routes:
            tool_name = endpoint_to_tool_name(ep.http_method, ep.path, ep.function_name)
            if tool_name in seen:
                continue
            seen.add(tool_name)

            desc = f"{ep.http_method} {ep.path} - {ep.description}"

            capabilities.append(Capability(
                name=tool_name,
                description=desc,
                category="api",
                parameters=ep.parameters,
                return_type="object",
                source_file=file_path,
                source_function=ep.function_name,
                ipc_type=IPCType.PROTOCOL,
            ))

    return capabilities
