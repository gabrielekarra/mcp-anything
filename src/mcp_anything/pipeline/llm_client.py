"""Shared LLM helpers: JSON extraction and retries, on top of `mcp_anything.llm`.

The model is whatever `--model` or MCP_ANYTHING_MODEL chose (see llm.py).
"""

import json
import logging
from typing import Any, Optional

from mcp_anything import llm

_MAX_RETRIES = 3


def _extract_json(text: str) -> str:
    """Strip markdown code fences and extract the first JSON object or array."""
    import re

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
    model: Optional[str] = None,
    max_tokens: int = 16000,
) -> Any:
    """Call the model and return a parsed JSON object.

    Retries up to _MAX_RETRIES times if the response is not valid JSON,
    feeding the parse error back to the model.

    Raises llm.LLMUnavailable if no model can be used, RuntimeError if all
    retries are exhausted.
    """
    messages: list[dict] = [{"role": "user", "content": prompt}]
    last_error: Optional[str] = None

    for _ in range(_MAX_RETRIES):
        text = llm.chat(messages, system=system, max_tokens=max_tokens, model=model)
        try:
            return json.loads(_extract_json(text))
        except json.JSONDecodeError as exc:
            last_error = str(exc)
            messages += [
                {"role": "assistant", "content": text or "(empty)"},
                {"role": "user", "content": (
                    f"Your previous response was not valid JSON. Parse error: {last_error}\n"
                    "Please return ONLY the JSON object with no extra text or markdown."
                )},
            ]

    raise RuntimeError(
        f"LLM did not return valid JSON after {_MAX_RETRIES} attempts. "
        f"Last error: {last_error}"
    )


def call_llm_for_text(
    prompt: str,
    system: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: int = 8000,
) -> str:
    """Call the model and return the raw text response.

    Retries up to _MAX_RETRIES times on transient failures or empty responses.
    Raises llm.LLMUnavailable at once if no model can be used.
    """
    last_error: Optional[str] = None
    for _ in range(_MAX_RETRIES):
        try:
            text = llm.complete(prompt, system=system, max_tokens=max_tokens, model=model).strip()
        except llm.LLMUnavailable:
            raise
        except llm.LLMError as exc:
            last_error = str(exc)
            continue
        if text:
            return text
        last_error = "Empty text response from LLM"
        logging.getLogger(__name__).warning("LLM returned an empty response; retrying.")

    raise RuntimeError(
        f"LLM did not return usable text after {_MAX_RETRIES} attempts. "
        f"Last error: {last_error}"
    )
