"""OpenAPI/Swagger specification analyzer.

Parses OpenAPI 3.x and Swagger 2.x spec files to extract HTTP endpoints
and convert them into Capability objects for MCP server generation.
"""

import json
import re
from pathlib import Path
from typing import Optional

from mcp_anything.models.analysis import Capability, IPCType, ParameterSpec

# Common OpenAPI spec filenames
OPENAPI_FILENAMES = {
    "openapi.json", "openapi.yaml", "openapi.yml",
    "swagger.json", "swagger.yaml", "swagger.yml",
    "api-spec.json", "api-spec.yaml", "api-spec.yml",
    "api.json", "api.yaml", "api.yml",
}

# Directories where specs are commonly found (checked non-recursively)
SPEC_DIRS = {"", "docs", "doc", "api", "spec", "specs", "static", "public", "resources"}

# OpenAPI type → MCP type
_TYPE_MAP = {
    "string": "string",
    "integer": "integer",
    "number": "float",
    "boolean": "boolean",
    "array": "array",
    "object": "object",
}

# HTTP methods we care about
_HTTP_METHODS = {"get", "post", "put", "delete", "patch"}


def _load_yaml(text: str) -> Optional[dict]:
    """Try to load YAML text, falling back to JSON."""
    try:
        import yaml
        return yaml.safe_load(text)
    except ImportError:
        return None
    except Exception:
        return None


def _load_spec(text: str, is_yaml: bool) -> Optional[dict]:
    """Load an OpenAPI spec from text."""
    if is_yaml:
        result = _load_yaml(text)
        if result:
            return result
    # Try JSON (works for .json files and also YAML that's valid JSON)
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        pass
    # Last resort: try YAML for .json files that might actually be YAML
    if not is_yaml:
        return _load_yaml(text)
    return None


def _is_openapi_spec(data: dict) -> bool:
    """Check if a dict looks like an OpenAPI or Swagger spec."""
    # OpenAPI 3.x
    if "openapi" in data and "paths" in data:
        return True
    # Swagger 2.x
    if "swagger" in data and "paths" in data:
        return True
    return False


def _resolve_ref(spec: dict, ref: str) -> Optional[dict]:
    """Resolve a simple $ref pointer like '#/components/schemas/User'."""
    if not ref.startswith("#/"):
        return None
    parts = ref[2:].split("/")
    current = spec
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current if isinstance(current, dict) else None


def _extract_schema_type(schema: dict, spec: dict) -> str:
    """Extract MCP type from an OpenAPI schema object."""
    if not schema:
        return "string"

    # Handle $ref
    if "$ref" in schema:
        resolved = _resolve_ref(spec, schema["$ref"])
        if resolved:
            return _extract_schema_type(resolved, spec)
        return "object"

    schema_type = schema.get("type", "")

    # allOf, oneOf, anyOf → object
    if any(k in schema for k in ("allOf", "oneOf", "anyOf")):
        return "object"

    return _TYPE_MAP.get(schema_type, "string")


def _extract_parameters(
    operation: dict,
    path_params_from_path: set[str],
    spec: dict,
) -> list[ParameterSpec]:
    """Extract parameters from an OpenAPI operation."""
    params: list[ParameterSpec] = []
    seen: set[str] = set()

    # Path/query/header parameters
    for param in operation.get("parameters", []):
        # Resolve $ref
        if "$ref" in param:
            resolved = _resolve_ref(spec, param["$ref"])
            if resolved:
                param = resolved
            else:
                continue

        name = param.get("name", "")
        location = param.get("in", "")
        if not name or location in ("header", "cookie"):
            continue
        if name in seen:
            continue
        seen.add(name)

        schema = param.get("schema", {})
        if "$ref" in schema:
            resolved = _resolve_ref(spec, schema["$ref"])
            if resolved:
                schema = resolved

        param_type = _extract_schema_type(schema, spec)
        description = param.get("description", "")
        required = param.get("required", location == "path")
        default = schema.get("default")

        # Enum values
        enum_values = None
        if "enum" in schema:
            enum_values = [str(v) for v in schema["enum"]]

        params.append(ParameterSpec(
            name=name,
            type=param_type,
            description=description,
            required=required,
            default=str(default) if default is not None else None,
            enum_values=enum_values,
        ))

    # Request body (OpenAPI 3.x)
    request_body = operation.get("requestBody", {})
    if request_body:
        if "$ref" in request_body:
            resolved = _resolve_ref(spec, request_body["$ref"])
            if resolved:
                request_body = resolved

        content = request_body.get("content", {})
        json_content = content.get("application/json", {})
        schema = json_content.get("schema", {})

        if schema:
            if "$ref" in schema:
                resolved = _resolve_ref(spec, schema["$ref"])
                if resolved:
                    # Extract individual properties from the referenced schema
                    properties = resolved.get("properties", {})
                    required_fields = set(resolved.get("required", []))
                    for prop_name, prop_schema in properties.items():
                        if prop_name in seen:
                            continue
                        seen.add(prop_name)
                        params.append(ParameterSpec(
                            name=prop_name,
                            type=_extract_schema_type(prop_schema, spec),
                            description=prop_schema.get("description", ""),
                            required=prop_name in required_fields,
                            default=str(prop_schema["default"]) if "default" in prop_schema else None,
                        ))
            elif schema.get("type") == "object" and "properties" in schema:
                properties = schema["properties"]
                required_fields = set(schema.get("required", []))
                for prop_name, prop_schema in properties.items():
                    if prop_name in seen:
                        continue
                    seen.add(prop_name)
                    params.append(ParameterSpec(
                        name=prop_name,
                        type=_extract_schema_type(prop_schema, spec),
                        description=prop_schema.get("description", ""),
                        required=prop_name in required_fields,
                        default=str(prop_schema["default"]) if "default" in prop_schema else None,
                    ))
            else:
                # Generic body param
                body_desc = request_body.get("description", "Request body")
                if "body" not in seen:
                    params.append(ParameterSpec(
                        name="body",
                        type="object",
                        description=body_desc,
                        required=request_body.get("required", True),
                    ))

    return params


def _operation_to_tool_name(method: str, path: str) -> str:
    """Generate a snake_case tool name from HTTP method + path."""
    path_parts = path.strip("/").split("/")
    # Remove common prefixes
    if path_parts and path_parts[0] in ("api", "v1", "v2", "v3"):
        path_parts = path_parts[1:]

    clean_parts = []
    for part in path_parts:
        if part.startswith("{") and part.endswith("}"):
            clean_parts.append(f"by_{part[1:-1]}")
        else:
            clean_parts.append(part)

    method_prefix = method.lower()
    path_name = "_".join(clean_parts) if clean_parts else "root"

    name = f"{method_prefix}_{path_name}"
    name = re.sub(r"[^a-z0-9_]", "_", name.lower())
    name = re.sub(r"_+", "_", name).strip("_")
    return name


def _extract_path_params(path: str) -> set[str]:
    """Extract parameter names from an OpenAPI path template."""
    return {m.group(1) for m in re.finditer(r"\{(\w+)\}", path)}


def find_openapi_specs(root: Path) -> list[Path]:
    """Find OpenAPI/Swagger spec files in a project directory."""
    specs: list[Path] = []
    root = root.resolve()

    for dir_name in SPEC_DIRS:
        search_dir = root / dir_name if dir_name else root
        if not search_dir.is_dir():
            continue
        for filename in OPENAPI_FILENAMES:
            spec_path = search_dir / filename
            if spec_path.is_file():
                specs.append(spec_path)

    # Recursive search for known OpenAPI filenames (up to 3 levels deep)
    found_set = set(specs)
    for pattern in ("openapi.json", "openapi.yaml", "openapi.yml",
                     "swagger.json", "swagger.yaml", "swagger.yml"):
        for path in root.rglob(pattern):
            if path not in found_set and path.is_file():
                # Skip node_modules, .git, etc.
                parts = path.relative_to(root).parts
                if any(p.startswith(".") or p == "node_modules" for p in parts):
                    continue
                specs.append(path)
                found_set.add(path)

    # Also check any JSON/YAML in root for OpenAPI markers
    for ext in (".json", ".yaml", ".yml"):
        for path in root.glob(f"*{ext}"):
            if path in found_set:
                continue
            if path.stat().st_size > 1_000_000:  # Skip files > 1MB
                continue
            try:
                text = path.read_text(errors="replace")
                if '"openapi"' in text or '"swagger"' in text or "openapi:" in text or "swagger:" in text:
                    specs.append(path)
                    found_set.add(path)
            except OSError:
                continue

    return specs


def parse_openapi_spec(spec_path: Path) -> Optional[dict]:
    """Parse an OpenAPI spec file and return the spec dict."""
    try:
        text = spec_path.read_text(errors="replace")
    except OSError:
        return None

    is_yaml = spec_path.suffix in (".yaml", ".yml")
    data = _load_spec(text, is_yaml)

    if data and isinstance(data, dict) and _is_openapi_spec(data):
        return data
    return None


def openapi_to_capabilities(
    spec: dict,
    spec_path: str = "",
) -> list[Capability]:
    """Convert an OpenAPI spec into Capability objects."""
    capabilities: list[Capability] = []
    seen: set[str] = set()

    paths = spec.get("paths", {})

    # Swagger 2.x: basePath
    base_path = spec.get("basePath", "").rstrip("/")

    # Collect path-level parameters (shared by all operations on the path)
    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue

        path_level_params = path_item.get("parameters", [])
        full_path = base_path + path if base_path else path

        for method in _HTTP_METHODS:
            operation = path_item.get(method)
            if not operation or not isinstance(operation, dict):
                continue

            # Merge path-level + operation-level parameters
            merged_operation = dict(operation)
            if path_level_params:
                op_params = list(operation.get("parameters", []))
                op_param_names = {
                    p.get("name") for p in op_params if isinstance(p, dict)
                }
                for pp in path_level_params:
                    if isinstance(pp, dict) and pp.get("name") not in op_param_names:
                        op_params.append(pp)
                merged_operation["parameters"] = op_params

            # Generate tool name
            tool_name = _operation_to_tool_name(method, full_path)
            # Use operationId if available and cleaner
            operation_id = operation.get("operationId", "")
            if operation_id:
                clean_id = re.sub(r"[^a-z0-9_]", "_", operation_id.lower())
                clean_id = re.sub(r"_+", "_", clean_id).strip("_")
                if clean_id and len(clean_id) < 50:
                    tool_name = clean_id

            if tool_name in seen:
                # Disambiguate
                tool_name = _operation_to_tool_name(method, full_path)
            if tool_name in seen:
                continue
            seen.add(tool_name)

            # Description
            description = operation.get("summary", "") or operation.get("description", "")
            if not description:
                description = f"{method.upper()} {full_path}"
            # Prepend HTTP info for design phase
            desc_with_method = f"{method.upper()} {full_path} - {description}"

            # Extract parameters
            path_params = _extract_path_params(full_path)
            params = _extract_parameters(merged_operation, path_params, spec)

            # Handle Swagger 2.x body parameters
            if "requestBody" not in operation:
                body_params = [
                    p for p in merged_operation.get("parameters", [])
                    if isinstance(p, dict) and p.get("in") == "body"
                ]
                for bp in body_params:
                    schema = bp.get("schema", {})
                    if "$ref" in schema:
                        resolved = _resolve_ref(spec, schema["$ref"])
                        if resolved and "properties" in resolved:
                            required_fields = set(resolved.get("required", []))
                            for prop_name, prop_schema in resolved["properties"].items():
                                params.append(ParameterSpec(
                                    name=prop_name,
                                    type=_extract_schema_type(prop_schema, spec),
                                    description=prop_schema.get("description", ""),
                                    required=prop_name in required_fields,
                                ))

            capabilities.append(Capability(
                name=tool_name,
                description=desc_with_method,
                category="api",
                parameters=params,
                return_type="object",
                source_file=spec_path,
                source_function=operation_id or f"{method}_{full_path}",
                ipc_type=IPCType.PROTOCOL,
            ))

    return capabilities


def extract_security_schemes(spec: dict) -> list[dict[str, str]]:
    """Extract security scheme info from an OpenAPI spec.

    Returns a list of dicts with keys: type, scheme, name, location.
    """
    schemes = []

    # OpenAPI 3.x: components.securitySchemes
    security_schemes = spec.get("components", {}).get("securitySchemes", {})
    # Swagger 2.x: securityDefinitions
    if not security_schemes:
        security_schemes = spec.get("securityDefinitions", {})

    for scheme_name, scheme in security_schemes.items():
        if not isinstance(scheme, dict):
            continue
        entry: dict[str, str] = {"name": scheme_name}
        scheme_type = scheme.get("type", "")

        if scheme_type == "apiKey":
            entry["type"] = "api_key"
            entry["header"] = scheme.get("name", "")
            entry["location"] = scheme.get("in", "header")  # "header" or "query"
        elif scheme_type == "http":
            http_scheme = scheme.get("scheme", "").lower()
            if http_scheme == "bearer":
                entry["type"] = "bearer"
            elif http_scheme == "basic":
                entry["type"] = "basic"
            else:
                entry["type"] = http_scheme
        elif scheme_type == "oauth2":
            entry["type"] = "bearer"  # OAuth2 tokens are sent as Bearer
        else:
            continue

        schemes.append(entry)

    return schemes


def extract_server_info(spec: dict) -> dict[str, str]:
    """Extract server host/port info from an OpenAPI spec."""
    info: dict[str, str] = {"protocol": "http"}

    # OpenAPI 3.x servers
    servers = spec.get("servers", [])
    if servers and isinstance(servers[0], dict):
        url = servers[0].get("url", "")
        if url:
            info["base_url"] = url
            # Extract port
            port_match = re.search(r":(\d+)", url)
            if port_match:
                info["port"] = port_match.group(1)

    # Swagger 2.x
    host = spec.get("host", "")
    if host:
        info["base_url"] = f"http://{host}"
        if ":" in host:
            info["port"] = host.split(":")[1]

    base_path = spec.get("basePath", "")
    if base_path and "base_url" in info:
        info["base_url"] = info["base_url"].rstrip("/") + base_path

    return info
