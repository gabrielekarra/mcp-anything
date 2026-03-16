"""Regex-based Java source analyzer for Spring Boot and Spring MVC endpoints.

Extracts REST controller methods, path mappings, request parameters,
path variables, and request bodies from Java source files.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from mcp_anything.models.analysis import Capability, FileInfo, IPCType, Language, ParameterSpec


@dataclass
class SpringEndpoint:
    """A REST endpoint extracted from a Spring controller."""

    http_method: str  # GET, POST, PUT, DELETE, PATCH
    path: str
    method_name: str
    description: str
    parameters: list[ParameterSpec]
    return_type: str
    source_file: str
    controller_class: str
    controller_path: str  # base path from @RequestMapping on class


@dataclass
class JavaAnalysisResult:
    """Result of analyzing Java source files for Spring patterns."""

    endpoints: list[SpringEndpoint] = field(default_factory=list)
    controllers: list[str] = field(default_factory=list)
    has_spring_boot: bool = False


# Mapping annotations → HTTP methods
_HTTP_METHOD_ANNOTATIONS = {
    "GetMapping": "GET",
    "PostMapping": "POST",
    "PutMapping": "PUT",
    "DeleteMapping": "DELETE",
    "PatchMapping": "PATCH",
}

# Java type → MCP parameter type
_JAVA_TYPE_MAP = {
    "String": "string",
    "int": "integer",
    "Integer": "integer",
    "long": "integer",
    "Long": "integer",
    "double": "float",
    "Double": "float",
    "float": "float",
    "Float": "float",
    "boolean": "boolean",
    "Boolean": "boolean",
    "List": "array",
    "Map": "object",
}

# Regex to find class-level @RequestMapping("/api/...")
_CLASS_REQUEST_MAPPING_RE = re.compile(
    r'@RequestMapping\s*\(\s*(?:value\s*=\s*)?["\']([^"\']*)["\']',
)

# Regex to find @RestController or @Controller class
_CONTROLLER_CLASS_RE = re.compile(
    r'@(?:Rest)?Controller\s+(?:.*\n)*?\s*(?:public\s+)?class\s+(\w+)',
)

# Regex to find method-level mapping annotations (captures annotation + path only)
_METHOD_ANNOTATION_RE = re.compile(
    r'@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|RequestMapping)'
    r'(?:\s*\(\s*'
    r'(?:value\s*=\s*)?'
    r'(?:["\']([^"\']*)["\'])?'  # path in quotes
    r'(?:,\s*method\s*=\s*RequestMethod\.(\w+))?'  # method for @RequestMapping
    r'[^)]*\))?'  # rest of annotation params
    r'\s+'
    r'(?:public\s+)?'
    r'([\w<>,\s]+?)'  # return type (possibly generic like List<User>)
    r'\s+'
    r'(\w+)'  # method name
    r'\s*\(',  # opening paren of method
    re.DOTALL,
)

# Regex to match annotation + type + name for each parameter
_PARAM_ANNOTATION_RE = re.compile(
    r'@(RequestParam|PathVariable|RequestBody)'
    r'(?:\s*\(([^)]*)\))?'  # annotation arguments (everything inside parens)
    r'\s+'
    r'([\w]+(?:<[\w<>,\s]+>)?)\s+'  # type (possibly generic like Map<String, Object>)
    r'(\w+)'  # parameter name
)

# For unannotated params (after skipping annotated ones)
_BARE_PARAM_RE = re.compile(
    r'(?:^|,)\s*'
    r'(?!@)'  # not annotated
    r'([\w]+(?:<[\w<>,\s]+>)?)\s+'
    r'(\w+)'
    r'\s*(?:,|$)',
)


def _parse_annotation_args(args_str: str) -> dict:
    """Parse annotation arguments like 'required = false, defaultValue = "10"'."""
    result: dict[str, str] = {}
    if not args_str:
        return result

    # Extract required = true/false
    req_match = re.search(r'required\s*=\s*(true|false)', args_str)
    if req_match:
        result["required"] = req_match.group(1)

    # Extract defaultValue = "..."
    def_match = re.search(r'defaultValue\s*=\s*["\']([^"\']*)["\']', args_str)
    if def_match:
        result["defaultValue"] = def_match.group(1)

    # Extract value/name = "..."
    name_match = re.search(r'(?:value|name)\s*=\s*["\'](\w+)["\']', args_str)
    if name_match:
        result["name"] = name_match.group(1)
    # Also handle bare string as first arg: @RequestParam("name")
    elif args_str.strip() and not "=" in args_str:
        bare = args_str.strip().strip('"').strip("'")
        if bare and bare.isidentifier():
            result["name"] = bare

    return result


def _extract_params(param_string: str) -> list[ParameterSpec]:
    """Extract parameters from a Java method signature string."""
    params: list[ParameterSpec] = []

    for match in _PARAM_ANNOTATION_RE.finditer(param_string):
        annotation = match.group(1)  # RequestParam, PathVariable, RequestBody
        ann_args = match.group(2) or ""  # annotation arguments
        java_type = match.group(3).strip()
        param_name = match.group(4)

        # Skip injected Spring objects
        if java_type in (
            "HttpServletRequest", "HttpServletResponse", "HttpSession",
            "Principal", "Authentication", "BindingResult", "Model",
            "RedirectAttributes", "Pageable", "MultipartFile",
        ):
            continue

        # Parse annotation arguments
        ann = _parse_annotation_args(ann_args)

        # Map Java type
        base_type = java_type.split("<")[0].strip()
        mcp_type = _JAVA_TYPE_MAP.get(base_type, "string")

        name = ann.get("name", param_name)
        default_value = ann.get("defaultValue")

        # Determine if required
        if annotation == "PathVariable":
            required = True
        elif annotation == "RequestBody":
            required = True
            mcp_type = "object"
        elif "required" in ann:
            required = ann["required"] == "true"
        elif annotation == "RequestParam":
            required = default_value is None
        else:
            required = True

        params.append(ParameterSpec(
            name=name,
            type=mcp_type,
            description="",
            required=required,
            default=default_value,
        ))

    return params


def _make_description(method_name: str) -> str:
    """Generate a readable description from a Java method name."""
    # Split camelCase
    words = re.sub(r'([a-z])([A-Z])', r'\1 \2', method_name).lower()
    return words[0].upper() + words[1:]


def _extract_balanced_parens(source: str, start: int) -> str:
    """Extract content between balanced parentheses starting at position start.

    start should point to the opening '(' character.
    """
    if start >= len(source) or source[start] != "(":
        return ""
    depth = 0
    i = start
    while i < len(source):
        if source[i] == "(":
            depth += 1
        elif source[i] == ")":
            depth -= 1
            if depth == 0:
                return source[start + 1:i]
        i += 1
    return source[start + 1:]


def analyze_java_file(root: Path, file_info: FileInfo) -> Optional[JavaAnalysisResult]:
    """Analyze a single Java file for Spring REST endpoints."""
    if file_info.language != Language.JAVA:
        return None

    try:
        source = (root / file_info.path).read_text(errors="replace")
    except OSError:
        return None

    result = JavaAnalysisResult()

    if "@SpringBootApplication" in source:
        result.has_spring_boot = True

    # Find controller class
    controller_match = _CONTROLLER_CLASS_RE.search(source)
    if not controller_match:
        return result if result.has_spring_boot else None

    controller_name = controller_match.group(1)
    result.controllers.append(controller_name)

    # Find class-level base path
    class_path = ""
    class_mapping = _CLASS_REQUEST_MAPPING_RE.search(source)
    if class_mapping:
        class_path = class_mapping.group(1).rstrip("/")

    # Find all endpoint methods
    for match in _METHOD_ANNOTATION_RE.finditer(source):
        annotation = match.group(1)
        method_path = match.group(2) or ""
        request_method_override = match.group(3)
        return_type = match.group(4)
        method_name = match.group(5)

        # Extract balanced parentheses content for parameters
        paren_start = match.end() - 1  # position of '('
        param_string = _extract_balanced_parens(source, paren_start)

        # Determine HTTP method
        if annotation == "RequestMapping" and request_method_override:
            http_method = request_method_override
        elif annotation in _HTTP_METHOD_ANNOTATIONS:
            http_method = _HTTP_METHOD_ANNOTATIONS[annotation]
        else:
            http_method = "GET"

        # Build full path
        full_path = class_path
        if method_path:
            if not method_path.startswith("/"):
                method_path = "/" + method_path
            full_path += method_path

        # Extract parameters
        params = _extract_params(param_string)

        # Map Java return type
        mcp_return = _JAVA_TYPE_MAP.get(return_type, "string")

        endpoint = SpringEndpoint(
            http_method=http_method,
            path=full_path or "/",
            method_name=method_name,
            description=_make_description(method_name),
            parameters=params,
            return_type=mcp_return,
            source_file=file_info.path,
            controller_class=controller_name,
            controller_path=class_path,
        )
        result.endpoints.append(endpoint)

    return result


def java_results_to_capabilities(
    results: dict[str, JavaAnalysisResult],
) -> list[Capability]:
    """Convert Java analysis results into Capability objects."""
    capabilities: list[Capability] = []
    seen: set[str] = set()

    for file_path, result in results.items():
        for ep in result.endpoints:
            # Generate a unique tool name: http_method + path segments
            # e.g., GET /api/users/{id} → get_user_by_id
            tool_name = _endpoint_to_tool_name(ep)

            if tool_name in seen:
                continue
            seen.add(tool_name)

            # Add http_method and path as metadata in description
            desc = f"{ep.http_method} {ep.path} - {ep.description}"

            capabilities.append(Capability(
                name=tool_name,
                description=desc,
                category="api",
                parameters=ep.parameters,
                return_type=ep.return_type,
                source_file=file_path,
                source_function=ep.method_name,
                ipc_type=IPCType.PROTOCOL,
            ))

    return capabilities


def _endpoint_to_tool_name(ep: SpringEndpoint) -> str:
    """Generate a snake_case tool name from an endpoint."""
    # Clean up path: /api/users/{id} → users_id
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
    path_name = "_".join(clean_parts) if clean_parts else ep.method_name

    name = f"{method_prefix}_{path_name}"
    # Clean up
    name = re.sub(r"[^a-z0-9_]", "_", name.lower())
    name = re.sub(r"_+", "_", name).strip("_")
    return name
