"""Regex-based analyzer for Express.js route endpoints.

Extracts HTTP routes, path parameters, query parameters, and request
bodies from Express.js source files using regex patterns.
"""

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
    r"(?:app|router|\w+Router|\w+)\."
    r"(get|post|put|delete|patch|all)\s*\(\s*"
    r"['\"]([^'\"]+)['\"]",
    re.IGNORECASE,
)

# Chained route pattern: router.route('/path').get(...).post(...)
_ROUTE_CHAIN_RE = re.compile(
    r"\.route\s*\(\s*['\"]([^'\"]+)['\"]\s*\)"
)
_CHAIN_METHOD_RE = re.compile(
    r"\.(get|post|put|delete|patch)\s*\(",
    re.IGNORECASE,
)

# Regex for router mount: app.use('/prefix', router)
_ROUTER_USE_RE = re.compile(
    r"app\.use\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*(\w+)",
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
_DESTRUCTURE_PARAMS_RE = re.compile(r"(?:const|let|var)\s*\{([^}]+)\}\s*=\s*req\.params")
_DESTRUCTURE_QUERY_RE = re.compile(r"(?:const|let|var)\s*\{([^}]+)\}\s*=\s*req\.query")
_DESTRUCTURE_BODY_RE = re.compile(r"(?:const|let|var)\s*\{([^}]+)\}\s*=\s*req\.body")


def _extract_params_from_context(source: str, route_pos: int) -> list[ParameterSpec]:
    """Extract parameters by scanning the handler body after a route definition."""
    # Look at the next ~500 chars after the route for the handler body
    context = source[route_pos:route_pos + 800]
    params: list[ParameterSpec] = []
    seen: set[str] = set()

    # Path params from req.params.X or destructured
    for match in _REQ_PARAM_RE.finditer(context):
        name = match.group(1)
        if name not in seen:
            seen.add(name)
            params.append(ParameterSpec(name=name, type="string", required=True))
    for match in _DESTRUCTURE_PARAMS_RE.finditer(context):
        for name in re.split(r"\s*,\s*", match.group(1).strip()):
            name = name.strip()
            if name and name not in seen:
                seen.add(name)
                params.append(ParameterSpec(name=name, type="string", required=True))

    # Query params from req.query.X or destructured
    for match in _REQ_QUERY_RE.finditer(context):
        name = match.group(1)
        if name not in seen:
            seen.add(name)
            params.append(ParameterSpec(name=name, type="string", required=False))
    for match in _DESTRUCTURE_QUERY_RE.finditer(context):
        for name in re.split(r"\s*,\s*", match.group(1).strip()):
            name = name.strip()
            if name and name not in seen:
                seen.add(name)
                params.append(ParameterSpec(name=name, type="string", required=False))

    # Body params from req.body.X or destructured
    for match in _REQ_BODY_RE.finditer(context):
        name = match.group(1)
        if name not in seen:
            seen.add(name)
            params.append(ParameterSpec(name=name, type="string", required=True))
    for match in _DESTRUCTURE_BODY_RE.finditer(context):
        for name in re.split(r"\s*,\s*", match.group(1).strip()):
            name = name.strip()
            if name and name not in seen:
                seen.add(name)
                params.append(ParameterSpec(name=name, type="string", required=True))

    return params


def _extract_path_params(path: str) -> list[ParameterSpec]:
    """Extract path parameters from Express :param syntax."""
    params = []
    for match in re.finditer(r":(\w+)", path):
        params.append(ParameterSpec(name=match.group(1), type="string", required=True))
    return params


def analyze_express_file(
    root: Path, file_info: FileInfo,
) -> Optional[ExpressAnalysisResult]:
    """Analyze a JS/TS file for Express.js route endpoints."""
    if file_info.language not in (Language.JAVASCRIPT, Language.TYPESCRIPT):
        return None

    try:
        source = (root / file_info.path).read_text(errors="replace")
    except OSError:
        return None

    # Must have express reference
    if not re.search(r"express|require\s*\(\s*['\"]express['\"]|from\s+['\"]express['\"]", source):
        # Could be a router file — check for Router()
        if "Router()" not in source and "router." not in source:
            return None

    result = ExpressAnalysisResult()

    if "Router()" in source:
        result.has_routers = True

    # Find router prefixes
    router_prefixes: dict[str, str] = {}
    for match in _ROUTER_USE_RE.finditer(source):
        prefix = match.group(1).rstrip("/")
        var_name = match.group(2)
        router_prefixes[var_name] = prefix

    # Find chained routes: router.route('/path').get(...).post(...)
    for match in _ROUTE_CHAIN_RE.finditer(source):
        chain_path = match.group(1)
        # Scan ahead for chained methods
        chain_text = source[match.end():match.end() + 1500]
        for method_match in _CHAIN_METHOD_RE.finditer(chain_text):
            http_method = method_match.group(1).upper()
            # Stop if we hit another .route( call
            preceding = chain_text[:method_match.start()]
            if ".route(" in preceding:
                break

            path_params = _extract_path_params(chain_path)
            body_params = _extract_params_from_context(source, match.end() + method_match.start())

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
        http_method = match.group(1).upper()
        path = match.group(2)

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
        body_params = _extract_params_from_context(source, match.start())

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
