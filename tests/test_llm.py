"""Issue #15: any model, any provider, no hardcoded model ids."""

import re
import sys
import types
from pathlib import Path

import pytest

from llm_fakes import FakeModelServer
from mcp_anything import llm
from mcp_anything.pipeline.llm_client import call_llm_for_json, call_llm_for_text

SRC = Path(__file__).parent.parent / "src" / "mcp_anything"
FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def clean_model(monkeypatch):
    for name in ("MCP_ANYTHING_MODEL", "MCP_ANYTHING_BASE_URL", "OLLAMA_HOST", "OPENAI_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    llm.set_model(None)
    yield
    llm.set_model(None)


def test_no_model_ids_outside_llm_module():
    offenders = []
    for path in SRC.rglob("*.py"):
        if path.name == "llm.py":
            continue
        for number, line in enumerate(path.read_text().splitlines(), 1):
            if re.search(r"claude-(sonnet|opus|haiku|fable|mythos|\d)", line):
                offenders.append(f"{path.relative_to(SRC)}:{number}: {line.strip()}")
    assert offenders == []


@pytest.mark.parametrize("spec, provider, name, url", [
    ("anthropic:claude-opus-5-5", "anthropic", "claude-opus-5-5", None),
    ("claude-sonnet-5-5", "anthropic", "claude-sonnet-5-5", None),
    ("ollama:qwen3:8b", "ollama", "qwen3:8b", "http://localhost:11434"),
    ("openai:gpt-5", "openai", "gpt-5", "https://api.openai.com/v1"),
    ("openrouter:meta-llama/llama-3.3-70b-instruct", "openrouter", "meta-llama/llama-3.3-70b-instruct", "https://openrouter.ai/api/v1"),
    ("lmstudio:qwen3-8b", "lmstudio", "qwen3-8b", "http://localhost:1234/v1"),
    ("llamacpp:any", "llamacpp", "any", "http://localhost:8080/v1"),
    ("vllm:Qwen/Qwen3-8B", "vllm", "Qwen/Qwen3-8B", "http://localhost:8000/v1"),
])
def test_model_spec_is_resolved(spec, provider, name, url):
    model = llm.resolve(spec)
    assert (model.provider, model.name, model.base_url) == (provider, name, url)


def test_unknown_provider_lists_the_known_ones():
    with pytest.raises(ValueError, match="Known: anthropic, ollama, openai"):
        llm.resolve("nope:x")


def test_model_from_environment_and_option(monkeypatch):
    assert llm.current() == llm.DEFAULT_MODEL
    monkeypatch.setenv("MCP_ANYTHING_MODEL", "ollama:qwen3:8b")
    assert llm.current() == "ollama:qwen3:8b"
    llm.set_model("openai:gpt-5")
    assert llm.current() == "openai:gpt-5"


def test_openai_compatible_round_trip(monkeypatch):
    with FakeModelServer("<think>let me see</think>Hello there.") as server:
        monkeypatch.setenv("MCP_ANYTHING_BASE_URL", server.url)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        assert llm.complete("Say hi", system="Be brief.", model="openai:gpt-5") == "Hello there."
        llm.complete("again", model="lmstudio:local")
    (path, body, headers), (_, second, plain_headers) = server.requests
    assert path == "/chat/completions"
    assert body["model"] == "gpt-5"
    assert body["messages"] == [{"role": "system", "content": "Be brief."}, {"role": "user", "content": "Say hi"}]
    assert headers["Authorization"] == "Bearer sk-test"
    assert "Authorization" not in plain_headers


def test_ollama_sets_context(monkeypatch):
    with FakeModelServer("ok") as server:
        monkeypatch.setenv("MCP_ANYTHING_BASE_URL", server.url)
        monkeypatch.setenv("MCP_ANYTHING_CONTEXT", "16384")
        assert llm.complete("hi", model="ollama:qwen3:8b") == "ok"
    path, body, _ = server.requests[0]
    assert path == "/api/chat" and body["stream"] is False and body["options"] == {"num_ctx": 16384}


def test_server_error_and_unreachable_server(monkeypatch):
    with FakeModelServer("model not found", status=404) as server:
        monkeypatch.setenv("MCP_ANYTHING_BASE_URL", server.url)
        with pytest.raises(llm.LLMError, match="HTTP 404"):
            llm.complete("hi", model="vllm:x")
    monkeypatch.setenv("MCP_ANYTHING_BASE_URL", "http://127.0.0.1:9")
    with pytest.raises(llm.LLMUnavailable, match="Cannot reach"):
        llm.complete("hi", model="vllm:x")


class FakeAnthropic:
    """Stands in for the anthropic package: records requests, returns a scripted response."""

    def __init__(self, content, stop_reason="end_turn"):
        self.requests, self.content, self.stop_reason = [], content, stop_reason
        fake = self

        class Messages:
            def create(self, **request):
                fake.requests.append(request)
                return types.SimpleNamespace(content=fake.content, stop_reason=fake.stop_reason)

        class Client:
            def __init__(self, *args, **kwargs):
                self.messages = Messages()
                self.beta = types.SimpleNamespace(messages=Messages())

        error = type("AnthropicError", (Exception,), {})
        self.module = types.SimpleNamespace(
            Anthropic=Client, AnthropicError=error,
            APIError=type("APIError", (error,), {}), AuthenticationError=type("AuthenticationError", (error,), {}),
        )


def block(kind, **fields):
    return types.SimpleNamespace(type=kind, **fields)


def test_anthropic_reply_with_thinking_block(monkeypatch):
    fake = FakeAnthropic([block("thinking", thinking=""), block("text", text="Hello."), block("text", text=" Again.")])
    monkeypatch.setitem(sys.modules, "anthropic", fake.module)

    assert llm.complete("hi", system="s", max_tokens=100) == "Hello. Again."

    (request,) = fake.requests
    assert request["model"] == "claude-opus-5-5" and request["system"] == "s"
    assert request["fallbacks"] == "default" and llm.FALLBACK_BETA in request["betas"]


def test_fallbacks_only_where_supported(monkeypatch):
    fake = FakeAnthropic([block("text", text="ok")])
    monkeypatch.setitem(sys.modules, "anthropic", fake.module)
    llm.complete("hi", model="claude-haiku-5-5")
    assert "fallbacks" not in fake.requests[0]


def test_refusal_is_reported(monkeypatch):
    fake = FakeAnthropic([], stop_reason="refusal")
    monkeypatch.setitem(sys.modules, "anthropic", fake.module)
    with pytest.raises(llm.LLMError, match="declined"):
        llm.complete("hi")


def test_missing_sdk_is_explained(monkeypatch):
    monkeypatch.setitem(sys.modules, "anthropic", None)
    with pytest.raises(llm.LLMUnavailable, match=r"mcp-anything\[llm\]"):
        llm.complete("hi")


def test_json_helper_retries_with_the_error(monkeypatch):
    with FakeModelServer("not json", '```json\n{"ok": true}\n```') as server:
        monkeypatch.setenv("MCP_ANYTHING_BASE_URL", server.url)
        llm.set_model("vllm:x")
        assert call_llm_for_json("give me json") == {"ok": True}
        assert call_llm_for_text("hello") == "{}"
    retry = server.requests[1][1]["messages"]
    assert retry[-2] == {"role": "assistant", "content": "not json"}
    assert "not valid JSON" in retry[-1]["content"]


def test_build_uses_the_chosen_model(monkeypatch, tmp_path):
    brief = tmp_path / "petstore.yaml"
    brief.write_text(
        "server_name: petstore-mcp\n"
        "domain_description: A pet store API for listing, adding and reading pets.\n"
        "use_cases:\n  - List pets\n  - Add a pet\n  - Read a pet\n"
        f"data_source_path: {FIXTURES / 'petstore_openapi.json'}\n"
        "data_source_kind: openapi\nbackend_target: fastmcp\n"
    )
    from mcp_anything import cli

    with FakeModelServer() as server:
        monkeypatch.setenv("MCP_ANYTHING_BASE_URL", server.url)
        cli.main(["build", "--brief", str(brief), "-o", str(tmp_path / "out"), "--auto-approve", "--model", "openai:fake-model"])
    assert server.requests, "no phase asked the chosen model"
    assert {body["model"] for _, body, _ in server.requests} == {"fake-model"}
    assert (tmp_path / "out").exists()
