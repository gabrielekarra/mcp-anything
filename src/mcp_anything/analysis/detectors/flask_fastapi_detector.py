"""Detect Flask and FastAPI HTTP framework patterns."""

import re
from pathlib import Path

from mcp_anything.models.analysis import FileInfo, IPCMechanism, IPCType

from .base import Detector

FLASK_PATTERNS = [
    (r"from\s+flask\s+import|import\s+flask", "Flask import", 0.9),
    (r"Flask\s*\(", "Flask app creation", 0.95),
    (r"@\w+\.route\s*\(", "Flask route decorator", 0.9),
    (r"Blueprint\s*\(", "Flask Blueprint", 0.85),
    (r"request\.args|request\.form|request\.json", "Flask request access", 0.8),
]

FASTAPI_PATTERNS = [
    (r"from\s+fastapi\s+import|import\s+fastapi", "FastAPI import", 0.9),
    (r"FastAPI\s*\(", "FastAPI app creation", 0.95),
    (r"APIRouter\s*\(", "FastAPI APIRouter", 0.9),
    (r"@\w+\.(get|post|put|delete|patch)\s*\(", "FastAPI route decorator", 0.9),
    (r"from\s+fastapi\s+import.*(?:Query|Path|Body|Depends)", "FastAPI param injection", 0.85),
    (r"from\s+pydantic\s+import|import\s+pydantic", "Pydantic models", 0.7),
]

# Port extraction from uvicorn.run() or app.run()
_PORT_RE = re.compile(r'(?:uvicorn\.run|app\.run)\s*\([^)]*port\s*=\s*(\d+)')
_UVICORN_CLI_RE = re.compile(r'uvicorn.*--port\s+(\d+)')


class FlaskFastAPIDetector(Detector):
    @property
    def name(self) -> str:
        return "Flask/FastAPI Detector"

    def detect(self, root: Path, files: list[FileInfo]) -> list[IPCMechanism]:
        flask_evidence: list[str] = []
        fastapi_evidence: list[str] = []
        flask_confidence = 0.0
        fastapi_confidence = 0.0
        port = "8000"  # FastAPI default
        framework = ""

        for fi in files:
            content = self._read_file(root, fi)
            if not content:
                continue

            for pattern, desc, conf in FLASK_PATTERNS:
                if re.search(pattern, content):
                    flask_evidence.append(f"{fi.path}: {desc}")
                    flask_confidence = max(flask_confidence, conf)

            for pattern, desc, conf in FASTAPI_PATTERNS:
                if re.search(pattern, content):
                    fastapi_evidence.append(f"{fi.path}: {desc}")
                    fastapi_confidence = max(fastapi_confidence, conf)

            # Try to extract port
            port_match = _PORT_RE.search(content) or _UVICORN_CLI_RE.search(content)
            if port_match:
                port = port_match.group(1)

        # Determine which framework wins
        if fastapi_confidence >= flask_confidence and fastapi_evidence:
            framework = "fastapi"
            evidence = fastapi_evidence
            confidence = fastapi_confidence
        elif flask_evidence:
            framework = "flask"
            evidence = flask_evidence
            confidence = flask_confidence
            port = "5000"  # Flask default
        else:
            return []

        return [
            IPCMechanism(
                ipc_type=IPCType.PROTOCOL,
                confidence=min(confidence, 1.0),
                evidence=evidence,
                details={
                    "protocol": "http",
                    "port": port,
                    "framework": framework,
                },
            )
        ]
