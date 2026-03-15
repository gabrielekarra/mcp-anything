"""Detect Express.js patterns in JavaScript/TypeScript source files."""

import re
from pathlib import Path

from mcp_anything.models.analysis import FileInfo, IPCMechanism, IPCType, Language

from .base import Detector

EXPRESS_PATTERNS = [
    (r"require\s*\(\s*['\"]express['\"]\s*\)", "Express require", 0.95),
    (r"from\s+['\"]express['\"]", "Express import", 0.95),
    (r"express\s*\(\s*\)", "Express app creation", 0.9),
    (r"\.(get|post|put|delete|patch)\s*\(\s*['\"/]", "Express route", 0.9),
    (r"Router\s*\(\s*\)", "Express Router", 0.85),
    (r"\.listen\s*\(\s*", "Express listen", 0.8),
    (r"app\.use\s*\(", "Express middleware", 0.7),
]


class ExpressDetector(Detector):
    @property
    def name(self) -> str:
        return "Express.js Detector"

    def detect(self, root: Path, files: list[FileInfo]) -> list[IPCMechanism]:
        evidence: list[str] = []
        max_confidence = 0.0
        port = "3000"

        for fi in files:
            if fi.language not in (Language.JAVASCRIPT, Language.TYPESCRIPT):
                continue
            content = self._read_file(root, fi)
            if not content:
                continue

            for pattern, desc, conf in EXPRESS_PATTERNS:
                if re.search(pattern, content):
                    evidence.append(f"{fi.path}: {desc}")
                    max_confidence = max(max_confidence, conf)

            # Extract port
            port_match = re.search(r"\.listen\s*\(\s*(\d+)", content)
            if port_match:
                port = port_match.group(1)
            port_env = re.search(r"PORT\s*\|\|\s*(\d+)", content)
            if port_env:
                port = port_env.group(1)

        # Also check package.json for express dependency
        pkg_json = root / "package.json"
        if pkg_json.exists():
            try:
                content = pkg_json.read_text(errors="replace")
                if '"express"' in content:
                    evidence.append("package.json: express dependency")
                    max_confidence = max(max_confidence, 0.95)
            except OSError:
                pass

        if not evidence:
            return []

        has_routes = any("route" in e.lower() for e in evidence)
        has_express = any("Express" in e for e in evidence)
        if not has_routes and not has_express:
            return []

        return [
            IPCMechanism(
                ipc_type=IPCType.PROTOCOL,
                confidence=min(max_confidence, 1.0),
                evidence=evidence,
                details={"protocol": "http", "port": port, "framework": "express"},
            )
        ]
