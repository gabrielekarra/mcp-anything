"""Detect Spring Boot and Spring MVC patterns in Java source files."""

import re
from pathlib import Path

from mcp_anything.models.analysis import FileInfo, IPCMechanism, IPCType, Language

from .base import Detector

SPRING_PATTERNS = [
    # Core Spring Boot
    (r"@SpringBootApplication", "Spring Boot application", 0.95),
    (r"import\s+org\.springframework\.boot", "Spring Boot import", 0.9),
    # REST controllers
    (r"@RestController", "REST controller", 0.95),
    (r"@Controller", "Spring controller", 0.85),
    (r"@RequestMapping", "Request mapping", 0.9),
    (r"@GetMapping", "GET endpoint", 0.9),
    (r"@PostMapping", "POST endpoint", 0.9),
    (r"@PutMapping", "PUT endpoint", 0.9),
    (r"@DeleteMapping", "DELETE endpoint", 0.9),
    (r"@PatchMapping", "PATCH endpoint", 0.9),
    # Spring components
    (r"@Service", "Spring service", 0.7),
    (r"@Repository", "Spring repository", 0.7),
    (r"@Component", "Spring component", 0.7),
    (r"@Autowired", "Spring autowiring", 0.7),
    # Config
    (r"application\.(properties|yml|yaml)", "Spring config file", 0.8),
    (r"server\.port\s*=", "Server port config", 0.85),
]


class SpringDetector(Detector):
    @property
    def name(self) -> str:
        return "Spring Detector"

    def detect(self, root: Path, files: list[FileInfo]) -> list[IPCMechanism]:
        evidence: list[str] = []
        max_confidence = 0.0
        port = "8080"  # default
        has_boot = False

        for fi in files:
            if fi.language not in (Language.JAVA, Language.OTHER):
                continue
            content = self._read_file(root, fi)
            if not content:
                continue

            for pattern, desc, conf in SPRING_PATTERNS:
                if re.search(pattern, content):
                    evidence.append(f"{fi.path}: {desc}")
                    max_confidence = max(max_confidence, conf)
                    if "Spring Boot" in desc:
                        has_boot = True

            # Extract configured port
            port_match = re.search(r"server\.port\s*=\s*(\d+)", content)
            if port_match:
                port = port_match.group(1)

        # Also check for application.properties/yml in non-source files
        for config_name in ("application.properties", "application.yml", "application.yaml"):
            config_path = root / "src" / "main" / "resources" / config_name
            if config_path.exists():
                evidence.append(f"src/main/resources/{config_name}: Spring config file")
                max_confidence = max(max_confidence, 0.8)
                try:
                    config_content = config_path.read_text(errors="replace")
                    port_match = re.search(r"server\.port\s*[=:]\s*(\d+)", config_content)
                    if port_match:
                        port = port_match.group(1)
                except OSError:
                    pass

        if not evidence:
            return []

        # Need at least a controller or SpringBootApplication to be confident
        has_rest = any("controller" in e.lower() or "endpoint" in e.lower() for e in evidence)
        if not has_rest and not has_boot:
            return []

        # Distinguish Spring Boot from plain Spring MVC
        framework = "spring-boot" if has_boot else "spring-mvc"

        return [
            IPCMechanism(
                ipc_type=IPCType.PROTOCOL,
                confidence=min(max_confidence, 1.0),
                evidence=evidence,
                details={"protocol": "http", "port": port, "framework": framework},
            )
        ]
