"""Unit tests for the generated github-scoped backend."""

import asyncio
import json
import types
from unittest.mock import AsyncMock

import pytest

from mcp_github_scoped.backend import Backend


def _run(awaitable):
    """Run async backend helpers in synchronous pytest tests."""
    return asyncio.run(awaitable)


class TestHttpBackend:
    """Verify HTTP backend response formatting."""

    def test_request_pretty_prints_json_response(self, monkeypatch):
        backend = Backend()

        class FakeResponse:
            status_code = 200
            text = '{"ok": true}'

            def json(self):
                return {"ok": True}

        fake_client = types.SimpleNamespace(request=AsyncMock(return_value=FakeResponse()))
        monkeypatch.setattr(backend, "_get_client", AsyncMock(return_value=fake_client))

        result = _run(backend.request("GET", "/items"))

        assert json.loads(result) == {"ok": True}
        fake_client.request.assert_awaited_once()

    def test_request_returns_raw_text_when_json_parsing_fails(self, monkeypatch):
        backend = Backend()

        class FakeResponse:
            status_code = 200
            text = "plain-text-response"

            def json(self):
                raise ValueError("not json")

        fake_client = types.SimpleNamespace(request=AsyncMock(return_value=FakeResponse()))
        monkeypatch.setattr(backend, "_get_client", AsyncMock(return_value=fake_client))

        result = _run(backend.request("GET", "/items"))

        assert result == "plain-text-response"
