"""Shared LLM client utility with JSON extraction and retry logic."""

import json
import re
from typing import Any, Optional


_DEFAULT_MODEL = "claude-sonnet-4-6"
_MAX_RETRIES = 3


def _extract_json(text: str) -> str:
    """Strip markdown code fences and extract the first JSON object or array."""
    text = text.strip()
    # Remove ```json ... ``` or ``` ... ``` fences
    fenced = re.sub(r"^```(?:json)?\s*\n?", "", text)
    fenced = re.sub(r"\n?```\s*$", "", fenced)
    if fenced != text:
        return fenced.strip()
    # Find first { or [ and return from there
    for i, ch in enumerate(text):
        if ch in ("{", "["):
            return text[i:]
    return text


def call_llm_for_json(
    prompt: str,
    system: Optional[str] = None,
    model: str = _DEFAULT_MODEL,
    max_tokens: int = 16000,
) -> Any:
    """Call the Claude API and return a parsed JSON object.

    Retries up to _MAX_RETRIES times if the response is not valid JSON,
    feeding the parse error back to the model.

    Raises ImportError if anthropic is not installed.
    Raises RuntimeError if all retries are exhausted.
    """
    import anthropic

    client = anthropic.Anthropic()
    messages: list[dict] = [{"role": "user", "content": prompt}]
    last_error: Optional[str] = None

    for attempt in range(_MAX_RETRIES):
        if attempt > 0 and last_error:
            messages.append({
                "role": "assistant",
                "content": _last_response_text,
            })
            messages.append({
                "role": "user",
                "content": (
                    f"Your previous response was not valid JSON. Parse error: {last_error}\n"
                    "Please return ONLY the JSON object with no extra text or markdown."
                ),
            })

        kwargs: dict = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system

        response = client.messages.create(**kwargs)
        _last_response_text = response.content[0].text

        try:
            return json.loads(_extract_json(_last_response_text))
        except json.JSONDecodeError as exc:
            last_error = str(exc)

    raise RuntimeError(
        f"LLM did not return valid JSON after {_MAX_RETRIES} attempts. "
        f"Last error: {last_error}"
    )
