"""AST-based analyzer for Django REST Framework endpoints.

Extracts ViewSets, APIViews, and @api_view functions from DRF source files.
"""

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from mcp_anything.models.analysis import Capability, FileInfo, IPCType, Language, ParameterSpec
from mcp_anything.analysis.route_utils import endpoint_to_tool_name, make_description


# DRF ViewSet action → HTTP method mapping
_VIEWSET_ACTIONS = {
    "list": "GET",
    "create": "POST",
    "retrieve": "GET",
    "update": "PUT",
    "partial_update": "PATCH",
    "destroy": "DELETE",
}


@dataclass
class DjangoEndpoint:
    """A REST endpoint extracted from DRF source."""

    http_method: str
    path: str
    function_name: str
    description: str
    parameters: list[ParameterSpec]
    source_file: str
    view_class: str = ""


@dataclass
class DjangoAnalysisResult:
    """Result of analyzing Python files for DRF patterns."""

    endpoints: list[DjangoEndpoint] = field(default_factory=list)
    viewsets: list[str] = field(default_factory=list)
    serializers: list[str] = field(default_factory=list)
    has_drf: bool = False


def _extract_serializer_fields(tree: ast.Module) -> dict[str, list[str]]:
    """Extract field names from serializer Meta classes."""
    serializer_fields: dict[str, list[str]] = {}

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        # Check if it's a Serializer class
        is_serializer = any(
            (isinstance(base, ast.Name) and "Serializer" in base.id) or
            (isinstance(base, ast.Attribute) and "Serializer" in base.attr)
            for base in node.bases
        )
        if not is_serializer:
            continue

        # Find Meta class with fields
        for item in node.body:
            if isinstance(item, ast.ClassDef) and item.name == "Meta":
                for meta_item in item.body:
                    if isinstance(meta_item, ast.Assign):
                        for target in meta_item.targets:
                            if isinstance(target, ast.Name) and target.id == "fields":
                                if isinstance(meta_item.value, (ast.List, ast.Tuple)):
                                    fields = []
                                    for elt in meta_item.value.elts:
                                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                            fields.append(elt.value)
                                    serializer_fields[node.name] = fields

    return serializer_fields


def _extract_url_patterns(root: Path) -> dict[str, str]:
    """Parse urls.py to find router.register() patterns and path() entries.

    Returns mapping of ViewSet name → URL prefix.
    """
    patterns: dict[str, str] = {}

    # Search for urls.py files
    for urls_file in root.rglob("urls.py"):
        try:
            source = urls_file.read_text(errors="replace")
        except OSError:
            continue

        # router.register(r'prefix', ViewSetName)
        for match in re.finditer(
            r"router\.register\s*\(\s*r?['\"]([^'\"]+)['\"]\s*,\s*(\w+)",
            source,
        ):
            prefix = match.group(1).strip("/")
            viewset = match.group(2)
            patterns[viewset] = f"/{prefix}"

        # path('prefix/', ViewSetName.as_view({...}))
        for match in re.finditer(
            r"path\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*(\w+)\.as_view",
            source,
        ):
            prefix = match.group(1).strip("/")
            view = match.group(2)
            patterns[view] = f"/{prefix}"

    return patterns


def analyze_django_file(
    root: Path, file_info: FileInfo,
) -> Optional[DjangoAnalysisResult]:
    """Analyze a Python file for DRF endpoints."""
    if file_info.language != Language.PYTHON:
        return None

    try:
        source = (root / file_info.path).read_text(errors="replace")
        tree = ast.parse(source)
    except (OSError, SyntaxError):
        return None

    # Must have DRF reference
    has_drf = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and "rest_framework" in node.module:
                has_drf = True
                break

    if not has_drf:
        return None

    result = DjangoAnalysisResult(has_drf=True)

    # Extract serializer field info for parameter mapping
    serializer_fields = _extract_serializer_fields(tree)
    result.serializers = list(serializer_fields.keys())

    # Extract URL patterns for path mapping
    url_patterns = _extract_url_patterns(root)

    # Find ViewSet and APIView classes
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue

        base_names = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_names.append(base.id)
            elif isinstance(base, ast.Attribute):
                base_names.append(base.attr)

        is_viewset = any("ViewSet" in b for b in base_names)
        is_apiview = any("APIView" in b for b in base_names)

        if not is_viewset and not is_apiview:
            continue

        class_name = node.name
        base_path = url_patterns.get(class_name, f"/{class_name.lower().replace('viewset', '')}")

        if is_viewset:
            result.viewsets.append(class_name)

            # Find serializer_class for this viewset
            serializer_name = ""
            for item in node.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name) and target.id == "serializer_class":
                            if isinstance(item.value, ast.Name):
                                serializer_name = item.value.id

            fields = serializer_fields.get(serializer_name, [])

            # Generate standard ViewSet actions
            for method_node in node.body:
                if not isinstance(method_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue

                method_name = method_node.name

                if method_name in _VIEWSET_ACTIONS:
                    http_method = _VIEWSET_ACTIONS[method_name]
                    is_detail = method_name in ("retrieve", "update", "partial_update", "destroy")
                    path = f"{base_path}/{{id}}" if is_detail else base_path

                    params: list[ParameterSpec] = []
                    if is_detail:
                        params.append(ParameterSpec(name="id", type="integer", required=True))
                    if method_name in ("create", "update", "partial_update") and fields:
                        for f in fields:
                            if f != "id":
                                params.append(ParameterSpec(
                                    name=f, type="string",
                                    required=method_name != "partial_update",
                                ))

                    docstring = ast.get_docstring(method_node) or ""
                    desc = docstring.split("\n")[0] if docstring else make_description(method_name)

                    result.endpoints.append(DjangoEndpoint(
                        http_method=http_method,
                        path=path,
                        function_name=method_name,
                        description=desc,
                        parameters=params,
                        source_file=file_info.path,
                        view_class=class_name,
                    ))

                # Check for @action decorator (custom actions)
                for decorator in method_node.decorator_list:
                    if isinstance(decorator, ast.Call):
                        func = decorator.func
                        if (isinstance(func, ast.Name) and func.id == "action") or \
                           (isinstance(func, ast.Attribute) and func.attr == "action"):
                            # Extract detail and methods
                            detail = False
                            methods = ["GET"]
                            for kw in decorator.keywords:
                                if kw.arg == "detail" and isinstance(kw.value, ast.Constant):
                                    detail = kw.value.value
                                elif kw.arg == "methods" and isinstance(kw.value, ast.List):
                                    methods = [
                                        elt.value.upper()
                                        for elt in kw.value.elts
                                        if isinstance(elt, ast.Constant)
                                    ]

                            for m in methods:
                                path = f"{base_path}/{{id}}/{method_name}" if detail else f"{base_path}/{method_name}"
                                params = []
                                if detail:
                                    params.append(ParameterSpec(name="id", type="integer", required=True))

                                docstring = ast.get_docstring(method_node) or ""
                                desc = docstring.split("\n")[0] if docstring else make_description(method_name)

                                result.endpoints.append(DjangoEndpoint(
                                    http_method=m,
                                    path=path,
                                    function_name=method_name,
                                    description=desc,
                                    parameters=params,
                                    source_file=file_info.path,
                                    view_class=class_name,
                                ))

        elif is_apiview:
            # APIView — look for get(), post(), put(), delete() methods
            for method_node in node.body:
                if not isinstance(method_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                method_name = method_node.name
                if method_name in ("get", "post", "put", "delete", "patch"):
                    http_method = method_name.upper()
                    path = url_patterns.get(class_name, f"/{class_name.lower().replace('view', '')}")

                    docstring = ast.get_docstring(method_node) or ""
                    desc = docstring.split("\n")[0] if docstring else make_description(f"{method_name} {class_name}")

                    result.endpoints.append(DjangoEndpoint(
                        http_method=http_method,
                        path=path,
                        function_name=method_name,
                        description=desc,
                        parameters=[],
                        source_file=file_info.path,
                        view_class=class_name,
                    ))

    return result if (result.endpoints or result.has_drf) else None


def django_results_to_capabilities(
    results: dict[str, DjangoAnalysisResult],
) -> list[Capability]:
    """Convert DRF analysis results into Capability objects."""
    capabilities: list[Capability] = []
    seen: set[str] = set()

    for file_path, result in results.items():
        for ep in result.endpoints:
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
