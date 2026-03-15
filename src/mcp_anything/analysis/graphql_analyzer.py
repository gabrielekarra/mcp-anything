"""Regex-based GraphQL schema analyzer."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from mcp_anything.models.analysis import (
    Capability,
    FileInfo,
    IPCType,
    Language,
    ParameterSpec,
)

# Map GraphQL scalar types to JSON-friendly type names.
_SCALAR_MAP: dict[str, str] = {
    "String": "string",
    "Int": "integer",
    "Float": "float",
    "Boolean": "boolean",
    "ID": "string",
}

_TYPE_RE = re.compile(
    r"type\s+(\w+)\s*(?:implements\s+[\w&\s]+)?\s*\{([^}]+)\}",
    re.MULTILINE,
)

_FIELD_RE = re.compile(
    r"(\w+)(?:\(([^)]*)\))?\s*:\s*([\w!\[\]]+)",
)

_ARG_RE = re.compile(
    r"(\w+)\s*:\s*([\w!\[\]]+)",
)


@dataclass
class GraphQLField:
    name: str
    type: str
    args: list[ParameterSpec] = field(default_factory=list)
    description: str = ""


@dataclass
class GraphQLAnalysisResult:
    queries: list[GraphQLField] = field(default_factory=list)
    mutations: list[GraphQLField] = field(default_factory=list)
    subscriptions: list[GraphQLField] = field(default_factory=list)
    types: dict[str, list[GraphQLField]] = field(default_factory=dict)


def _map_type(graphql_type: str) -> str:
    """Convert a GraphQL type string to a simple type name."""
    # Strip list brackets and non-null markers for mapping.
    base = graphql_type.replace("[", "").replace("]", "").replace("!", "")
    return _SCALAR_MAP.get(base, base.lower())


def _parse_args(args_str: str) -> list[ParameterSpec]:
    """Parse a GraphQL argument list string into ParameterSpec objects."""
    params: list[ParameterSpec] = []
    for match in _ARG_RE.finditer(args_str):
        arg_name = match.group(1)
        arg_type_raw = match.group(2)
        required = arg_type_raw.endswith("!")
        params.append(
            ParameterSpec(
                name=arg_name,
                type=_map_type(arg_type_raw),
                required=required,
            )
        )
    return params


def parse_graphql_sdl(source: str) -> GraphQLAnalysisResult:
    """Parse a GraphQL SDL schema string and return analysis results."""
    result = GraphQLAnalysisResult()

    for type_match in _TYPE_RE.finditer(source):
        type_name = type_match.group(1)
        body = type_match.group(2)

        fields: list[GraphQLField] = []
        for fm in _FIELD_RE.finditer(body):
            f_name = fm.group(1)
            f_args_str = fm.group(2) or ""
            f_type = fm.group(3)

            args = _parse_args(f_args_str) if f_args_str.strip() else []
            fields.append(
                GraphQLField(
                    name=f_name,
                    type=_map_type(f_type),
                    args=args,
                )
            )

        if type_name == "Query":
            result.queries = fields
        elif type_name == "Mutation":
            result.mutations = fields
        elif type_name == "Subscription":
            result.subscriptions = fields
        else:
            result.types[type_name] = fields

    return result


def analyze_graphql_file(
    root: Path, file_info: FileInfo
) -> Optional[GraphQLAnalysisResult]:
    """Analyze a single .graphql / .gql file and return results."""
    if file_info.language != Language.GRAPHQL:
        return None

    filepath = root / file_info.path
    try:
        source = filepath.read_text(errors="replace")
    except OSError:
        return None

    result = parse_graphql_sdl(source)

    # Only return a result if we found something meaningful.
    if not result.queries and not result.mutations and not result.subscriptions and not result.types:
        return None

    return result


def graphql_results_to_capabilities(
    results: dict[str, GraphQLAnalysisResult],
) -> list[Capability]:
    """Convert GraphQL analysis results (keyed by file path) to Capability objects."""
    capabilities: list[Capability] = []

    for source_file, result in results.items():
        for q in result.queries:
            capabilities.append(
                Capability(
                    name=q.name,
                    description=f"GraphQL query: {q.name}",
                    category="graphql_query",
                    parameters=list(q.args),
                    return_type=q.type,
                    source_file=source_file,
                    ipc_type=IPCType.PROTOCOL,
                )
            )

        for m in result.mutations:
            capabilities.append(
                Capability(
                    name=m.name,
                    description=f"GraphQL mutation: {m.name}",
                    category="graphql_mutation",
                    parameters=list(m.args),
                    return_type=m.type,
                    source_file=source_file,
                    ipc_type=IPCType.PROTOCOL,
                )
            )

        for s in result.subscriptions:
            capabilities.append(
                Capability(
                    name=s.name,
                    description=f"GraphQL subscription: {s.name}",
                    category="graphql_subscription",
                    parameters=list(s.args),
                    return_type=s.type,
                    source_file=source_file,
                    ipc_type=IPCType.PROTOCOL,
                )
            )

    return capabilities
