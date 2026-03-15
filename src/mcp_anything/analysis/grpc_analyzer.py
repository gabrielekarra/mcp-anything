"""Regex-based .proto file parser and gRPC capability extractor."""

from __future__ import annotations

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

# ── Proto-to-JSON-Schema type mapping ────────────────────────────────────────

PROTO_TYPE_MAP: dict[str, str] = {
    "string": "string",
    "int32": "integer",
    "int64": "integer",
    "uint32": "integer",
    "uint64": "integer",
    "sint32": "integer",
    "sint64": "integer",
    "float": "float",
    "double": "float",
    "bool": "boolean",
    "bytes": "string",
}

# ── Dataclasses ──────────────────────────────────────────────────────────────


@dataclass
class ProtoField:
    name: str
    type: str
    number: int
    repeated: bool = False


@dataclass
class ProtoMessage:
    name: str
    fields: list[ProtoField] = field(default_factory=list)


@dataclass
class ProtoRPCMethod:
    name: str
    request_type: str
    response_type: str
    client_streaming: bool = False
    server_streaming: bool = False


@dataclass
class ProtoService:
    name: str
    methods: list[ProtoRPCMethod] = field(default_factory=list)


@dataclass
class GRPCAnalysisResult:
    services: list[ProtoService] = field(default_factory=list)
    messages: dict[str, ProtoMessage] = field(default_factory=dict)
    package: str = ""


# ── Parsing helpers ──────────────────────────────────────────────────────────

_PACKAGE_RE = re.compile(r"package\s+([\w.]+)\s*;")
_MESSAGE_RE = re.compile(r"message\s+(\w+)\s*\{([^}]+)\}")
_FIELD_RE = re.compile(
    r"(?:repeated\s+|optional\s+|required\s+)?([\w.]+)\s+(\w+)\s*=\s*(\d+)"
)
_RPC_RE = re.compile(
    r"rpc\s+(\w+)\s*\(\s*(stream\s+)?(\w+)\s*\)\s*returns\s*\(\s*(stream\s+)?(\w+)\s*\)"
)

_REPEATED_PREFIX_RE = re.compile(r"^repeated\s+")


def _find_service_blocks(source: str) -> list[tuple[str, str]]:
    """Return (service_name, service_body) pairs, handling nested braces."""
    results: list[tuple[str, str]] = []
    for m in re.finditer(r"service\s+(\w+)\s*\{", source):
        name = m.group(1)
        start = m.end()
        depth = 1
        pos = start
        while pos < len(source) and depth > 0:
            if source[pos] == "{":
                depth += 1
            elif source[pos] == "}":
                depth -= 1
            pos += 1
        body = source[start : pos - 1]
        results.append((name, body))
    return results


def parse_proto_file(source: str) -> GRPCAnalysisResult:
    """Parse a .proto file and return structured analysis data."""
    result = GRPCAnalysisResult()

    # Package
    pkg_match = _PACKAGE_RE.search(source)
    if pkg_match:
        result.package = pkg_match.group(1)

    # Messages
    for msg_match in _MESSAGE_RE.finditer(source):
        msg_name = msg_match.group(1)
        body = msg_match.group(2)
        fields: list[ProtoField] = []
        for fld_match in _FIELD_RE.finditer(body):
            ftype = fld_match.group(1)
            fname = fld_match.group(2)
            fnum = int(fld_match.group(3))
            # Check if the original line had 'repeated'
            line_start = body.rfind("\n", 0, fld_match.start()) + 1
            line_text = body[line_start : fld_match.end()]
            repeated = bool(_REPEATED_PREFIX_RE.search(line_text))
            fields.append(ProtoField(name=fname, type=ftype, number=fnum, repeated=repeated))
        result.messages[msg_name] = ProtoMessage(name=msg_name, fields=fields)

    # Services
    for svc_name, svc_body in _find_service_blocks(source):
        methods: list[ProtoRPCMethod] = []
        for rpc_match in _RPC_RE.finditer(svc_body):
            methods.append(
                ProtoRPCMethod(
                    name=rpc_match.group(1),
                    request_type=rpc_match.group(3),
                    response_type=rpc_match.group(5),
                    client_streaming=rpc_match.group(2) is not None,
                    server_streaming=rpc_match.group(4) is not None,
                )
            )
        result.services.append(ProtoService(name=svc_name, methods=methods))

    return result


def analyze_proto_file(root: Path, file_info: FileInfo) -> Optional[GRPCAnalysisResult]:
    """Analyze a single .proto FileInfo and return parsed results."""
    if file_info.language != Language.PROTOBUF:
        return None
    try:
        source = (root / file_info.path).read_text(errors="replace")
    except OSError:
        return None
    return parse_proto_file(source)


# ── Capability extraction ────────────────────────────────────────────────────


def grpc_results_to_capabilities(
    results: dict[str, GRPCAnalysisResult],
) -> list[Capability]:
    """Convert parsed gRPC analysis results into a list of Capability objects.

    *results* maps proto file paths to their ``GRPCAnalysisResult``.
    Each RPC method becomes one ``Capability``.
    """
    capabilities: list[Capability] = []

    for proto_path, analysis in results.items():
        for service in analysis.services:
            for method in service.methods:
                # Build parameter specs from the request message fields
                params: list[ParameterSpec] = []
                req_msg = analysis.messages.get(method.request_type)
                if req_msg:
                    for fld in req_msg.fields:
                        mapped_type = PROTO_TYPE_MAP.get(fld.type, "string")
                        params.append(
                            ParameterSpec(
                                name=fld.name,
                                type=mapped_type,
                                description=f"{fld.type} field",
                                required=True,
                            )
                        )

                # Description
                parts = [f"gRPC {service.name}.{method.name}"]
                if method.client_streaming:
                    parts.append("(client streaming)")
                if method.server_streaming:
                    parts.append("(server streaming)")
                description = " ".join(parts)

                capabilities.append(
                    Capability(
                        name=f"{service.name}.{method.name}",
                        description=description,
                        category="grpc",
                        parameters=params,
                        return_type=method.response_type,
                        source_file=proto_path,
                        source_function=method.name,
                        ipc_type=IPCType.PROTOCOL,
                    )
                )

    return capabilities
