"""Detect Rust web framework patterns (Actix, Axum, Rocket, Warp) in Rust source files."""

import re
from pathlib import Path

from mcp_anything.models.analysis import FileInfo, IPCMechanism, IPCType, Language

from .base import Detector

RUST_WEB_PATTERNS = [
    # Actix
    (r"actix_web", "Actix-web", 0.95),
    (r"#\[(?:get|post|put|delete|patch)\s*\(", "Actix route macro", 0.95),
    (r"HttpServer::new", "Actix HttpServer", 0.9),
    (r"web::(?:get|post|put|delete|patch|resource)\s*\(\)", "Actix web method", 0.9),
    # Axum
    (r"axum::", "Axum import", 0.95),
    (r"Router::new\s*\(\)", "Axum Router", 0.9),
    (r"\.route\s*\(\s*\"[^\"]+\"", "Axum route", 0.9),
    (r"\.nest\s*\(\s*\"[^\"]+\"", "Axum nest", 0.85),
    # Rocket
    (r"#\[rocket::(?:get|post|put|delete)", "Rocket route", 0.95),
    (r"rocket::build\(\)", "Rocket build", 0.9),
    # Warp
    (r"warp::(?:get|post|put|delete|path)", "Warp filter", 0.9),
]


class RustWebDetector(Detector):
    @property
    def name(self) -> str:
        return "Rust Web Framework Detector"

    def detect(self, root: Path, files: list[FileInfo]) -> list[IPCMechanism]:
        evidence: list[str] = []
        max_confidence = 0.0
        port = "8080"
        framework = "actix"

        for fi in files:
            if fi.language != Language.RUST:
                continue
            content = self._read_file(root, fi)
            if not content:
                continue

            for pattern, desc, conf in RUST_WEB_PATTERNS:
                if re.search(pattern, content):
                    evidence.append(f"{fi.path}: {desc}")
                    max_confidence = max(max_confidence, conf)
                    if "Axum" in desc:
                        framework = "axum"
                    elif "Rocket" in desc:
                        framework = "rocket"
                    elif "Warp" in desc:
                        framework = "warp"

            # Extract port
            port_match = re.search(r'bind\s*\(\s*["\'][\w.]*:(\d+)', content)
            if port_match:
                port = port_match.group(1)

        # Check Cargo.toml
        cargo_toml = root / "Cargo.toml"
        if cargo_toml.exists():
            try:
                content = cargo_toml.read_text(errors="replace")
                if "actix-web" in content:
                    evidence.append("Cargo.toml: actix-web dependency")
                    framework = "actix"
                    max_confidence = max(max_confidence, 0.95)
                elif "axum" in content:
                    evidence.append("Cargo.toml: axum dependency")
                    framework = "axum"
                    max_confidence = max(max_confidence, 0.95)
                elif "rocket" in content:
                    evidence.append("Cargo.toml: rocket dependency")
                    framework = "rocket"
                    max_confidence = max(max_confidence, 0.95)
            except OSError:
                pass

        if not evidence:
            return []

        return [
            IPCMechanism(
                ipc_type=IPCType.PROTOCOL,
                confidence=min(max_confidence, 1.0),
                evidence=evidence,
                details={"protocol": "http", "port": port, "framework": framework},
            )
        ]
