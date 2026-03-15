"""Regex-based analyzer for Go web framework endpoints.

Supports net/http, Gin, Echo, Chi, and gorilla/mux.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from mcp_anything.models.analysis import Capability, FileInfo, IPCType, Language, ParameterSpec
from mcp_anything.analysis.route_utils import endpoint_to_tool_name, normalize_path, make_description


@dataclass
class GoEndpoint:
    """A route extracted from Go source."""

    http_method: str
    path: str
    function_name: str
    description: str
    parameters: list[ParameterSpec]
    source_file: str
    framework: str


@dataclass
class GoAnalysisResult:
    """Result of analyzing Go files for web framework routes."""

    routes: list[GoEndpoint] = field(default_factory=list)
    framework: str = ""


# Gin routes: r.GET("/path", handler), group.POST("/path", handler)
_GIN_ROUTE_RE = re.compile(
    r"(\w+)\.(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s*\(\s*"
    r"['\"]([^'\"]+)['\"]\s*,\s*(\w+)",
)

# Gin groups: v1 := r.Group("/api/v1")
_GIN_GROUP_RE = re.compile(
    r"(\w+)\s*:?=\s*(\w+)\.Group\s*\(\s*['\"]([^'\"]+)['\"]",
)

# Echo routes: e.GET("/path", handler)
_ECHO_ROUTE_RE = re.compile(
    r"(\w+)\.(GET|POST|PUT|DELETE|PATCH)\s*\(\s*"
    r"['\"]([^'\"]+)['\"]\s*,\s*(\w+)",
)

# Echo groups: g := e.Group("/admin")
_ECHO_GROUP_RE = re.compile(
    r"(\w+)\s*:?=\s*(\w+)\.Group\s*\(\s*['\"]([^'\"]+)['\"]",
)

# net/http HandleFunc: http.HandleFunc("/path", handler)
_HTTP_HANDLEFUNC_RE = re.compile(
    r"(?:http\.HandleFunc|(\w+)\.HandleFunc)\s*\(\s*"
    r"['\"]([^'\"]+)['\"]\s*,\s*(\w+)",
)

# gorilla/mux: r.HandleFunc("/path", handler).Methods("GET")
_MUX_ROUTE_RE = re.compile(
    r"(\w+)\.HandleFunc\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*(\w+)\s*\)"
    r"(?:\.Methods\s*\(\s*['\"](\w+)['\"])?"
)

# Chi routes: r.Get("/path", handler)
_CHI_ROUTE_RE = re.compile(
    r"(\w+)\.(Get|Post|Put|Delete|Patch)\s*\(\s*"
    r"['\"]([^'\"]+)['\"]\s*,\s*(\w+)",
)

# Chi Route method: r.Route("/prefix", func(r chi.Router) { ... })
_CHI_ROUTE_GROUP_RE = re.compile(
    r"(\w+)\.Route\s*\(\s*['\"]([^'\"]+)['\"]",
)

# Extract params from handler body: c.Param("id"), c.Query("q"), c.BindJSON(&obj)
_GIN_PARAM_RE = re.compile(r'c\.Param\s*\(\s*["\'](\w+)["\']\s*\)')
_GIN_QUERY_RE = re.compile(r'c\.(?:Query|DefaultQuery)\s*\(\s*["\'](\w+)["\']\s*')
_GIN_BODY_RE = re.compile(r'c\.(?:BindJSON|ShouldBindJSON|Bind|ShouldBind)\s*\(')

_ECHO_PARAM_RE = re.compile(r'c\.Param\s*\(\s*["\'](\w+)["\']\s*\)')
_ECHO_QUERY_RE = re.compile(r'c\.QueryParam\s*\(\s*["\'](\w+)["\']\s*\)')
_ECHO_BODY_RE = re.compile(r'c\.Bind\s*\(')


def _extract_path_params(path: str) -> list[ParameterSpec]:
    """Extract path parameters from :param or {param} syntax."""
    params = []
    for match in re.finditer(r":(\w+)|\{(\w+)\}", path):
        name = match.group(1) or match.group(2)
        params.append(ParameterSpec(name=name, type="string", required=True))
    return params


def _find_handler_body(source: str, handler_name: str) -> str:
    """Find the body of a handler function."""
    pattern = re.compile(rf"func\s+{re.escape(handler_name)}\s*\([^)]*\)\s*\{{")
    match = pattern.search(source)
    if not match:
        return ""
    # Get ~500 chars of the function body
    start = match.end()
    depth = 1
    i = start
    while i < min(len(source), start + 1000) and depth > 0:
        if source[i] == "{":
            depth += 1
        elif source[i] == "}":
            depth -= 1
        i += 1
    return source[start:i]


def _extract_handler_params(source: str, handler_name: str, framework: str) -> list[ParameterSpec]:
    """Extract query/body params from handler function body."""
    body = _find_handler_body(source, handler_name)
    if not body:
        return []

    params: list[ParameterSpec] = []
    seen: set[str] = set()

    if framework in ("gin", "echo"):
        param_re = _GIN_PARAM_RE if framework == "gin" else _ECHO_PARAM_RE
        query_re = _GIN_QUERY_RE if framework == "gin" else _ECHO_QUERY_RE
        body_re = _GIN_BODY_RE if framework == "gin" else _ECHO_BODY_RE

        for match in query_re.finditer(body):
            name = match.group(1)
            if name not in seen:
                seen.add(name)
                params.append(ParameterSpec(name=name, type="string", required=False))

        if body_re.search(body):
            # Has JSON body binding — add a generic body param
            if "body" not in seen:
                seen.add("body")
                params.append(ParameterSpec(name="body", type="object", required=True,
                                           description="Request body"))

    return params


def analyze_go_file(
    root: Path, file_info: FileInfo,
) -> Optional[GoAnalysisResult]:
    """Analyze a Go file for web framework route endpoints."""
    if file_info.language != Language.GO:
        return None

    try:
        source = (root / file_info.path).read_text(errors="replace")
    except OSError:
        return None

    result = GoAnalysisResult()

    # Detect framework
    if "gin-gonic/gin" in source or "gin.Default" in source or "gin.New" in source:
        result.framework = "gin"
    elif "labstack/echo" in source or "echo.New" in source:
        result.framework = "echo"
    elif "go-chi/chi" in source or "chi.NewRouter" in source:
        result.framework = "chi"
    elif "gorilla/mux" in source or "mux.NewRouter" in source:
        result.framework = "gorilla/mux"
    elif '"net/http"' in source:
        result.framework = "net/http"
    else:
        return None

    # Collect group prefixes
    group_prefixes: dict[str, str] = {}
    for match in _GIN_GROUP_RE.finditer(source):
        var_name = match.group(1)
        prefix = match.group(3).rstrip("/")
        group_prefixes[var_name] = prefix

    # Also use echo group pattern (same regex structure)
    for match in _ECHO_GROUP_RE.finditer(source):
        var_name = match.group(1)
        prefix = match.group(3).rstrip("/")
        group_prefixes[var_name] = prefix

    if result.framework == "gin":
        for match in _GIN_ROUTE_RE.finditer(source):
            var_name = match.group(1)
            http_method = match.group(2)
            path = match.group(3)
            handler = match.group(4)

            # Prepend group prefix
            prefix = group_prefixes.get(var_name, "")
            full_path = prefix + path

            path_params = _extract_path_params(full_path)
            handler_params = _extract_handler_params(source, handler, "gin")

            seen = {p.name for p in path_params}
            all_params = list(path_params)
            for p in handler_params:
                if p.name not in seen:
                    all_params.append(p)

            result.routes.append(GoEndpoint(
                http_method=http_method,
                path=normalize_path(full_path),
                function_name=handler,
                description=make_description(handler),
                parameters=all_params,
                source_file=file_info.path,
                framework="gin",
            ))

    elif result.framework == "echo":
        for match in _ECHO_ROUTE_RE.finditer(source):
            var_name = match.group(1)
            http_method = match.group(2)
            path = match.group(3)
            handler = match.group(4)

            prefix = group_prefixes.get(var_name, "")
            full_path = prefix + path

            path_params = _extract_path_params(full_path)
            handler_params = _extract_handler_params(source, handler, "echo")

            seen = {p.name for p in path_params}
            all_params = list(path_params)
            for p in handler_params:
                if p.name not in seen:
                    all_params.append(p)

            result.routes.append(GoEndpoint(
                http_method=http_method,
                path=normalize_path(full_path),
                function_name=handler,
                description=make_description(handler),
                parameters=all_params,
                source_file=file_info.path,
                framework="echo",
            ))

    elif result.framework == "chi":
        for match in _CHI_ROUTE_RE.finditer(source):
            http_method = match.group(2).upper()
            path = match.group(3)
            handler = match.group(4)

            path_params = _extract_path_params(path)

            result.routes.append(GoEndpoint(
                http_method=http_method,
                path=normalize_path(path),
                function_name=handler,
                description=make_description(handler),
                parameters=path_params,
                source_file=file_info.path,
                framework="chi",
            ))

    elif result.framework == "gorilla/mux":
        for match in _MUX_ROUTE_RE.finditer(source):
            path = match.group(2)
            handler = match.group(3)
            http_method = (match.group(4) or "GET").upper()

            path_params = _extract_path_params(path)

            result.routes.append(GoEndpoint(
                http_method=http_method,
                path=normalize_path(path),
                function_name=handler,
                description=make_description(handler),
                parameters=path_params,
                source_file=file_info.path,
                framework="gorilla/mux",
            ))

    elif result.framework == "net/http":
        for match in _HTTP_HANDLEFUNC_RE.finditer(source):
            path = match.group(2)
            handler = match.group(3)

            result.routes.append(GoEndpoint(
                http_method="GET",  # net/http doesn't specify method in route
                path=normalize_path(path),
                function_name=handler,
                description=make_description(handler),
                parameters=[],
                source_file=file_info.path,
                framework="net/http",
            ))

    return result if result.routes else None


def go_results_to_capabilities(
    results: dict[str, GoAnalysisResult],
) -> list[Capability]:
    """Convert Go analysis results into Capability objects."""
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
