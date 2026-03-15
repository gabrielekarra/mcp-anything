"""Shared utilities for HTTP route analyzers across frameworks."""

import re
from mcp_anything.models.analysis import Capability, IPCType, ParameterSpec


def endpoint_to_tool_name(http_method: str, path: str, fallback_name: str = "") -> str:
    """Generate a snake_case tool name from HTTP method + path."""
    path_parts = path.strip("/").split("/")
    if path_parts and path_parts[0] in ("api", "v1", "v2", "v3"):
        path_parts = path_parts[1:]

    clean_parts = []
    for part in path_parts:
        # {id} or :id → by_id
        if part.startswith("{") and part.endswith("}"):
            clean_parts.append(f"by_{part[1:-1]}")
        elif part.startswith(":"):
            clean_parts.append(f"by_{part[1:]}")
        else:
            clean_parts.append(part)

    method_prefix = http_method.lower()
    path_name = "_".join(clean_parts) if clean_parts else fallback_name

    name = f"{method_prefix}_{path_name}"
    name = re.sub(r"[^a-z0-9_]", "_", name.lower())
    name = re.sub(r"_+", "_", name).strip("_")
    return name


def normalize_path(path: str) -> str:
    """Normalize path parameters to {param} style.

    Converts :param and <type:param> to {param}.
    """
    # Express/Gin/Echo style :param
    path = re.sub(r":(\w+)", r"{\1}", path)
    # Flask style <type:param> or <param>
    path = re.sub(r"<(?:\w+:)?(\w+)>", r"{\1}", path)
    return path


def make_description(name: str) -> str:
    """Generate a readable description from a function/method name."""
    words = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
    words = words.replace("_", " ").strip()
    return words[0].upper() + words[1:] if words else name


def endpoints_to_capabilities(
    endpoints: list[dict],
    source_file: str,
) -> list[Capability]:
    """Convert a list of endpoint dicts to Capability objects.

    Each endpoint dict should have: http_method, path, function_name,
    description, parameters (list[ParameterSpec]).
    """
    capabilities: list[Capability] = []
    seen: set[str] = set()

    for ep in endpoints:
        tool_name = endpoint_to_tool_name(
            ep["http_method"], ep["path"], ep.get("function_name", "")
        )
        if tool_name in seen:
            continue
        seen.add(tool_name)

        desc = f"{ep['http_method']} {ep['path']} - {ep.get('description', '')}"

        capabilities.append(Capability(
            name=tool_name,
            description=desc,
            category="api",
            parameters=ep.get("parameters", []),
            return_type="object",
            source_file=source_file,
            source_function=ep.get("function_name", ""),
            ipc_type=IPCType.PROTOCOL,
        ))

    return capabilities
