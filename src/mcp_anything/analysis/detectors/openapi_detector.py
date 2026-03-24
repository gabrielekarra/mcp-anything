"""Detect OpenAPI/Swagger specification files."""

from pathlib import Path

from mcp_anything.analysis.openapi_analyzer import (
    find_openapi_specs,
    parse_openapi_spec,
    extract_server_info,
    extract_security_schemes,
)
from mcp_anything.models.analysis import FileInfo, IPCMechanism, IPCType

from .base import Detector


class OpenAPIDetector(Detector):
    @property
    def name(self) -> str:
        return "OpenAPI/Swagger Detector"

    def detect(self, root: Path, files: list[FileInfo]) -> list[IPCMechanism]:
        specs = find_openapi_specs(root)
        if not specs:
            return []

        evidence: list[str] = []
        details: dict[str, str] = {"protocol": "http"}
        endpoint_count = 0

        for spec_path in specs:
            spec = parse_openapi_spec(spec_path)
            if not spec:
                continue

            rel_path = str(spec_path.relative_to(root.resolve()))

            # Count endpoints
            paths = spec.get("paths", {})
            n_endpoints = sum(
                1 for p in paths.values() if isinstance(p, dict)
                for method in ("get", "post", "put", "delete", "patch")
                if method in p
            )
            endpoint_count += n_endpoints

            # Version info
            version = spec.get("openapi", spec.get("swagger", "unknown"))
            title = spec.get("info", {}).get("title", "")

            evidence.append(
                f"{rel_path}: OpenAPI {version} spec"
                + (f" ({title})" if title else "")
                + f" with {n_endpoints} endpoints"
            )

            # Extract server info
            server_info = extract_server_info(spec)
            details.update(server_info)
            details["framework"] = "openapi"
            details["spec_file"] = rel_path

            # Extract auth scheme so it survives manifest serialization (needed for --resume
            # and for design phase when spec file may no longer be accessible)
            if "auth_type" not in details:
                schemes = extract_security_schemes(spec)
                if schemes:
                    scheme = schemes[0]
                    auth_type = scheme.get("type", "")
                    if auth_type:
                        details["auth_type"] = auth_type
                        if auth_type == "api_key":
                            details["auth_header"] = scheme.get("header", "")
                            details["auth_location"] = scheme.get("location", "header")

        if not evidence:
            return []

        # Higher confidence with more endpoints
        confidence = min(0.95, 0.85 + endpoint_count * 0.01)

        return [
            IPCMechanism(
                ipc_type=IPCType.PROTOCOL,
                confidence=confidence,
                evidence=evidence,
                details=details,
            )
        ]
