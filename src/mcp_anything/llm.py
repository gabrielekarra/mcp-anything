"""Every model call goes through here, so any provider can do the work.

Choose the model with `--model provider:model` or the MCP_ANYTHING_MODEL
environment variable:

    anthropic:claude-opus-5-5     (or just claude-opus-5-5; needs the `llm` extra)
    openai:gpt-5                  OPENAI_API_KEY
    openrouter:<model>            OPENROUTER_API_KEY
    ollama:qwen3:8b               OLLAMA_HOST, default localhost:11434
    lmstudio:<model>              localhost:1234
    llamacpp:<model>              localhost:8080
    vllm:<model>                  localhost:8000

MCP_ANYTHING_BASE_URL overrides the server address of any non-Anthropic
provider; MCP_ANYTHING_CONTEXT sets Ollama's context window (default 32768).
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Optional

DEFAULT_MODEL = "anthropic:claude-opus-5-5"

# Claude models that accept server-side refusal fallbacks: when one declines a
# request, the API retries it on another model within the same call.
FALLBACK_MODELS = {"claude-fable-5-2", "claude-fable-5-1", "claude-opus-5-5", "claude-opus-5", "claude-sonnet-5-5"}
FALLBACK_BETA = "server-side-fallback-2026-07-01"

OPENAI_COMPATIBLE = {
    "openai": ("https://api.openai.com/v1", "OPENAI_API_KEY"),
    "openrouter": ("https://openrouter.ai/api/v1", "OPENROUTER_API_KEY"),
    "lmstudio": ("http://localhost:1234/v1", None),
    "llamacpp": ("http://localhost:8080/v1", None),
    "vllm": ("http://localhost:8000/v1", None),
}
PROVIDERS = ["anthropic", "ollama", *OPENAI_COMPATIBLE]

_chosen: Optional[str] = None  # set by --model


class LLMError(RuntimeError):
    """A model call failed, or the model declined the request."""


class LLMUnavailable(LLMError):
    """No model can be used: a missing package, key or server."""


@dataclass
class Model:
    provider: str
    name: str
    base_url: Optional[str] = None
    api_key: Optional[str] = None

    def __str__(self):
        return f"{self.provider}:{self.name}"


def set_model(spec: Optional[str]) -> None:
    """Use `spec` for every model call in this process (the --model option)."""
    global _chosen
    if spec:
        resolve(spec)  # fail early on a bad spec
    _chosen = spec


def current() -> str:
    return _chosen or os.environ.get("MCP_ANYTHING_MODEL") or DEFAULT_MODEL


def resolve(spec: Optional[str] = None) -> Model:
    spec = spec or current()
    prefix, _, name = spec.partition(":")
    if spec.startswith("claude-"):
        prefix, name = "anthropic", spec
    if not name:
        raise ValueError(f"Model {spec!r} needs a name after the provider, e.g. ollama:qwen3:8b.")
    override = os.environ.get("MCP_ANYTHING_BASE_URL")
    if prefix == "anthropic":
        return Model("anthropic", name)
    if prefix == "ollama":
        host = override or os.environ.get("OLLAMA_HOST", "localhost:11434")
        host = host if "://" in host else f"http://{host}"
        return Model("ollama", name, host.rstrip("/"))
    if prefix in OPENAI_COMPATIBLE:
        url, key = OPENAI_COMPATIBLE[prefix]
        return Model(prefix, name, (override or url).rstrip("/"), os.environ.get(key) if key else None)
    raise ValueError(f"Unknown model provider {prefix!r} in {spec!r}. Known: {', '.join(PROVIDERS)}.")


def chat(messages: list[dict], system: Optional[str] = None, max_tokens: int = 8000,
         model: Optional[str] = None) -> str:
    """Send a conversation of user/assistant messages; return the reply's text."""
    chosen = resolve(model)
    if chosen.provider == "anthropic":
        return _anthropic(chosen, messages, system, max_tokens)
    if chosen.provider == "ollama":
        return _ollama(chosen, messages, system)
    return _openai(chosen, messages, system, max_tokens)


def complete(prompt: str, system: Optional[str] = None, max_tokens: int = 8000, model: Optional[str] = None) -> str:
    """One prompt in, the reply's text out."""
    return chat([{"role": "user", "content": prompt}], system, max_tokens, model)


# --- providers ---------------------------------------------------------------------


def _anthropic(chosen: Model, messages, system, max_tokens):
    try:
        import anthropic
    except ImportError:
        raise LLMUnavailable("Claude models need the Anthropic SDK: pip install 'mcp-anything[llm]'") from None
    try:
        client = anthropic.Anthropic()
        request = {"model": chosen.name, "max_tokens": max_tokens, "messages": messages}
        if system:
            request["system"] = system
        if chosen.name in FALLBACK_MODELS:
            response = client.beta.messages.create(**request, betas=[FALLBACK_BETA], fallbacks="default")
        else:
            response = client.messages.create(**request)
    except anthropic.AuthenticationError as error:
        raise LLMUnavailable(f"Anthropic rejected the API key: {error}") from None
    except anthropic.APIError as error:
        raise LLMError(f"Anthropic API error: {error}") from None
    except (anthropic.AnthropicError, TypeError) as error:  # e.g. no credentials configured at all
        raise LLMUnavailable(f"No Anthropic credentials: set ANTHROPIC_API_KEY or choose another --model ({error})") from None
    if getattr(response, "stop_reason", None) == "refusal":
        raise LLMError("The model declined this request.")
    # Replies can start with thinking blocks: keep only the text.
    return "".join(block.text for block in response.content if getattr(block, "type", None) == "text")


def _openai(chosen: Model, messages, system, max_tokens):
    body = {"model": chosen.name, "messages": ([{"role": "system", "content": system}] if system else []) + messages,
            "max_tokens": max_tokens}
    headers = {"Authorization": f"Bearer {chosen.api_key}"} if chosen.api_key else {}
    data = _post(f"{chosen.base_url}/chat/completions", body, headers, str(chosen))
    choice = (data.get("choices") or [{}])[0]
    if choice.get("finish_reason") == "content_filter":
        raise LLMError("The model declined this request.")
    return _visible((choice.get("message") or {}).get("content") or "")


def _ollama(chosen: Model, messages, system):
    body = {
        "model": chosen.name,
        "messages": ([{"role": "system", "content": system}] if system else []) + messages,
        "stream": False,
        # Ollama silently drops what does not fit its default window: a spec
        # prompt would lose its beginning.
        "options": {"num_ctx": int(os.environ.get("MCP_ANYTHING_CONTEXT", "32768"))},
    }
    data = _post(f"{chosen.base_url}/api/chat", body, {}, str(chosen))
    return _visible((data.get("message") or {}).get("content") or "")


def _post(url, body, headers, name):
    request = urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json", **headers})
    try:
        with urllib.request.urlopen(request, timeout=600) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        raise LLMError(f"{name}: HTTP {error.code}: {error.read().decode('utf-8', 'replace')[:300]}") from None
    except (urllib.error.URLError, OSError) as error:
        raise LLMUnavailable(f"Cannot reach {name} at {url}: {getattr(error, 'reason', error)}") from None


def _visible(text: str) -> str:
    """Text without the reasoning some local models wrap in <think> tags."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    if "</think>" in text:
        text = text.split("</think>", 1)[1]
    return text.strip()
