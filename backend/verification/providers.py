"""LLM provider abstraction for the verification engine.

The engine depends only on the small ``LLMProvider`` protocol below, so it can
run against Gemini, a local Mistral via Ollama, or a scripted mock in tests.
This dependency injection is what lets the whole pipeline be unit-tested
without network access or model downloads.
"""

from __future__ import annotations

from typing import Callable, List, Optional, Protocol
import json
import re


class LLMProvider(Protocol):
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str: ...


def extract_json(raw: str):
    """Best-effort JSON extraction from an LLM response.

    Handles ```json fences and leading/trailing prose. Returns the parsed
    object, or None if nothing parseable is found.
    """
    if not raw:
        return None
    text = raw.strip()
    # Strip code fences.
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    # Fall back to the first {...} or [...] block.
    for opener, closer in (("{", "}"), ("[", "]")):
        start = text.find(opener)
        end = text.rfind(closer)
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except Exception:
                continue
    return None


class GeminiProvider:
    """Adapter over the project's GeminiClient."""

    def __init__(self, gemini_client):
        self._client = gemini_client

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        return self._client.generate(prompt, system_prompt)


class MistralProvider:
    """Adapter over the project's local MistralLLM (Ollama)."""

    def __init__(self, mistral_client):
        self._client = mistral_client

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        return self._client.generate(prompt, system_prompt)


class MockLLMProvider:
    """Scripted provider for tests.

    Pass a callable that maps (prompt, system_prompt) -> response string, or a
    list of responses to be returned in order.
    """

    def __init__(self, responder):
        if isinstance(responder, list):
            self._queue = list(responder)
            self._fn: Optional[Callable] = None
        else:
            self._fn = responder
            self._queue = None
        self.calls: List[dict] = []

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        self.calls.append({"prompt": prompt, "system_prompt": system_prompt})
        if self._fn is not None:
            return self._fn(prompt, system_prompt)
        if self._queue:
            return self._queue.pop(0)
        return ""
