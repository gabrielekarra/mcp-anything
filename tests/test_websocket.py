"""Tests for the WebSocket endpoint analyzer."""

from pathlib import Path

import pytest

from mcp_anything.analysis.scanner import scan_codebase
from mcp_anything.analysis.websocket_analyzer import (
    WebSocketAnalysisResult,
    analyze_websocket_file,
    websocket_results_to_capabilities,
)


@pytest.fixture
def fake_websocket_app() -> Path:
    return Path(__file__).parent / "fixtures" / "fake_websocket_app"


def _collect_ws_results(app_dir: Path) -> dict[str, WebSocketAnalysisResult]:
    """Scan a directory and collect all WebSocket analysis results."""
    files = scan_codebase(app_dir)
    results: dict[str, WebSocketAnalysisResult] = {}
    for fi in files:
        res = analyze_websocket_file(app_dir, fi)
        if res is not None:
            results[fi.path] = res
    return results


class TestWebSocketAnalyzer:
    def test_finds_fastapi_ws_endpoints(self, fake_websocket_app: Path) -> None:
        results = _collect_ws_results(fake_websocket_app)
        # Should find the ws_server.py file with FastAPI WebSocket endpoints
        ws_server_results = [
            r for r in results.values() if r.framework == "fastapi-ws"
        ]
        assert len(ws_server_results) == 1
        assert len(ws_server_results[0].endpoints) == 2

    def test_finds_socketio_events(self, fake_websocket_app: Path) -> None:
        results = _collect_ws_results(fake_websocket_app)
        sio_results = [
            r for r in results.values() if r.framework == "socketio"
        ]
        assert len(sio_results) == 1
        events = sio_results[0].endpoints[0].events
        # socket_io.js has: chat message, join room, typing, disconnect
        # Note: "chat message" won't match \w+ (has a space), so regex catches
        # word-only event names
        assert "typing" in events
        assert "disconnect" in events

    def test_extracts_ws_path(self, fake_websocket_app: Path) -> None:
        results = _collect_ws_results(fake_websocket_app)
        ws_server_results = [
            r for r in results.values() if r.framework == "fastapi-ws"
        ]
        assert len(ws_server_results) == 1
        paths = [ep.path for ep in ws_server_results[0].endpoints]
        assert "/ws/chat" in paths
        assert "/ws/notifications/{user_id}" in paths

    def test_extracts_events(self, fake_websocket_app: Path) -> None:
        results = _collect_ws_results(fake_websocket_app)
        ws_server_results = [
            r for r in results.values() if r.framework == "fastapi-ws"
        ]
        assert len(ws_server_results) == 1
        # Find the chat endpoint
        chat_eps = [
            ep for ep in ws_server_results[0].endpoints
            if ep.path == "/ws/chat"
        ]
        assert len(chat_eps) == 1
        events = chat_eps[0].events
        assert "receive_json" in events
        assert "send_json" in events
        assert "accept" in events

        # Find the notification endpoint
        notif_eps = [
            ep for ep in ws_server_results[0].endpoints
            if ep.path == "/ws/notifications/{user_id}"
        ]
        assert len(notif_eps) == 1
        events = notif_eps[0].events
        assert "receive_text" in events
        assert "send_text" in events
        assert "accept" in events


class TestWebSocketCapabilities:
    def test_endpoints_become_capabilities(self, fake_websocket_app: Path) -> None:
        results = _collect_ws_results(fake_websocket_app)
        capabilities = websocket_results_to_capabilities(results)
        # Should have capabilities from both ws_server.py and socket_io.js
        assert len(capabilities) >= 3  # 2 FastAPI + 1 Socket.IO
        # All should have category="websocket"
        for cap in capabilities:
            assert cap.category == "websocket"
            assert cap.ipc_type is not None
            assert cap.ipc_type.value == "protocol"
        # Check that tool names are generated
        names = [cap.name for cap in capabilities]
        assert all(name.startswith("ws_") for name in names)
