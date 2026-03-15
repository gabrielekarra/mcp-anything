"""Detect Ruby on Rails patterns in Ruby source files."""

import re
from pathlib import Path

from mcp_anything.models.analysis import FileInfo, IPCMechanism, IPCType, Language

from .base import Detector

RAILS_PATTERNS = [
    (r"Rails\.application", "Rails application", 0.95),
    (r"class\s+\w+\s*<\s*ApplicationController", "Rails controller", 0.9),
    (r"class\s+\w+\s*<\s*ActionController::Base", "Rails base controller", 0.9),
    (r"class\s+\w+\s*<\s*ActionController::API", "Rails API controller", 0.95),
    (r"resources?\s+:\w+", "Rails resources route", 0.85),
    (r"gem\s+['\"]rails['\"]", "Rails gem", 0.85),
    (r"class\s+\w+\s*<\s*ActiveRecord::Base", "ActiveRecord model", 0.8),
    (r"class\s+\w+\s*<\s*ApplicationRecord", "ApplicationRecord model", 0.8),
    (r"render\s+json:", "Rails JSON render", 0.85),
    (r"namespace\s+:api", "Rails API namespace", 0.9),
]


class RailsDetector(Detector):
    @property
    def name(self) -> str:
        return "Ruby on Rails Detector"

    def detect(self, root: Path, files: list[FileInfo]) -> list[IPCMechanism]:
        evidence: list[str] = []
        max_confidence = 0.0
        port = "3000"

        for fi in files:
            if fi.language != Language.RUBY:
                continue
            content = self._read_file(root, fi)
            if not content:
                continue

            for pattern, desc, conf in RAILS_PATTERNS:
                if re.search(pattern, content):
                    evidence.append(f"{fi.path}: {desc}")
                    max_confidence = max(max_confidence, conf)

        # Check for Gemfile
        gemfile = root / "Gemfile"
        if gemfile.exists():
            try:
                content = gemfile.read_text(errors="replace")
                if "rails" in content.lower():
                    evidence.append("Gemfile: Rails dependency")
                    max_confidence = max(max_confidence, 0.9)
            except OSError:
                pass

        # Check for config/routes.rb
        routes_rb = root / "config" / "routes.rb"
        if routes_rb.exists():
            evidence.append("config/routes.rb: Rails routes file")
            max_confidence = max(max_confidence, 0.9)

        if not evidence:
            return []

        has_controller = any("controller" in e.lower() for e in evidence)
        has_rails = any("Rails" in e or "routes" in e.lower() for e in evidence)
        if not has_controller and not has_rails:
            return []

        return [
            IPCMechanism(
                ipc_type=IPCType.PROTOCOL,
                confidence=min(max_confidence, 1.0),
                evidence=evidence,
                details={"protocol": "http", "port": port, "framework": "rails"},
            )
        ]
