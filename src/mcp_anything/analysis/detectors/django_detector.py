"""Detect Django REST Framework patterns in Python source files."""

import re
from pathlib import Path

from mcp_anything.models.analysis import FileInfo, IPCMechanism, IPCType, Language

from .base import Detector

DJANGO_PATTERNS = [
    (r"from\s+rest_framework", "DRF import", 0.95),
    (r"class\s+\w+\(.*ViewSet\)", "DRF ViewSet", 0.95),
    (r"class\s+\w+\(.*APIView\)", "DRF APIView", 0.9),
    (r"class\s+\w+\(.*ModelSerializer\)", "DRF ModelSerializer", 0.85),
    (r"class\s+\w+\(.*Serializer\)", "DRF Serializer", 0.8),
    (r"from\s+django", "Django import", 0.7),
    (r"urlpatterns\s*=", "Django URL patterns", 0.8),
    (r"DJANGO_SETTINGS_MODULE", "Django settings", 0.75),
    (r"@api_view", "DRF api_view decorator", 0.9),
    (r"router\.register", "DRF router registration", 0.9),
]


class DjangoDetector(Detector):
    @property
    def name(self) -> str:
        return "Django REST Framework Detector"

    def detect(self, root: Path, files: list[FileInfo]) -> list[IPCMechanism]:
        evidence: list[str] = []
        max_confidence = 0.0
        port = "8000"

        for fi in files:
            if fi.language != Language.PYTHON:
                continue
            content = self._read_file(root, fi)
            if not content:
                continue

            for pattern, desc, conf in DJANGO_PATTERNS:
                if re.search(pattern, content):
                    evidence.append(f"{fi.path}: {desc}")
                    max_confidence = max(max_confidence, conf)

        # Check for manage.py in root (not in SKIP_FILES for detection)
        manage_py = root / "manage.py"
        if manage_py.exists():
            evidence.append("manage.py: Django management script")
            max_confidence = max(max_confidence, 0.8)

        if not evidence:
            return []

        has_drf = any("DRF" in e or "api_view" in e.lower() for e in evidence)
        has_django = any("Django" in e for e in evidence)
        if not has_drf and not has_django:
            return []

        return [
            IPCMechanism(
                ipc_type=IPCType.PROTOCOL,
                confidence=min(max_confidence, 1.0),
                evidence=evidence,
                details={"protocol": "http", "port": port, "framework": "django-rest-framework"},
            )
        ]
