"""Regex-based analyzer for Rust web framework endpoints.

Supports Actix-web and Axum route extraction.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from mcp_anything.models.analysis import Capability, FileInfo, IPCType, Language, ParameterSpec
from mcp_anything.analysis.route_utils import endpoint_to_tool_name, normalize_path, make_description


@dataclass
class RustEndpoint:
    """A route extracted from Rust source."""

    http_method: str
    path: str
    function_name: str
    description: str
    parameters: list[ParameterSpec]
    source_file: str
    framework: str


@dataclass
class RustWebAnalysisResult:
    """Result of analyzing Rust files for web framework routes."""

    routes: list[RustEndpoint] = field(default_factory=list)
    framework: str = ""


# Actix attribute macros: #[get("/path")], #[post("/path")]
_ACTIX_MACRO_RE = re.compile(
    r'#\[(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']\s*\)\s*\]\s*'
    r'(?:pub\s+)?async\s+fn\s+(\w+)',
    re.DOTALL,
)

# Actix web::resource/scope routes:
# .route("/path", web::get().to(handler))
_ACTIX_ROUTE_RE = re.compile(
    r'\.route\s*\(\s*["\']([^"\']+)["\']\s*,\s*web::(get|post|put|delete|patch)\s*\(\s*\)\.to\s*\(\s*(\w+)',
)

# Actix service with resource:
# web::resource("/path").route(web::get().to(handler))
_ACTIX_RESOURCE_RE = re.compile(
    r'web::resource\s*\(\s*["\']([^"\']+)["\']\s*\)'
    r'(?:.*?)\.route\s*\(\s*web::(get|post|put|delete|patch)',
    re.DOTALL,
)

# Axum routes: .route("/path", get(handler))
_AXUM_ROUTE_RE = re.compile(
    r'\.route\s*\(\s*["\']([^"\']+)["\']\s*,\s*'
    r'(get|post|put|delete|patch)\s*\(\s*(\w+)\s*\)',
)

# Axum method chaining: .route("/path", get(h1).post(h2))
_AXUM_CHAIN_RE = re.compile(
    r'\.route\s*\(\s*["\']([^"\']+)["\']\s*,\s*'
    r'((?:(?:get|post|put|delete|patch)\s*\(\s*\w+\s*\)\s*\.?\s*)+)',
)

# Axum nest: .nest("/prefix", router)
_AXUM_NEST_RE = re.compile(
    r'\.nest\s*\(\s*["\']([^"\']+)["\']\s*,\s*(\w+)',
)

# Extract path params from Actix/Axum function signatures:
# Path<(i32,)>, Path<PathParams>, Query<QueryParams>, Json<CreateUser>
_RUST_PATH_PARAM_RE = re.compile(r'Path\s*<\s*(\w+)')
_RUST_QUERY_PARAM_RE = re.compile(r'Query\s*<\s*(\w+)')
_RUST_JSON_PARAM_RE = re.compile(r'Json\s*<\s*(\w+)')

# Extract struct fields: pub name: String,
_STRUCT_FIELD_RE = re.compile(r'(?:pub\s+)?(\w+)\s*:\s*([\w<>]+)')


def _extract_path_params(path: str) -> list[ParameterSpec]:
    """Extract path parameters from {param} syntax."""
    params = []
    for match in re.finditer(r"\{(\w+)\}", path):
        params.append(ParameterSpec(name=match.group(1), type="string", required=True))
    return params


def _find_struct_fields(source: str, struct_name: str) -> list[str]:
    """Find fields of a struct by name."""
    pattern = re.compile(
        rf'struct\s+{re.escape(struct_name)}\s*\{{([^}}]+)\}}',
        re.DOTALL,
    )
    match = pattern.search(source)
    if not match:
        return []
    fields = []
    for field_match in _STRUCT_FIELD_RE.finditer(match.group(1)):
        field_name = field_match.group(1)
        if field_name not in ("pub", "crate"):
            fields.append(field_name)
    return fields


def _extract_handler_params(source: str, handler_name: str) -> list[ParameterSpec]:
    """Extract parameters from a Rust handler function signature."""
    # Find function signature
    pattern = re.compile(
        rf'(?:pub\s+)?async\s+fn\s+{re.escape(handler_name)}\s*\(([^)]*)\)',
        re.DOTALL,
    )
    match = pattern.search(source)
    if not match:
        return []

    sig = match.group(1)
    params: list[ParameterSpec] = []

    # Query parameters
    query_match = _RUST_QUERY_PARAM_RE.search(sig)
    if query_match:
        struct_name = query_match.group(1)
        fields = _find_struct_fields(source, struct_name)
        for f in fields:
            params.append(ParameterSpec(name=f, type="string", required=False))

    # JSON body parameters
    json_match = _RUST_JSON_PARAM_RE.search(sig)
    if json_match:
        struct_name = json_match.group(1)
        fields = _find_struct_fields(source, struct_name)
        for f in fields:
            params.append(ParameterSpec(name=f, type="string", required=True))

    return params


def analyze_rust_web_file(
    root: Path, file_info: FileInfo,
) -> Optional[RustWebAnalysisResult]:
    """Analyze a Rust file for web framework route endpoints."""
    if file_info.language != Language.RUST:
        return None

    try:
        source = (root / file_info.path).read_text(errors="replace")
    except OSError:
        return None

    result = RustWebAnalysisResult()

    # Detect framework
    if "actix_web" in source or "actix-web" in source:
        result.framework = "actix"
    elif "axum::" in source:
        result.framework = "axum"
    else:
        return None

    if result.framework == "actix":
        # Actix attribute macros
        for match in _ACTIX_MACRO_RE.finditer(source):
            http_method = match.group(1).upper()
            path = match.group(2)
            handler = match.group(3)

            path_params = _extract_path_params(path)
            handler_params = _extract_handler_params(source, handler)

            seen = {p.name for p in path_params}
            all_params = list(path_params)
            for p in handler_params:
                if p.name not in seen:
                    all_params.append(p)

            result.routes.append(RustEndpoint(
                http_method=http_method,
                path=path,
                function_name=handler,
                description=make_description(handler),
                parameters=all_params,
                source_file=file_info.path,
                framework="actix",
            ))

        # Actix .route() style
        for match in _ACTIX_ROUTE_RE.finditer(source):
            path = match.group(1)
            http_method = match.group(2).upper()
            handler = match.group(3)

            path_params = _extract_path_params(path)

            result.routes.append(RustEndpoint(
                http_method=http_method,
                path=path,
                function_name=handler,
                description=make_description(handler),
                parameters=path_params,
                source_file=file_info.path,
                framework="actix",
            ))

    elif result.framework == "axum":
        # Axum .route() style
        for match in _AXUM_ROUTE_RE.finditer(source):
            path = match.group(1)
            http_method = match.group(2).upper()
            handler = match.group(3)

            path_params = _extract_path_params(path)
            handler_params = _extract_handler_params(source, handler)

            seen = {p.name for p in path_params}
            all_params = list(path_params)
            for p in handler_params:
                if p.name not in seen:
                    all_params.append(p)

            result.routes.append(RustEndpoint(
                http_method=http_method,
                path=path,
                function_name=handler,
                description=make_description(handler),
                parameters=all_params,
                source_file=file_info.path,
                framework="axum",
            ))

    return result if result.routes else None


def rust_web_results_to_capabilities(
    results: dict[str, RustWebAnalysisResult],
) -> list[Capability]:
    """Convert Rust web analysis results into Capability objects."""
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
