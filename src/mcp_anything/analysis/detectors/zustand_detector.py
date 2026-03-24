"""Detect Zustand state management stores in TypeScript/JavaScript source files."""

import re
from pathlib import Path

from mcp_anything.models.analysis import FileInfo, IPCMechanism, IPCType, Language

from .base import Detector

_ZUSTAND_IMPORT_RE = re.compile(r"""from\s+['"]zustand['"]""")
_ZUSTAND_REQUIRE_RE = re.compile(r"""require\s*\(\s*['"]zustand['"]\s*\)""")
_ZUSTAND_CREATE_RE = re.compile(r"""\bcreate\s*<\w+>\s*\(\s*\)""")

_DEFAULT_BRIDGE_PORT = "9001"


class ZustandDetector(Detector):
    @property
    def name(self) -> str:
        return "Zustand Detector"

    def detect(self, root: Path, files: list[FileInfo]) -> list[IPCMechanism]:
        evidence: list[str] = []
        max_confidence = 0.0

        for fi in files:
            if fi.language not in (Language.TYPESCRIPT, Language.JAVASCRIPT):
                continue
            content = self._read_file(root, fi)
            if not content:
                continue

            if _ZUSTAND_IMPORT_RE.search(content) or _ZUSTAND_REQUIRE_RE.search(content):
                evidence.append(f"{fi.path}: zustand import")
                max_confidence = max(max_confidence, 0.90)

            if _ZUSTAND_CREATE_RE.search(content):
                evidence.append(f"{fi.path}: zustand store creation (create<State>()())")
                max_confidence = max(max_confidence, 0.95)

        # Also check package.json for zustand dependency
        pkg_json = root / "package.json"
        if pkg_json.exists():
            try:
                content = pkg_json.read_text(errors="replace")
                if '"zustand"' in content:
                    evidence.append("package.json: zustand dependency")
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
                details={
                    "protocol": "zustand",
                    "framework": "zustand",
                    "port": _DEFAULT_BRIDGE_PORT,
                },
            )
        ]
