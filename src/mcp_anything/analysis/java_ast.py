"""AST-based Java REST endpoint analyzer using the javalang library.

Handles JAX-RS/Jersey, Spring MVC/Boot, and Micronaut annotations correctly
regardless of annotation ordering, inline comments, multiline annotations, or
path parameter regex constraints.

Falls back gracefully when javalang is not installed.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

try:
    import javalang
    import javalang.tree
    import javalang.parser
    _HAS_JAVALANG = True
except ImportError:  # pragma: no cover
    _HAS_JAVALANG = False
    javalang = None  # type: ignore


# ---------------------------------------------------------------------------
# Constant maps — must match the values used by the existing regex analyzer
# ---------------------------------------------------------------------------

# Java type name → MCP parameter type string (same values as legacy _JAVA_TYPE_MAP)
_JAVA_TO_MCP_TYPE: dict[str, str] = {
    "String": "string", "UUID": "string", "char": "string", "Character": "string",
    "URI": "string", "URL": "string",
    "int": "integer", "Integer": "integer",
    "long": "integer", "Long": "integer",
    "short": "integer", "Short": "integer",
    "byte": "integer", "Byte": "integer",
    "BigInteger": "integer",
    "double": "float", "Double": "float",
    "float": "float", "Float": "float",
    "BigDecimal": "float",
    "boolean": "boolean", "Boolean": "boolean",
    "List": "array", "ArrayList": "array", "LinkedList": "array",
    "Set": "array", "HashSet": "array", "TreeSet": "array",
    "Collection": "array", "Iterable": "array", "Flux": "array",
    "Map": "object", "HashMap": "object", "LinkedHashMap": "object",
    "TreeMap": "object", "Hashtable": "object",
    "Response": "object", "void": "object", "Void": "object",
    "Object": "object", "Any": "object",
    "Optional": "object", "CompletableFuture": "object", "Future": "object",
    "Mono": "object",
    # Kotlin
    "Int": "integer",
}

# Annotations that indicate an HTTP method (None = need to inspect method= attr)
_HTTP_METHOD_ANNOTATIONS: dict[str, Optional[str]] = {
    # JAX-RS
    "GET": "GET", "POST": "POST", "PUT": "PUT",
    "DELETE": "DELETE", "PATCH": "PATCH",
    "HEAD": "HEAD", "OPTIONS": "OPTIONS",
    # Spring MVC
    "GetMapping": "GET", "PostMapping": "POST",
    "PutMapping": "PUT", "DeleteMapping": "DELETE",
    "PatchMapping": "PATCH",
    "RequestMapping": None,   # determined by method= attribute
    # Micronaut
    "Get": "GET", "Post": "POST", "Put": "PUT",
    "Delete": "DELETE", "Patch": "PATCH",
}

# Annotations that also carry a path value
_PATH_ANNOTATIONS = frozenset({
    "Path",
    "RequestMapping",
    "GetMapping", "PostMapping", "PutMapping", "DeleteMapping", "PatchMapping",
    "Get", "Post", "Put", "Delete", "Patch",   # Micronaut
})

# Parameter annotation → where the value comes from
_PARAM_SOURCE_MAP: dict[str, str] = {
    # JAX-RS
    "PathParam": "path",
    "QueryParam": "query",
    "HeaderParam": "header",
    "CookieParam": "cookie",
    "FormParam": "body",
    "MatrixParam": "query",
    # Spring MVC
    "PathVariable": "path",
    "RequestParam": "query",
    "RequestHeader": "header",
    "RequestBody": "body",
    "CookieValue": "cookie",
    # Micronaut
    "QueryValue": "query",
    "Body": "body",
}

# Default required value per annotation (None = compute from attrs)
_PARAM_REQUIRED_DEFAULT: dict[str, Optional[bool]] = {
    "PathParam": True,   "QueryParam": False,
    "HeaderParam": False, "CookieParam": False,
    "FormParam": False,   "MatrixParam": False,
    "PathVariable": True, "RequestParam": None,   # computed
    "RequestHeader": False, "RequestBody": True,
    "CookieValue": False,
    "QueryValue": False, "Body": True,
}

# Annotation types whose parameters should be ignored entirely
_IGNORE_ANNOTATIONS = frozenset({
    "Context", "Suspended", "BeanParam",
})

# Java/Kotlin parameter types that are framework-injected — skip them
_IGNORE_PARAM_TYPES = frozenset({
    "UriInfo", "HttpHeaders", "Request", "SecurityContext",
    "HttpServletRequest", "HttpServletResponse", "HttpSession",
    "Principal", "Authentication", "BindingResult", "Model",
    "RedirectAttributes", "Pageable", "MultipartFile",
    "AsyncResponse",
})

# MediaType constant name → MIME type string
_MEDIA_TYPE_CONSTANTS: dict[str, str] = {
    "APPLICATION_JSON": "application/json",
    "APPLICATION_XML": "application/xml",
    "APPLICATION_OCTET_STREAM": "application/octet-stream",
    "APPLICATION_FORM_URLENCODED": "application/x-www-form-urlencoded",
    "MULTIPART_FORM_DATA": "multipart/form-data",
    "TEXT_PLAIN": "text/plain",
    "TEXT_HTML": "text/html",
    "TEXT_XML": "text/xml",
    "SERVER_SENT_EVENTS": "text/event-stream",
    "WILDCARD": "*/*",
}

# Regex to strip JAX-RS path regex constraints: {id: [0-9]+} → {id}
_PATH_CONSTRAINT_RE = re.compile(r'\{(\w+)\s*:[^}]*\}')

# Regex for Javadoc blocks
_JAVADOC_RE = re.compile(r'/\*\*(.+?)\*/', re.DOTALL)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_java_string(source: str, app_base_path: str = "") -> list[dict[str, Any]]:
    """Parse Java source from a string. Returns [] on any parse error."""
    if not _HAS_JAVALANG:
        return []
    try:
        tree = javalang.parse.parse(source)
    except Exception:
        return []
    return _extract_from_tree(tree, source, app_base_path)


def analyze_java_file(file_path: Path, app_base_path: str = "") -> list[dict[str, Any]]:
    """Parse a single .java file. Returns [] on any error."""
    try:
        source = file_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    return analyze_java_string(source, app_base_path)


def analyze_java_codebase(root_path: Path, app_base_path: str = "") -> list[dict[str, Any]]:
    """Walk all .java files under root_path and return unified capability list."""
    all_caps: list[dict[str, Any]] = []
    seen: set[str] = set()
    for java_file in root_path.rglob("*.java"):
        for cap in analyze_java_file(java_file, app_base_path):
            key = f"{cap['http_method']}:{cap['path']}"
            if key not in seen:
                seen.add(key)
                all_caps.append(cap)
    return all_caps


# ---------------------------------------------------------------------------
# Core extraction
# ---------------------------------------------------------------------------

def _extract_from_tree(
    tree: Any,
    source: str,
    app_base_path: str,
) -> list[dict[str, Any]]:
    """Walk the javalang AST and extract all REST endpoint capabilities."""
    app_path = _find_app_base_path(tree) or app_base_path
    lines = source.splitlines()
    capabilities: list[dict[str, Any]] = []

    for type_decl in tree.types:
        if not isinstance(
            type_decl,
            (javalang.tree.ClassDeclaration, javalang.tree.InterfaceDeclaration),
        ):
            continue

        class_base = _get_class_base_path(type_decl.annotations)
        full_class_path = _join_paths(app_path, class_base)
        class_consumes = _extract_media_types(type_decl.annotations, "Consumes")
        class_produces = _extract_media_types(type_decl.annotations, "Produces")

        for method in type_decl.methods:
            cap = _extract_method_cap(
                method, full_class_path,
                class_consumes, class_produces,
                source, lines,
                type_decl.name,
            )
            if cap is not None:
                capabilities.append(cap)

    return capabilities


def _extract_method_cap(
    method: Any,
    class_path: str,
    class_consumes: list[str],
    class_produces: list[str],
    source: str,
    lines: list[str],
    class_name: str,
) -> Optional[dict[str, Any]]:
    """Return a capability dict for a method if it is a REST endpoint, else None."""
    http_method = _get_http_method(method.annotations)
    if not http_method:
        return None

    method_path = _get_path_value(method.annotations)
    full_path = _strip_path_regex(_join_paths(class_path, method_path))

    method_consumes = _extract_media_types(method.annotations, "Consumes") or class_consumes
    method_produces = _extract_media_types(method.annotations, "Produces") or class_produces

    javadoc = _extract_javadoc(source, method)
    description = _first_sentence(javadoc) if javadoc else _name_to_description(method.name)

    params = _extract_parameters(method, http_method)
    if javadoc:
        _enrich_param_docs(params, javadoc)

    return_type = _map_return_type(method.return_type)
    name = _build_tool_name(http_method, full_path, method.name)

    return {
        "name": name,
        "http_method": http_method,
        "path": full_path or "/",
        "description": description,
        "parameters": params,
        "return_type": return_type,
        "produces": method_produces,
        "consumes": method_consumes,
        "backend_type": "http",
        # Private fields used by java_analyzer integration only
        "_java_method_name": method.name,
        "_controller_class": class_name,
    }


# ---------------------------------------------------------------------------
# Annotation helpers
# ---------------------------------------------------------------------------

def _find_app_base_path(tree: Any) -> str:
    """Find @ApplicationPath on an Application subclass, return path or ''."""
    for type_decl in tree.types:
        if not isinstance(type_decl, javalang.tree.ClassDeclaration):
            continue
        # Must extend Application or a JAX-RS Application class
        extends = type_decl.extends
        if not extends:
            continue
        ext_name = extends.name if hasattr(extends, "name") else str(extends)
        if "Application" not in ext_name:
            continue
        for ann in type_decl.annotations:
            if ann.name == "ApplicationPath":
                val = _ann_string(ann)
                if val is not None:
                    return val.rstrip("/")
    return ""


def _get_class_base_path(annotations: list) -> str:
    """Extract class-level path from @Path, @RequestMapping, or @Controller."""
    for ann in annotations:
        if ann.name == "Path":
            return _ann_string(ann) or ""
        elif ann.name == "RequestMapping":
            val = _ann_named(ann, ("value", "path"))
            if val is not None:
                return val
            val = _ann_string(ann)
            if val is not None:
                return val
        elif ann.name == "Controller":
            # Micronaut: @Controller("/api/path") carries the base path
            val = _ann_string(ann)
            if val:  # non-empty → Micronaut style
                return val
    return ""


def _get_http_method(annotations: list) -> Optional[str]:
    """Return the HTTP method string from the annotation list, or None."""
    for ann in annotations:
        if ann.name not in _HTTP_METHOD_ANNOTATIONS:
            continue
        method = _HTTP_METHOD_ANNOTATIONS[ann.name]
        if method is not None:
            return method
        # @RequestMapping: inspect method= attribute
        method_val = _ann_named(ann, ("method",))
        if method_val:
            m = re.search(r'\b(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\b',
                          method_val.upper())
            if m:
                return m.group(1)
        return "GET"   # @RequestMapping without method= defaults to GET
    return None


def _get_path_value(annotations: list) -> str:
    """Extract path value from method-level annotations."""
    for ann in annotations:
        if ann.name == "Path":
            return _ann_string(ann) or ""
        elif ann.name in _PATH_ANNOTATIONS and ann.name != "Path":
            val = _ann_named(ann, ("value", "path"))
            if val is None:
                val = _ann_string(ann)
            return val or ""
    return ""


def _extract_media_types(annotations: list, annotation_name: str) -> list[str]:
    """Extract MIME type strings from @Produces or @Consumes."""
    for ann in annotations:
        if ann.name != annotation_name:
            continue
        values = _collect_elem_strings(ann.element)
        return [_resolve_media_type(v) for v in values if v]
    return []


# ---------------------------------------------------------------------------
# Annotation element value extraction
# ---------------------------------------------------------------------------

def _ann_string(ann: Any) -> Optional[str]:
    """Get a single string value from annotation like @Path("/users")."""
    return _element_to_str(_resolve_named_or_direct(ann.element))


def _ann_named(ann: Any, names: tuple) -> Optional[str]:
    """Get a named attribute value like value= or path= from annotation element."""
    elem = ann.element
    if not isinstance(elem, (list, tuple)):
        return None
    for item in elem:
        if hasattr(item, "name") and item.name in names:
            return _element_to_str(item.value)
    return None


def _resolve_named_or_direct(elem: Any) -> Any:
    """For element_value_pairs list extract value=/path= pair; else return elem."""
    if elem is None:
        return None
    # Only a Python list/tuple signals named pairs (@Annotation(key=val, ...))
    if isinstance(elem, (list, tuple)):
        for pair in elem:
            if hasattr(pair, "name") and pair.name in ("value", "path", None):
                return pair.value
        # No value=/path= pair found — don't misuse other attrs (e.g. required=false)
        return None
    # Direct value: Literal, MemberReference, ArrayInitializer, …
    return elem


def _iter_pairs(elem: Any):
    """Yield ElementValuePair items only when elem is a Python list/tuple."""
    if isinstance(elem, (list, tuple)):
        yield from elem


def _element_to_str(elem: Any) -> Optional[str]:
    """Convert a javalang element value node to a Python string."""
    if elem is None:
        return None

    # String / number literal: value attribute holds '"string"' or '42'
    if hasattr(elem, "value") and not hasattr(elem, "member") and not hasattr(elem, "operandl"):
        val = str(elem.value)
        if val.startswith('"') and val.endswith('"'):
            return val[1:-1]
        if val.startswith("'") and val.endswith("'"):
            return val[1:-1]
        return val

    # Member reference: MediaType.APPLICATION_JSON → "APPLICATION_JSON"
    if hasattr(elem, "member"):
        return str(elem.member)

    # Binary expression: "/users/" + CONST — extract left literal if possible
    if hasattr(elem, "operandl") and hasattr(elem, "operandr"):
        left = _element_to_str(elem.operandl)
        right = _element_to_str(elem.operandr)
        if left and right:
            return left + right
        return left or right

    # Array initializer — return first element
    for attr in ("initializers", "values"):
        items = getattr(elem, attr, None)
        if items:
            return _element_to_str(items[0])

    return str(elem) if elem else None


def _collect_elem_strings(elem: Any) -> list[str]:
    """Collect all string values from an annotation element (handles arrays)."""
    if elem is None:
        return []

    # Array initializer: {val1, val2, ...}
    for attr in ("initializers", "values"):
        items = getattr(elem, attr, None)
        if items:
            result = []
            for item in items:
                v = _element_to_str(item)
                if v:
                    result.append(v)
            return result

    # Python list of pairs (element_value_pairs)
    if isinstance(elem, (list, tuple)):
        result = []
        for item in elem:
            if hasattr(item, "name") and hasattr(item, "value"):
                v = _element_to_str(item.value)
            else:
                v = _element_to_str(item)
            if v:
                result.append(v)
        return result

    v = _element_to_str(elem)
    return [v] if v else []


def _get_ann_attr(ann: Any, name: str) -> Optional[str]:
    """Get a specific named attribute from an annotation like required=false."""
    elem = ann.element
    if not isinstance(elem, (list, tuple)):
        return None
    for item in elem:
        if hasattr(item, "name") and item.name == name:
            return _element_to_str(item.value)
    return None


def _resolve_media_type(value: str) -> str:
    """Resolve a constant name or MIME literal to a MIME type string."""
    if not value:
        return ""
    if "/" in value:
        return value
    # Full constant like "APPLICATION_JSON"
    if value in _MEDIA_TYPE_CONSTANTS:
        return _MEDIA_TYPE_CONSTANTS[value]
    # Member reference like "MediaType.APPLICATION_JSON" → last segment
    if "." in value:
        const = value.split(".")[-1]
        if const in _MEDIA_TYPE_CONSTANTS:
            return _MEDIA_TYPE_CONSTANTS[const]
    return value


# ---------------------------------------------------------------------------
# Parameter extraction
# ---------------------------------------------------------------------------

def _extract_parameters(method: Any, http_method: str) -> list[dict[str, Any]]:
    """Extract REST parameters from a method declaration."""
    params: list[dict[str, Any]] = []
    is_mutating = http_method in ("POST", "PUT", "PATCH", "DELETE")

    for fp in (method.parameters or []):
        type_name = _get_type_name(fp.type)

        # Skip framework-injected types
        if type_name in _IGNORE_PARAM_TYPES:
            continue

        ann_names = {a.name for a in (fp.annotations or [])}
        if ann_names & _IGNORE_ANNOTATIONS:
            continue

        source: Optional[str] = None
        param_name: str = fp.name
        default_val: Optional[str] = None
        required: Optional[bool] = None   # None = not yet determined

        for ann in (fp.annotations or []):
            if ann.name in _PARAM_SOURCE_MAP:
                source = _PARAM_SOURCE_MAP[ann.name]

                # Get required default for this annotation
                req_default = _PARAM_REQUIRED_DEFAULT.get(ann.name)

                if req_default is None:
                    # Compute from annotation attributes (Spring @RequestParam)
                    req_attr = _get_ann_attr(ann, "required")
                    dv = _get_ann_attr(ann, "defaultValue")
                    if req_attr is not None:
                        required = req_attr.lower() != "false"
                    else:
                        required = dv is None
                    if dv is not None:
                        default_val = dv
                else:
                    required = req_default

                # Name override: @QueryParam("limit") or @RequestParam(value="n")
                alias = _ann_string(ann)
                if alias and alias != param_name and _is_safe_name(alias):
                    param_name = alias
                else:
                    named = _ann_named(ann, ("value", "name"))
                    if named and _is_safe_name(named):
                        param_name = named

            elif ann.name == "DefaultValue":
                # JAX-RS @DefaultValue("10")
                dv = _ann_string(ann)
                if dv is not None:
                    default_val = dv

        # Handle unannotated parameters
        if source is None:
            if is_mutating:
                source = "body"
                required = True
            else:
                continue   # skip unannotated GET params

        if required is None:
            required = True

        py_type = _map_param_type(type_name, source)
        original_type: Optional[str] = None
        if source == "body" and py_type == "object" and type_name not in _JAVA_TO_MCP_TYPE:
            original_type = type_name

        params.append({
            "name": param_name,
            "type": py_type,
            "source": source,
            "required": required,
            "default": default_val,
            "description": "",
            "_original_java_type": original_type,
        })

    return params


def _is_safe_name(s: str) -> bool:
    """Return True if s looks like a valid parameter name (not a path segment)."""
    return bool(s) and "/" not in s and s.isidentifier()


def _get_type_name(type_node: Any) -> str:
    """Extract the base type name from a javalang type node."""
    if type_node is None:
        return "void"
    if hasattr(type_node, "name"):
        return type_node.name
    if hasattr(type_node, "sub_type"):
        return _get_type_name(type_node.sub_type)
    return str(type_node)


def _map_param_type(type_name: str, source: str) -> str:
    """Map a Java type name to a MCP parameter type string.

    Body parameters always map to 'object' to match the legacy regex behavior.
    """
    if source == "body":
        return "object"
    base = type_name.split("<")[0].strip().rstrip("?")
    return _JAVA_TO_MCP_TYPE.get(base, "string")


def _map_return_type(type_node: Any) -> str:
    """Map a javalang return type node to a MCP type string."""
    if type_node is None:
        return "object"
    name = _get_type_name(type_node)
    if name == "void":
        return "object"
    base = name.split("<")[0].strip().rstrip("?")
    return _JAVA_TO_MCP_TYPE.get(base, "string")


# ---------------------------------------------------------------------------
# Javadoc extraction
# ---------------------------------------------------------------------------

def _extract_javadoc(source: str, method: Any) -> str:
    """Extract the Javadoc comment that immediately precedes a method.

    Uses the method's line position to locate the nearest ``/** */`` block.
    """
    if not hasattr(method, "position") or method.position is None:
        return ""

    # Find the character offset of the method's first annotation (or the method itself)
    method_line = method.position[0]  # 1-based line number
    first_line = method_line
    for ann in (method.annotations or []):
        if hasattr(ann, "position") and ann.position:
            first_line = min(first_line, ann.position[0])

    # Slice source up to that line
    end_offset = _line_to_offset(source, first_line - 1)  # 0-based → char offset
    preceding = source[:end_offset]

    # Find the last Javadoc block in the preceding text
    last_match: Optional[re.Match] = None
    for m in _JAVADOC_RE.finditer(preceding):
        last_match = m

    if last_match is None:
        return ""

    # Reject if there is any method/class body ({}) between the Javadoc and our method
    gap = preceding[last_match.end():]
    gap_clean = re.sub(r'@\w+[^;{}\n]*(?:\([^)]*\))?\s*', '', gap)  # strip annotations
    gap_clean = re.sub(r'//[^\n]*', '', gap_clean)                   # strip // comments
    gap_clean = re.sub(r'/\*.*?\*/', '', gap_clean, flags=re.DOTALL) # strip /* */
    if "{" in gap_clean or "}" in gap_clean:
        return ""

    return last_match.group(1)


def _line_to_offset(source: str, line_index: int) -> int:
    """Return character offset for the start of 0-based *line_index*."""
    pos = 0
    for i, line in enumerate(source.splitlines(keepends=True)):
        if i >= line_index:
            return pos
        pos += len(line)
    return pos


def _first_sentence(javadoc: str) -> str:
    """Extract the first meaningful text line from a Javadoc block."""
    clean = re.sub(r'^\s*\*\s?', '', javadoc, flags=re.MULTILINE)
    clean = re.sub(r'@\w+.*$', '', clean, flags=re.MULTILINE)
    clean = clean.strip()
    if not clean:
        return ""
    for line in clean.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _enrich_param_docs(params: list[dict], javadoc: str) -> None:
    """Add @param descriptions from Javadoc to parameter dicts in-place."""
    param_re = re.compile(r'@param\s+(\w+)\s+(.+?)(?=@|\Z)', re.DOTALL)
    docs: dict[str, str] = {}
    for m in param_re.finditer(javadoc):
        raw = m.group(2).strip()
        doc = re.sub(r'\s*\n\s*\*\s*', ' ', raw).strip()
        docs[m.group(1)] = doc
    for p in params:
        if p["name"] in docs:
            p["description"] = docs[p["name"]]


# ---------------------------------------------------------------------------
# Path and name helpers
# ---------------------------------------------------------------------------

def _join_paths(*parts: str) -> str:
    """Join path segments, normalising slashes."""
    result = ""
    for part in parts:
        if not part:
            continue
        if not part.startswith("/"):
            part = "/" + part
        result = result.rstrip("/") + part
    return result


def _strip_path_regex(path: str) -> str:
    """Strip JAX-RS regex path constraints: {id: [0-9]+} → {id}."""
    return _PATH_CONSTRAINT_RE.sub(r'{\1}', path)


def _name_to_description(name: str) -> str:
    """Generate a readable description from a Java camelCase method name."""
    words = re.sub(r'([a-z])([A-Z])', r'\1 \2', name).lower()
    return words[0].upper() + words[1:] if words else name


def _build_tool_name(http_method: str, path: str, method_name: str) -> str:
    """Build a snake_case tool name from HTTP method and path."""
    normalized = _strip_path_regex(path)
    parts = normalized.strip("/").split("/")

    # Skip common API prefixes
    if parts and parts[0] in ("api", "v1", "v2", "v3", "v4"):
        parts = parts[1:]

    clean: list[str] = []
    for part in parts:
        if part.startswith("{") and part.endswith("}"):
            clean.append(f"by_{part[1:-1]}")
        elif part:
            clean.append(part)

    path_name = "_".join(clean) if clean else method_name
    name = f"{http_method.lower()}_{path_name}"
    name = re.sub(r"[^a-z0-9_]", "_", name.lower())
    name = re.sub(r"_+", "_", name).strip("_")
    return name
