"""Runtime validation tests for the generated github-scoped package."""

import asyncio
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest


def _run(awaitable):
    """Run async FastMCP helpers in synchronous pytest tests."""
    return asyncio.run(awaitable)


class TestPackageRuntime:
    """Validate generated package coherence across startup surfaces."""

    def test_pyproject_has_console_entrypoint(self):
        # tests/ is one level below the package root
        root = Path(__file__).parent.parent
        pyproject = (root / "pyproject.toml").read_text()
        assert '[project.scripts]' in pyproject
        assert 'mcp-github-scoped = "mcp_github_scoped.server:main"' in pyproject

    def test_mcp_config_matches_transport(self):
        root = Path(__file__).parent.parent
        config = json.loads((root / "mcp.json").read_text())
        server_entry = config["mcpServers"]["github-scoped"]
        assert server_entry["command"] == "mcp-github-scoped"
        assert server_entry["args"] == []

    def test_server_startup_default_transport(self, server_module, monkeypatch):
        mock_run = MagicMock()
        monkeypatch.setattr(server_module.server, "run", mock_run)
        monkeypatch.delenv("MCP_TRANSPORT", raising=False)
        monkeypatch.delenv("MCP_HOST", raising=False)
        monkeypatch.delenv("MCP_PORT", raising=False)

        server_module.main()

        mock_run.assert_called_once_with(transport="stdio")

    def test_server_startup_transport_override(self, server_module, monkeypatch):
        mock_run = MagicMock()
        monkeypatch.setattr(server_module.server, "run", mock_run)
        monkeypatch.setenv("MCP_TRANSPORT", "http")
        monkeypatch.setenv("MCP_HOST", "127.0.0.1")
        monkeypatch.setenv("MCP_PORT", "9100")

        server_module.main()

        assert server_module.server.settings.host == "127.0.0.1"
        assert server_module.server.settings.port == 9100
        mock_run.assert_called_once_with(transport="streamable-http")

    def test_backend_instance_is_available(self, server_module):
        assert hasattr(server_module, "_backend")
        backend = server_module._backend
        assert hasattr(backend, "request")

    def test_registered_runtime_surfaces(self, server):
        assert len(_run(server.list_tools())) == 67
        assert len(_run(server.list_resources())) == 4
        assert len(_run(server.list_prompts())) == 2
