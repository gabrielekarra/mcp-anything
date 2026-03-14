"""Detect protocol patterns (WebSocket, OSC, D-Bus, gRPC, etc.)."""

import re
from pathlib import Path

from mcp_anything.models.analysis import FileInfo, IPCMechanism, IPCType

from .base import Detector

PROTOCOL_PATTERNS = [
    (r"websockets?\.", "WebSocket usage", 0.85),
    (r"import\s+websockets?", "WebSocket import", 0.85),
    (r"ws://|wss://", "WebSocket URL", 0.8),
    (r"import\s+grpc", "gRPC import", 0.9),
    (r"\.proto$", "protobuf file", 0.85),
    (r"grpc\.(server|insecure_channel)", "gRPC usage", 0.9),
    (r"import\s+dbus", "D-Bus import", 0.9),
    (r"SessionBus\(\)|SystemBus\(\)", "D-Bus bus", 0.9),
    (r"pythonosc|osc4py3|liblo", "OSC library", 0.9),
    (r"OSCServer|OSCClient", "OSC usage", 0.85),
    (r"mqtt", "MQTT", 0.7),
    (r"paho\.mqtt", "Paho MQTT", 0.9),
    (r"import\s+redis", "Redis import", 0.7),
    (r"app\s*=\s*Sanic\s*\(", "Sanic HTTP framework", 0.8),
]


class ProtocolDetector(Detector):
    @property
    def name(self) -> str:
        return "Protocol Detector"

    def detect(self, root: Path, files: list[FileInfo]) -> list[IPCMechanism]:
        evidence: list[str] = []
        max_confidence = 0.0
        details: dict[str, str] = {}

        for fi in files:
            content = self._read_file(root, fi)
            if not content:
                continue

            for pattern, desc, conf in PROTOCOL_PATTERNS:
                if re.search(pattern, content):
                    evidence.append(f"{fi.path}: {desc}")
                    max_confidence = max(max_confidence, conf)

                    # Identify specific protocol
                    if "grpc" in desc.lower():
                        details["protocol"] = "grpc"
                    elif "dbus" in desc.lower():
                        details["protocol"] = "dbus"
                    elif "osc" in desc.lower():
                        details["protocol"] = "osc"
                    elif "websocket" in desc.lower():
                        details["protocol"] = "websocket"
                    elif "mqtt" in desc.lower():
                        details["protocol"] = "mqtt"
                    elif "http" in desc.lower():
                        details["protocol"] = "http"

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
