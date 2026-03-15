"""Detect Go web framework patterns (net/http, Gin, Echo) in Go source files."""

import re
from pathlib import Path

from mcp_anything.models.analysis import FileInfo, IPCMechanism, IPCType, Language

from .base import Detector

GO_WEB_PATTERNS = [
    # Standard library
    (r'"net/http"', "Go net/http", 0.85),
    (r"http\.HandleFunc\s*\(", "Go HandleFunc", 0.9),
    (r"http\.Handle\s*\(", "Go Handle", 0.85),
    (r"http\.ListenAndServe", "Go ListenAndServe", 0.9),
    # Gin
    (r'"github\.com/gin-gonic/gin"', "Gin import", 0.95),
    (r"gin\.Default\s*\(\)", "Gin Default", 0.9),
    (r"gin\.New\s*\(\)", "Gin New", 0.9),
    # Echo
    (r'"github\.com/labstack/echo', "Echo import", 0.95),
    (r"echo\.New\s*\(\)", "Echo New", 0.9),
    # Chi
    (r'"github\.com/go-chi/chi', "Chi import", 0.95),
    (r"chi\.NewRouter\s*\(\)", "Chi router", 0.9),
    # Fiber
    (r'"github\.com/gofiber/fiber', "Fiber import", 0.95),
    # gorilla/mux
    (r'"github\.com/gorilla/mux"', "gorilla/mux import", 0.9),
    (r"mux\.NewRouter\s*\(\)", "gorilla/mux router", 0.9),
]


class GoWebDetector(Detector):
    @property
    def name(self) -> str:
        return "Go Web Framework Detector"

    def detect(self, root: Path, files: list[FileInfo]) -> list[IPCMechanism]:
        evidence: list[str] = []
        max_confidence = 0.0
        port = "8080"
        framework = "net/http"

        for fi in files:
            if fi.language != Language.GO:
                continue
            content = self._read_file(root, fi)
            if not content:
                continue

            for pattern, desc, conf in GO_WEB_PATTERNS:
                if re.search(pattern, content):
                    evidence.append(f"{fi.path}: {desc}")
                    max_confidence = max(max_confidence, conf)
                    # Detect specific framework
                    if "Gin" in desc:
                        framework = "gin"
                    elif "Echo" in desc:
                        framework = "echo"
                    elif "Chi" in desc:
                        framework = "chi"
                    elif "Fiber" in desc:
                        framework = "fiber"
                    elif "gorilla" in desc:
                        framework = "gorilla/mux"

            # Extract port
            port_match = re.search(r'ListenAndServe\s*\(\s*["\']:?(\d+)', content)
            if port_match:
                port = port_match.group(1)
            port_match2 = re.search(r'\.Run\s*\(\s*["\']:?(\d+)', content)
            if port_match2:
                port = port_match2.group(1)
            port_match3 = re.search(r'\.Start\s*\(\s*["\']:?(\d+)', content)
            if port_match3:
                port = port_match3.group(1)

        # Check go.mod for framework dependencies
        go_mod = root / "go.mod"
        if go_mod.exists():
            try:
                content = go_mod.read_text(errors="replace")
                if "gin-gonic/gin" in content:
                    evidence.append("go.mod: Gin dependency")
                    framework = "gin"
                    max_confidence = max(max_confidence, 0.95)
                elif "labstack/echo" in content:
                    evidence.append("go.mod: Echo dependency")
                    framework = "echo"
                    max_confidence = max(max_confidence, 0.95)
                elif "go-chi/chi" in content:
                    evidence.append("go.mod: Chi dependency")
                    framework = "chi"
                    max_confidence = max(max_confidence, 0.95)
            except OSError:
                pass

        if not evidence:
            return []

        has_routes = any(
            "HandleFunc" in e or "route" in e.lower() or "Handle" in e
            for e in evidence
        )
        has_framework = any(
            "import" in e.lower() or "dependency" in e.lower()
            for e in evidence
        )
        if not has_routes and not has_framework:
            return []

        return [
            IPCMechanism(
                ipc_type=IPCType.PROTOCOL,
                confidence=min(max_confidence, 1.0),
                evidence=evidence,
                details={"protocol": "http", "port": port, "framework": framework},
            )
        ]
