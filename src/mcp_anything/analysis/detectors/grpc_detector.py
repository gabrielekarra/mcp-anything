"""Detect gRPC / Protocol Buffers patterns across multiple languages."""

import re
from pathlib import Path

from mcp_anything.analysis.detectors.base import Detector
from mcp_anything.models.analysis import FileInfo, IPCMechanism, IPCType, Language

# (language filter or None, regex, description, confidence)
GRPC_PATTERNS: list[tuple[Language | None, str, str, float]] = [
    # .proto files containing a service definition
    (Language.PROTOBUF, r"service\s+\w+\s*\{", "protobuf service definition", 0.95),
    # Python
    (Language.PYTHON, r"import\s+grpc", "Python gRPC import", 0.9),
    (Language.PYTHON, r"from\s+grpc\s+import", "Python gRPC from-import", 0.9),
    # JavaScript / TypeScript
    (Language.JAVASCRIPT, r"require\(['\"]@grpc/grpc-js['\"]\)", "Node.js gRPC require", 0.9),
    (Language.TYPESCRIPT, r"from\s+['\"]@grpc/grpc-js['\"]", "TypeScript gRPC import", 0.9),
    # Go
    (Language.GO, r"google\.golang\.org/grpc", "Go gRPC import", 0.9),
    # Rust
    (Language.RUST, r"tonic::", "Rust tonic gRPC usage", 0.9),
    (Language.RUST, r"tonic::transport", "Rust tonic transport", 0.9),
]

_PORT_PATTERN = re.compile(
    r"(?:serve|listen|bind|add_insecure_port)\s*\(\s*['\"]"
    r"(?:0\.0\.0\.0|127\.0\.0\.1|localhost|\[::\])?:(\d+)['\"]"
)


class GRPCDetector(Detector):
    """Detect gRPC usage via .proto service definitions and language-specific imports."""

    @property
    def name(self) -> str:
        return "gRPC Detector"

    def detect(self, root: Path, files: list[FileInfo]) -> list[IPCMechanism]:
        evidence: list[str] = []
        max_confidence = 0.0
        details: dict[str, str] = {"protocol": "grpc"}

        for fi in files:
            content = self._read_file(root, fi)
            if not content:
                continue

            for lang_filter, pattern, desc, conf in GRPC_PATTERNS:
                # Skip if pattern is language-specific and file doesn't match
                if lang_filter is not None and fi.language != lang_filter:
                    continue

                if re.search(pattern, content):
                    evidence.append(f"{fi.path}: {desc}")
                    max_confidence = max(max_confidence, conf)

            # Try to extract a port number
            port_match = _PORT_PATTERN.search(content)
            if port_match:
                details["port"] = port_match.group(1)

        if not evidence:
            return []

        return [
            IPCMechanism(
                ipc_type=IPCType.PROTOCOL,
                confidence=min(max_confidence, 1.0),
                evidence=evidence,
                details=details,
            )
        ]
