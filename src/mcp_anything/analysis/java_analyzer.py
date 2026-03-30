"""Java/Kotlin source analyzer for Spring, JAX-RS, and Micronaut endpoints.

Uses javalang AST parsing for Java files when available (accurate, handles any
annotation ordering or formatting).  Falls back to regex for Kotlin files and
when javalang is not installed.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from mcp_anything.models.analysis import Capability, FileInfo, IPCType, Language, ParameterSpec

# ---------------------------------------------------------------------------
# Optional AST-based analyzer (javalang)
# ---------------------------------------------------------------------------

try:
    from mcp_anything.analysis.java_ast import analyze_java_string as _ast_analyze_string
    _HAS_JAVALANG = True
except ImportError:  # pragma: no cover
    _HAS_JAVALANG = False
    _ast_analyze_string = None  # type: ignore

# Kotlin type → MCP parameter type additions
_KOTLIN_TYPE_MAP = {
    "String": "string",
    "Int": "integer",
    "Long": "integer",
    "Double": "float",
    "Float": "float",
    "Boolean": "boolean",
    "List": "array",
    "Map": "object",
    "Any": "object",
    # Nullable variants (strip ? later)
}


@dataclass
class SpringEndpoint:
    """A REST endpoint extracted from a Java controller."""

    http_method: str  # GET, POST, PUT, DELETE, PATCH
    path: str
    method_name: str
    description: str
    parameters: list[ParameterSpec]
    return_type: str
    source_file: str
    controller_class: str
    controller_path: str  # base path from class-level annotation


@dataclass
class JavaAnalysisResult:
    """Result of analyzing Java source files for REST patterns."""

    endpoints: list[SpringEndpoint] = field(default_factory=list)
    controllers: list[str] = field(default_factory=list)
    has_spring_boot: bool = False


# ---------------------------------------------------------------------------
# Spring annotations
# ---------------------------------------------------------------------------

_HTTP_METHOD_ANNOTATIONS = {
    "GetMapping": "GET",
    "PostMapping": "POST",
    "PutMapping": "PUT",
    "DeleteMapping": "DELETE",
    "PatchMapping": "PATCH",
}

# Java/Kotlin type → MCP parameter type
_JAVA_TYPE_MAP = {
    # Java primitives and boxed
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
    # Kotlin types
    "Int": "integer",
    "Any": "object",
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

# Regex to match annotation + type + name for each parameter (Spring)
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

# ---------------------------------------------------------------------------
# JAX-RS annotations
# ---------------------------------------------------------------------------

# Class-level @Path("/api/...") — matches class, interface, or abstract class
_JAXRS_CLASS_PATH_RE = re.compile(
    r'@Path\s*\(\s*["\']([^"\']*)["\'].*?\)\s+'
    r'(?:@\w+(?:\s*\([^)]*\))?\s+)*'  # skip other class-level annotations
    r'(?:public\s+)?(?:abstract\s+)?(?:class|interface)\s+(\w+)',
    re.DOTALL,
)

# Method-level: @GET/@POST/... optionally followed by @Path("...")
# Captures: (1) HTTP method, (2) optional path, (3) return type, (4) method name
_JAXRS_METHOD_RE = re.compile(
    r'@(GET|POST|PUT|DELETE|PATCH)\b'
    r'(?:\s+@Path\s*\(\s*["\']([^"\']*)["\'].*?\))?'  # optional @Path
    r'(?:\s+@(?:Consumes|Produces)\s*\([^)]*\))*'  # skip @Consumes/@Produces
    r'\s+'
    r'(?:public\s+)?'
    r'([\w<>,\s]+?)'  # return type
    r'\s+'
    r'(\w+)'  # method name
    r'\s*\(',  # opening paren
    re.DOTALL,
)

# JAX-RS parameter annotations: @QueryParam("name"), @PathParam("name"), @FormParam("name")
_JAXRS_PARAM_RE = re.compile(
    r'@(QueryParam|PathParam|FormParam)\s*\(\s*["\'](\w+)["\']\s*\)'
    r'\s+'
    r'([\w]+(?:<[\w<>,\s]+>)?)\s+'  # type
    r'(\w+)'  # parameter name
)

# ---------------------------------------------------------------------------
# Kotlin Spring patterns
# ---------------------------------------------------------------------------

# Class-level @RequestMapping on a Kotlin @RestController
_KOTLIN_SPRING_CLASS_RE = re.compile(
    r'@(?:Rest)?Controller\b'
    r'(?:\s+@\w+(?:\s*\([^)]*\))?\s*)*'
    r'\s+(?:open\s+)?class\s+(\w+)',
    re.DOTALL,
)

_KOTLIN_CLASS_REQUEST_MAPPING_RE = re.compile(
    r'@RequestMapping\s*\(\s*(?:value\s*=\s*)?["\']([^"\']*)["\']',
)

# Method-level mapping annotations + Kotlin `fun` keyword
_KOTLIN_SPRING_METHOD_RE = re.compile(
    r'@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|RequestMapping)'
    r'(?:\s*\(\s*'
    r'(?:value\s*=\s*)?'
    r'(?:["\']([^"\']*)["\'])?'
    r'(?:,\s*method\s*=\s*RequestMethod\.(\w+))?'
    r'[^)]*\))?'
    r'\s+'
    r'(?:override\s+)?fun\s+'
    r'(\w+)'   # method name
    r'\s*\(',
    re.DOTALL,
)

# Kotlin Spring params: @RequestParam / @PathVariable / @RequestBody + `name: Type`
_KOTLIN_SPRING_PARAM_RE = re.compile(
    r'@(RequestParam|PathVariable|RequestBody)'
    r'(?:\s*\(([^)]*)\))?'
    r'\s+'
    r'(\w+)'             # parameter name
    r'\s*:\s*'
    r'([\w<>,?\s]+?)'   # type (possibly nullable)
    r'\s*(?:[=,)]|$)',
)

# ---------------------------------------------------------------------------
# Kotlin JAX-RS / Jersey patterns
# Kotlin uses the same JAX-RS annotations but with 'fun' instead of 'public Type'
# ---------------------------------------------------------------------------

# Class-level @Path for Kotlin: annotation + 'class ClassName'
# Use [^\n]*\n to skip whole annotation lines so trailing comments like
# // note (with parens) don't terminate the match prematurely.
_KOTLIN_JAXRS_CLASS_PATH_RE = re.compile(
    r'@Path\s*\(\s*["\']([^"\']*)["\'].*?\)\s*\n'
    r'(?:@\w+[^\n]*\n)*'   # skip entire annotation lines
    r'(?:open\s+)?class\s+(\w+)',
)

# Kotlin method: @GET/@POST/... + optional @Path + 'fun methodName('
# Broadened to skip ANY intervening annotations (not just @Consumes/@Produces)
# so patterns like @Timeout(1000) // note (with parens) don't break the match.
_KOTLIN_JAXRS_METHOD_RE = re.compile(
    r'@(GET|POST|PUT|DELETE|PATCH)\b'
    r'(?:\s+@Path\s*\(\s*["\']([^"\']*)["\'].*?\))?'
    r'(?:\s+@\w+(?:\s*\([^)]*\))?)*'   # skip any number of other annotations
    r'\s+'
    r'(?:override\s+)?fun\s+'
    r'(\w+)'  # method name
    r'\s*\(',
    re.DOTALL,
)

# Kotlin JAX-RS params: @QueryParam/@PathParam/@FormParam annotation + 'name: Type'
_KOTLIN_JAXRS_PARAM_RE = re.compile(
    r'@(QueryParam|PathParam|FormParam)\s*\(\s*["\'](\w+)["\']\s*\)'
    r'\s+'
    r'(\w+)'          # parameter name
    r'\s*:\s*'
    r'([\w<>,?\s]+?)' # type (possibly nullable with ?)
    r'\s*(?:[=,)]|$)' # followed by default value, comma, closing paren, or end
)

# ---------------------------------------------------------------------------
# Micronaut annotations
# ---------------------------------------------------------------------------

# Class-level @Controller("/api/...")
_MICRONAUT_CLASS_RE = re.compile(
    r'@Controller\s*\(\s*["\']([^"\']*)["\'].*?\)\s+'
    r'(?:@\w+(?:\s*\([^)]*\))?\s+)*'
    r'(?:public\s+)?class\s+(\w+)',
    re.DOTALL,
)

# Method-level: @Get("/{id}"), @Post("/"), etc.
_MICRONAUT_METHOD_RE = re.compile(
    r'@(Get|Post|Put|Delete|Patch)\b'
    r'(?:\s*\(\s*["\']([^"\']*)["\'].*?\))?'  # optional path
    r'\s+'
    r'(?:public\s+)?'
    r'([\w<>,\s]+?)'  # return type
    r'\s+'
    r'(\w+)'  # method name
    r'\s*\(',  # opening paren
    re.DOTALL,
)

# Micronaut param annotations: @QueryValue, @PathVariable, @Body
_MICRONAUT_PARAM_RE = re.compile(
    r'@(QueryValue|PathVariable|Body)\b'
    r'(?:\s*\(\s*["\']?(\w*)["\']?\s*\))?'  # optional name
    r'\s+'
    r'([\w]+(?:<[\w<>,\s]+>)?)\s+'  # type
    r'(\w+)'  # parameter name
)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

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


def _extract_spring_params(param_string: str) -> list[ParameterSpec]:
    """Extract parameters from a Spring method signature string."""
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
        orig_type = None

        # Determine if required
        if annotation == "PathVariable":
            required = True
        elif annotation == "RequestBody":
            required = True
            mcp_type = "object"
            if base_type not in _JAVA_TYPE_MAP:
                orig_type = base_type
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
            original_type=orig_type,
        ))

    return params


def _extract_jaxrs_params(param_string: str, http_method: str = "GET") -> list[ParameterSpec]:
    """Extract parameters from a JAX-RS method signature string.

    In JAX-RS, unannotated parameters on POST/PUT/DELETE/PATCH methods are
    implicitly treated as the request body.
    """
    params: list[ParameterSpec] = []
    annotated_spans: list[tuple[int, int]] = []

    for match in _JAXRS_PARAM_RE.finditer(param_string):
        annotation = match.group(1)  # QueryParam, PathParam, FormParam
        param_alias = match.group(2)  # name from annotation
        java_type = match.group(3).strip()
        param_name = match.group(4)

        annotated_spans.append((match.start(), match.end()))

        base_type = java_type.split("<")[0].strip()
        mcp_type = _JAVA_TYPE_MAP.get(base_type, "string")

        name = param_alias or param_name

        if annotation == "PathParam":
            required = True
        else:
            required = False

        params.append(ParameterSpec(
            name=name,
            type=mcp_type,
            description="",
            required=required,
            default=None,
        ))

    # Detect unannotated params as implicit request body (JAX-RS convention)
    if http_method in ("POST", "PUT", "DELETE", "PATCH"):
        _UNANNOTATED_PARAM_RE = re.compile(
            r'(?<!\w)([\w]+(?:<[\w<>,\s]+>)?)\s+(\w+)\s*(?:,|$)'
        )
        for match in _UNANNOTATED_PARAM_RE.finditer(param_string):
            # Skip if this region overlaps with an annotated param
            if any(s <= match.start() < e for s, e in annotated_spans):
                continue
            java_type = match.group(1).strip()
            param_name = match.group(2)
            # Skip JAX-RS context types
            if java_type in (
                "Context", "UriInfo", "HttpHeaders", "Request",
                "SecurityContext", "HttpServletRequest", "HttpServletResponse",
                "AsyncResponse",
            ):
                continue
            base_type = java_type.split("<")[0].strip()
            mcp_type = _JAVA_TYPE_MAP.get(base_type, "object")
            # Store original type for POJO resolution
            orig_type = base_type if mcp_type == "object" else None
            params.append(ParameterSpec(
                name=param_name,
                type=mcp_type,
                description="",
                required=True,
                default=None,
                original_type=orig_type,
            ))

    return params


def _extract_kotlin_spring_params(param_string: str) -> list[ParameterSpec]:
    """Extract parameters from a Kotlin Spring method signature string."""
    params: list[ParameterSpec] = []

    for match in _KOTLIN_SPRING_PARAM_RE.finditer(param_string):
        annotation = match.group(1)  # RequestParam, PathVariable, RequestBody
        ann_args = match.group(2) or ""
        param_name = match.group(3)
        kotlin_type = match.group(4).strip().rstrip("?")  # strip nullable marker

        base_type = kotlin_type.split("<")[0].strip()
        mcp_type = _JAVA_TYPE_MAP.get(base_type, "string")

        # Skip injected Spring/Kotlin types
        if kotlin_type in (
            "HttpServletRequest", "HttpServletResponse", "HttpSession",
            "Principal", "Authentication", "BindingResult", "Model",
            "RedirectAttributes", "Pageable", "MultipartFile",
        ):
            continue

        ann = _parse_annotation_args(ann_args)
        name = ann.get("name", param_name)
        default_value = ann.get("defaultValue")

        if annotation == "PathVariable":
            required = True
        elif annotation == "RequestBody":
            required = True
            mcp_type = "object"
        elif "required" in ann:
            required = ann["required"] == "true"
        else:
            required = default_value is None

        params.append(ParameterSpec(
            name=name,
            type=mcp_type,
            description="",
            required=required,
            default=default_value,
        ))

    return params


def _extract_kotlin_jaxrs_params(param_string: str) -> list[ParameterSpec]:
    """Extract parameters from a Kotlin JAX-RS method signature string."""
    params: list[ParameterSpec] = []

    for match in _KOTLIN_JAXRS_PARAM_RE.finditer(param_string):
        annotation = match.group(1)  # QueryParam, PathParam, FormParam
        param_alias = match.group(2)  # name from annotation
        param_name = match.group(3)
        kotlin_type = match.group(4).strip().rstrip("?")  # strip nullable marker

        base_type = kotlin_type.split("<")[0].strip()
        mcp_type = _JAVA_TYPE_MAP.get(base_type, "string")

        name = param_alias or param_name
        required = annotation == "PathParam"

        params.append(ParameterSpec(
            name=name,
            type=mcp_type,
            description="",
            required=required,
            default=None,
        ))

    return params


def _extract_micronaut_params(param_string: str) -> list[ParameterSpec]:
    """Extract parameters from a Micronaut method signature string."""
    params: list[ParameterSpec] = []

    for match in _MICRONAUT_PARAM_RE.finditer(param_string):
        annotation = match.group(1)  # QueryValue, PathVariable, Body
        ann_name = match.group(2) or ""  # optional name override
        java_type = match.group(3).strip()
        param_name = match.group(4)

        base_type = java_type.split("<")[0].strip()
        mcp_type = _JAVA_TYPE_MAP.get(base_type, "string")

        name = ann_name if ann_name else param_name

        if annotation == "PathVariable":
            required = True
        elif annotation == "Body":
            required = True
            mcp_type = "object"
        else:
            required = False

        params.append(ParameterSpec(
            name=name,
            type=mcp_type,
            description="",
            required=required,
            default=None,
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


def _detect_framework(source: str) -> str:
    """Detect which Java REST framework a source file uses."""
    if re.search(r'import\s+(?:javax|jakarta)\.ws\.rs', source):
        return "jaxrs"
    if re.search(r'import\s+io\.micronaut', source):
        return "micronaut"
    if re.search(r'@(?:Rest)?Controller|@(?:Get|Post|Put|Delete|Patch)Mapping', source):
        return "spring"
    return "unknown"


# ---------------------------------------------------------------------------
# Main analysis function
# ---------------------------------------------------------------------------

def analyze_java_file(root: Path, file_info: FileInfo) -> Optional[JavaAnalysisResult]:
    """Analyze a single Java or Kotlin file for REST endpoints.

    For Java files, uses the javalang AST parser when available and falls back
    to regex.  Kotlin files always use the regex path (javalang is Java-only).
    """
    if file_info.language not in (Language.JAVA, Language.KOTLIN):
        return None

    try:
        source = (root / file_info.path).read_text(errors="replace")
    except OSError:
        return None

    result = JavaAnalysisResult()

    if "@SpringBootApplication" in source:
        result.has_spring_boot = True

    is_kotlin = file_info.language == Language.KOTLIN

    # -----------------------------------------------------------------------
    # AST path: javalang for Java files
    # -----------------------------------------------------------------------
    if _HAS_JAVALANG and not is_kotlin:
        ast_caps = _ast_analyze_string(source)
        if ast_caps:
            _ast_caps_to_result(ast_caps, file_info, result)
            if result.endpoints and not result.has_spring_boot:
                return result
            # If AST produced endpoints, trust them; keep has_spring_boot from above
            if result.endpoints:
                return result
        # Fall through to regex if AST found nothing

    # -----------------------------------------------------------------------
    # Regex fallback
    # -----------------------------------------------------------------------
    framework = _detect_framework(source)

    if framework == "jaxrs":
        if is_kotlin:
            _analyze_kotlin_jaxrs(source, file_info, result)
        else:
            _analyze_jaxrs(source, file_info, result)
    elif framework == "micronaut":
        _analyze_micronaut(source, file_info, result)
    elif is_kotlin:
        _analyze_kotlin_spring(source, file_info, result)
    else:
        _analyze_spring(source, file_info, result)

    if not result.endpoints and not result.controllers and not result.has_spring_boot:
        return None

    return result


def _ast_caps_to_result(
    caps: list,
    file_info: FileInfo,
    result: JavaAnalysisResult,
) -> None:
    """Convert java_ast capability dicts into SpringEndpoint objects in *result*."""
    seen_classes: set[str] = set()

    for cap in caps:
        class_name = cap.get("_controller_class", "")
        if class_name and class_name not in seen_classes:
            seen_classes.add(class_name)
            result.controllers.append(class_name)

        params: list[ParameterSpec] = []
        for p in cap.get("parameters", []):
            params.append(ParameterSpec(
                name=p["name"],
                type=p["type"],
                description=p.get("description", ""),
                required=p.get("required", True),
                default=p.get("default"),
                location=p.get("source", ""),
                original_type=p.get("_original_java_type"),
            ))

        result.endpoints.append(SpringEndpoint(
            http_method=cap["http_method"],
            path=cap["path"],
            # Preserve original Java method name so existing tests can look it up
            method_name=cap.get("_java_method_name", cap.get("name", "")),
            description=cap.get("description", ""),
            parameters=params,
            return_type=cap.get("return_type", "object"),
            source_file=file_info.path,
            controller_class=class_name,
            controller_path="",
        ))


def _analyze_spring(source: str, file_info: FileInfo, result: JavaAnalysisResult) -> None:
    """Extract Spring endpoints from source."""
    controller_match = _CONTROLLER_CLASS_RE.search(source)
    if not controller_match:
        return

    controller_name = controller_match.group(1)
    result.controllers.append(controller_name)

    class_path = ""
    class_mapping = _CLASS_REQUEST_MAPPING_RE.search(source)
    if class_mapping:
        class_path = class_mapping.group(1).rstrip("/")

    for match in _METHOD_ANNOTATION_RE.finditer(source):
        annotation = match.group(1)
        method_path = match.group(2) or ""
        request_method_override = match.group(3)
        return_type = match.group(4)
        method_name = match.group(5)

        paren_start = match.end() - 1
        param_string = _extract_balanced_parens(source, paren_start)

        if annotation == "RequestMapping" and request_method_override:
            http_method = request_method_override
        elif annotation in _HTTP_METHOD_ANNOTATIONS:
            http_method = _HTTP_METHOD_ANNOTATIONS[annotation]
        else:
            http_method = "GET"

        full_path = class_path
        if method_path:
            if not method_path.startswith("/"):
                method_path = "/" + method_path
            full_path += method_path

        params = _extract_spring_params(param_string)
        mcp_return = _JAVA_TYPE_MAP.get(return_type, "string")

        result.endpoints.append(SpringEndpoint(
            http_method=http_method,
            path=full_path or "/",
            method_name=method_name,
            description=_make_description(method_name),
            parameters=params,
            return_type=mcp_return,
            source_file=file_info.path,
            controller_class=controller_name,
            controller_path=class_path,
        ))


def _analyze_jaxrs(source: str, file_info: FileInfo, result: JavaAnalysisResult) -> None:
    """Extract JAX-RS endpoints from source."""
    class_match = _JAXRS_CLASS_PATH_RE.search(source)
    if not class_match:
        return

    class_path = class_match.group(1).rstrip("/")
    if class_path and not class_path.startswith("/"):
        class_path = "/" + class_path
    controller_name = class_match.group(2)
    result.controllers.append(controller_name)

    for match in _JAXRS_METHOD_RE.finditer(source):
        http_method = match.group(1)  # GET, POST, etc.
        method_path = match.group(2) or ""
        return_type = match.group(3)
        method_name = match.group(4)

        paren_start = match.end() - 1
        param_string = _extract_balanced_parens(source, paren_start)

        full_path = class_path
        if method_path:
            if not method_path.startswith("/"):
                method_path = "/" + method_path
            full_path += method_path

        # Normalize JAX-RS regex path params: {id: \\d+} → {id}
        full_path = _strip_jaxrs_regex(full_path)

        params = _extract_jaxrs_params(param_string, http_method=http_method)
        mcp_return = _JAVA_TYPE_MAP.get(return_type, "string")

        result.endpoints.append(SpringEndpoint(
            http_method=http_method,
            path=full_path or "/",
            method_name=method_name,
            description=_make_description(method_name),
            parameters=params,
            return_type=mcp_return,
            source_file=file_info.path,
            controller_class=controller_name,
            controller_path=class_path,
        ))


def _analyze_kotlin_jaxrs(source: str, file_info: FileInfo, result: JavaAnalysisResult) -> None:
    """Extract JAX-RS endpoints from a Kotlin source file."""
    class_match = _KOTLIN_JAXRS_CLASS_PATH_RE.search(source)
    if not class_match:
        return

    class_path = class_match.group(1).rstrip("/")
    controller_name = class_match.group(2)
    result.controllers.append(controller_name)

    for match in _KOTLIN_JAXRS_METHOD_RE.finditer(source):
        http_method = match.group(1)
        method_path = match.group(2) or ""
        method_name = match.group(3)

        paren_start = match.end() - 1
        param_string = _extract_balanced_parens(source, paren_start)

        full_path = class_path
        if method_path:
            if not method_path.startswith("/"):
                method_path = "/" + method_path
            full_path += method_path

        full_path = _strip_jaxrs_regex(full_path)
        params = _extract_kotlin_jaxrs_params(param_string)

        result.endpoints.append(SpringEndpoint(
            http_method=http_method,
            path=full_path or "/",
            method_name=method_name,
            description=_make_description(method_name),
            parameters=params,
            return_type="string",
            source_file=file_info.path,
            controller_class=controller_name,
            controller_path=class_path,
        ))


def _analyze_kotlin_spring(source: str, file_info: FileInfo, result: JavaAnalysisResult) -> None:
    """Extract Spring (Boot / MVC) endpoints from a Kotlin source file."""
    if "@SpringBootApplication" in source:
        result.has_spring_boot = True

    controller_match = _KOTLIN_SPRING_CLASS_RE.search(source)
    if not controller_match:
        return

    controller_name = controller_match.group(1)
    result.controllers.append(controller_name)

    class_path = ""
    class_mapping = _KOTLIN_CLASS_REQUEST_MAPPING_RE.search(source)
    if class_mapping:
        class_path = class_mapping.group(1).rstrip("/")

    for match in _KOTLIN_SPRING_METHOD_RE.finditer(source):
        annotation = match.group(1)
        method_path = match.group(2) or ""
        request_method_override = match.group(3)
        method_name = match.group(4)

        paren_start = match.end() - 1
        param_string = _extract_balanced_parens(source, paren_start)

        if annotation == "RequestMapping" and request_method_override:
            http_method = request_method_override
        elif annotation in _HTTP_METHOD_ANNOTATIONS:
            http_method = _HTTP_METHOD_ANNOTATIONS[annotation]
        else:
            http_method = "GET"

        full_path = class_path
        if method_path:
            if not method_path.startswith("/"):
                method_path = "/" + method_path
            full_path += method_path

        params = _extract_kotlin_spring_params(param_string)
        mcp_return = "string"

        result.endpoints.append(SpringEndpoint(
            http_method=http_method,
            path=full_path or "/",
            method_name=method_name,
            description=_make_description(method_name),
            parameters=params,
            return_type=mcp_return,
            source_file=file_info.path,
            controller_class=controller_name,
            controller_path=class_path,
        ))


def _analyze_micronaut(source: str, file_info: FileInfo, result: JavaAnalysisResult) -> None:
    """Extract Micronaut endpoints from source."""
    class_match = _MICRONAUT_CLASS_RE.search(source)
    if not class_match:
        return

    class_path = class_match.group(1).rstrip("/")
    controller_name = class_match.group(2)
    result.controllers.append(controller_name)

    _MICRONAUT_HTTP_METHODS = {
        "Get": "GET", "Post": "POST", "Put": "PUT",
        "Delete": "DELETE", "Patch": "PATCH",
    }

    for match in _MICRONAUT_METHOD_RE.finditer(source):
        annotation = match.group(1)  # Get, Post, etc.
        method_path = match.group(2) or ""
        return_type = match.group(3)
        method_name = match.group(4)

        paren_start = match.end() - 1
        param_string = _extract_balanced_parens(source, paren_start)

        http_method = _MICRONAUT_HTTP_METHODS.get(annotation, "GET")

        full_path = class_path
        if method_path:
            if not method_path.startswith("/"):
                method_path = "/" + method_path
            full_path += method_path

        params = _extract_micronaut_params(param_string)
        mcp_return = _JAVA_TYPE_MAP.get(return_type, "string")

        result.endpoints.append(SpringEndpoint(
            http_method=http_method,
            path=full_path or "/",
            method_name=method_name,
            description=_make_description(method_name),
            parameters=params,
            return_type=mcp_return,
            source_file=file_info.path,
            controller_class=controller_name,
            controller_path=class_path,
        ))


# ---------------------------------------------------------------------------
# Capability conversion (framework-agnostic)
# ---------------------------------------------------------------------------

def _resolve_pojo_properties(
    params: list[ParameterSpec],
    pojo_sources: dict[str, str],
) -> None:
    """Resolve object params with original_type to nested properties using POJO sources."""
    from mcp_anything.analysis.schema_extractor import extract_java_pojo_fields

    for param in params:
        if param.type != "object" or not param.original_type:
            continue
        type_name = param.original_type
        # Search all sources for the class definition
        for source in pojo_sources.values():
            fields = extract_java_pojo_fields(source, type_name)
            if fields:
                param.properties = [
                    ParameterSpec(
                        name=f.name,
                        type=f.type,
                        description=f.description,
                        required=f.required,
                    )
                    for f in fields
                ]
                break


def java_results_to_capabilities(
    results: dict[str, JavaAnalysisResult],
    root: Optional[Path] = None,
) -> list[Capability]:
    """Convert Java analysis results into Capability objects."""
    capabilities: list[Capability] = []
    seen: set[str] = set()

    # Collect all Java/Kotlin source content for POJO resolution
    pojo_sources: dict[str, str] = {}
    if root:
        for java_file in root.rglob("*.java"):
            try:
                rel = str(java_file.relative_to(root))
                pojo_sources[rel] = java_file.read_text(errors="replace")
            except OSError:
                pass
        for kt_file in root.rglob("*.kt"):
            try:
                rel = str(kt_file.relative_to(root))
                pojo_sources[rel] = kt_file.read_text(errors="replace")
            except OSError:
                pass

    for file_path, result in results.items():
        for ep in result.endpoints:
            tool_name = _endpoint_to_tool_name(ep)

            if tool_name in seen:
                continue
            seen.add(tool_name)

            # Resolve POJO types to nested properties
            if pojo_sources:
                _resolve_pojo_properties(ep.parameters, pojo_sources)

            capabilities.append(Capability(
                name=tool_name,
                description=ep.description,
                category="api",
                parameters=ep.parameters,
                return_type=ep.return_type,
                source_file=file_path,
                source_function=ep.method_name,
                ipc_type=IPCType.PROTOCOL,
                http_method=ep.http_method,
                http_path=ep.path,
            ))

    return capabilities


def _strip_jaxrs_regex(path: str) -> str:
    """Normalize JAX-RS regex path params: {id: \\d+} → {id}."""
    return re.sub(r'\{(\w+)[^}]*\}', r'{\1}', path)


def _endpoint_to_tool_name(ep: SpringEndpoint) -> str:
    """Generate a snake_case tool name from an endpoint."""
    normalized = _strip_jaxrs_regex(ep.path)
    path_parts = normalized.strip("/").split("/")
    if path_parts and path_parts[0] in ("api", "v1", "v2", "v3"):
        path_parts = path_parts[1:]

    clean_parts = []
    for part in path_parts:
        if part.startswith("{") and part.endswith("}"):
            clean_parts.append(f"by_{part[1:-1]}")
        else:
            clean_parts.append(part)

    method_prefix = ep.http_method.lower()
    path_name = "_".join(clean_parts) if clean_parts else ep.method_name

    name = f"{method_prefix}_{path_name}"
    name = re.sub(r"[^a-z0-9_]", "_", name.lower())
    name = re.sub(r"_+", "_", name).strip("_")
    return name
