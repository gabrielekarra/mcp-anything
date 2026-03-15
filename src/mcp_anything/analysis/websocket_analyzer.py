"""Regex-based analyzer for WebSocket endpoints.

Detects WebSocket patterns across frameworks: FastAPI, Django Channels,
Socket.IO (Python and JS/TS), and the ws library.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from mcp_anything.models.analysis import Capability, FileInfo, IPCType, Language, ParameterSpec


@dataclass
class WebSocketEndpoint:
    """A WebSocket endpoint extracted from source code."""

    path: str
    handler_name: str
    events: list[str]
    parameters: list[ParameterSpec]
    source_file: str
    framework: str


@dataclass
class WebSocketAnalysisResult:
    """Result of analyzing a file for WebSocket endpoints."""

    endpoints: list[WebSocketEndpoint] = field(default_factory=list)
    framework: str = ""


# --- FastAPI WebSocket patterns ---
_FASTAPI_WS_ROUTE_RE = re.compile(
    r'@\w+\.websocket\s*\(\s*["\']([^"\']+)["\']\s*\)'
)
_FASTAPI_WS_EVENT_RE = re.compile(
    r'await\s+websocket\.(receive_text|receive_json|send_text|send_json|accept|close)\s*\('
)

# --- Django Channels patterns ---
_DJANGO_CHANNELS_RE = re.compile(
    r'class\s+(\w+)\s*\(\s*(?:Async)?WebsocketConsumer\s*\)'
)

# --- Python Socket.IO patterns ---
_SOCKETIO_PY_EVENT_RE = re.compile(
    r'@\w+\.on\s*\(\s*["\'](\w+)["\']\s*\)'
)

# --- JavaScript/TypeScript Socket.IO patterns ---
_SOCKETIO_JS_SERVER_RE = re.compile(
    r'io\.on\s*\(\s*["\']connection["\']\s*,'
)
_SOCKETIO_JS_EVENT_RE = re.compile(
    r'socket\.on\s*\(\s*["\'](\w+)["\']\s*,'
)

# --- JavaScript/TypeScript ws library patterns ---
_WS_SERVER_RE = re.compile(
    r'new\s+WebSocket\.Server\s*\('
)
_WS_EVENT_RE = re.compile(
    r'wss?\.on\s*\(\s*["\'](\w+)["\']\s*,'
)


def _extract_path_params(path: str) -> list[ParameterSpec]:
    """Extract path parameters from a WebSocket route path."""
    params = []
    for match in re.finditer(r'\{(\w+)\}', path):
        params.append(ParameterSpec(
            name=match.group(1),
            type="string",
            description=f"Path parameter: {match.group(1)}",
            required=True,
        ))
    return params


def _analyze_python_websocket(source: str, file_info: FileInfo) -> Optional[WebSocketAnalysisResult]:
    """Analyze a Python file for WebSocket patterns."""
    result = WebSocketAnalysisResult()

    # Check for FastAPI WebSocket routes
    ws_routes = _FASTAPI_WS_ROUTE_RE.findall(source)
    ws_events = _FASTAPI_WS_EVENT_RE.findall(source)

    if ws_routes:
        result.framework = "fastapi-ws"
        # Find handler function names by looking for async def after each decorator
        handler_re = re.compile(
            r'@\w+\.websocket\s*\(\s*["\']([^"\']+)["\']\s*\)\s*\n\s*async\s+def\s+(\w+)'
        )
        handlers = handler_re.findall(source)

        for path, handler_name in handlers:
            # Find events used in this handler's body
            # Get the handler body (rough: from def to next def or end)
            handler_start = source.find(f"def {handler_name}")
            if handler_start == -1:
                continue
            # Find the next top-level def or class or end of file
            next_def = re.search(r'\ndef\s+\w+|\nclass\s+\w+', source[handler_start + 1:])
            if next_def:
                handler_body = source[handler_start:handler_start + 1 + next_def.start()]
            else:
                handler_body = source[handler_start:]

            events = list(set(_FASTAPI_WS_EVENT_RE.findall(handler_body)))
            events.sort()
            params = _extract_path_params(path)

            result.endpoints.append(WebSocketEndpoint(
                path=path,
                handler_name=handler_name,
                events=events,
                parameters=params,
                source_file=file_info.path,
                framework="fastapi-ws",
            ))

        if result.endpoints:
            return result

    # Check for Django Channels
    channel_classes = _DJANGO_CHANNELS_RE.findall(source)
    if channel_classes:
        result.framework = "django-channels"
        for class_name in channel_classes:
            result.endpoints.append(WebSocketEndpoint(
                path=f"/{class_name.lower()}/",
                handler_name=class_name,
                events=["connect", "disconnect", "receive"],
                parameters=[],
                source_file=file_info.path,
                framework="django-channels",
            ))
        return result

    # Check for Python Socket.IO
    sio_events = _SOCKETIO_PY_EVENT_RE.findall(source)
    if sio_events:
        result.framework = "socketio"
        events = list(set(sio_events))
        events.sort()
        result.endpoints.append(WebSocketEndpoint(
            path="/socket.io",
            handler_name="socketio_server",
            events=events,
            parameters=[],
            source_file=file_info.path,
            framework="socketio",
        ))
        return result

    return None


def _analyze_js_websocket(source: str, file_info: FileInfo) -> Optional[WebSocketAnalysisResult]:
    """Analyze a JavaScript/TypeScript file for WebSocket patterns."""
    result = WebSocketAnalysisResult()

    # Check for Socket.IO
    if _SOCKETIO_JS_SERVER_RE.search(source):
        result.framework = "socketio"
        events = _SOCKETIO_JS_EVENT_RE.findall(source)
        events = list(set(events))
        events.sort()
        result.endpoints.append(WebSocketEndpoint(
            path="/socket.io",
            handler_name="socketio_server",
            events=events,
            parameters=[],
            source_file=file_info.path,
            framework="socketio",
        ))
        return result

    # Check for ws library
    if _WS_SERVER_RE.search(source):
        result.framework = "ws"
        events = _WS_EVENT_RE.findall(source)
        events = list(set(events))
        events.sort()
        result.endpoints.append(WebSocketEndpoint(
            path="/",
            handler_name="ws_server",
            events=events,
            parameters=[],
            source_file=file_info.path,
            framework="ws",
        ))
        return result

    return None


def analyze_websocket_file(
    root: Path, file_info: FileInfo,
) -> Optional[WebSocketAnalysisResult]:
    """Analyze a source file for WebSocket endpoint patterns.

    Supports FastAPI, Django Channels, Socket.IO (Python and JS/TS),
    and the ws library.
    """
    try:
        source = (root / file_info.path).read_text(errors="replace")
    except OSError:
        return None

    if file_info.language == Language.PYTHON:
        return _analyze_python_websocket(source, file_info)
    elif file_info.language in (Language.JAVASCRIPT, Language.TYPESCRIPT):
        return _analyze_js_websocket(source, file_info)

    return None


def websocket_results_to_capabilities(
    results: dict[str, WebSocketAnalysisResult],
) -> list[Capability]:
    """Convert WebSocket analysis results into Capability objects.

    Each endpoint becomes a Capability with category='websocket'
    and ipc_type=IPCType.PROTOCOL.
    """
    capabilities: list[Capability] = []
    seen: set[str] = set()

    for file_path, result in results.items():
        for ep in result.endpoints:
            # Generate tool name from path or handler name
            tool_name = _endpoint_to_tool_name(ep)

            if tool_name in seen:
                continue
            seen.add(tool_name)

            events_desc = ", ".join(ep.events) if ep.events else "none"
            desc = f"WebSocket {ep.path} - Events: {events_desc}"

            capabilities.append(Capability(
                name=tool_name,
                description=desc,
                category="websocket",
                parameters=ep.parameters,
                return_type="string",
                source_file=file_path,
                source_function=ep.handler_name,
                ipc_type=IPCType.PROTOCOL,
            ))

    return capabilities


def _endpoint_to_tool_name(ep: WebSocketEndpoint) -> str:
    """Generate a snake_case tool name from a WebSocket endpoint."""
    # Try to use the path first
    path = ep.path.strip("/")
    if path and path != "socket.io":
        parts = path.split("/")
        clean_parts = []
        for part in parts:
            if part.startswith("{") and part.endswith("}"):
                clean_parts.append(f"by_{part[1:-1]}")
            else:
                clean_parts.append(part)
        name = "ws_" + "_".join(clean_parts)
    else:
        # Fall back to handler name
        name = f"ws_{ep.handler_name}"

    name = re.sub(r'[^a-z0-9_]', '_', name.lower())
    name = re.sub(r'_+', '_', name).strip('_')
    return name
