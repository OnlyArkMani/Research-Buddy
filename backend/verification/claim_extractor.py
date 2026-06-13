"""Decompose a block of text into atomic, independently checkable claims.

Why this matters: a sentence like "Transformers outperform RNNs and train
faster" contains two distinct claims that may have different evidence and even
different verdicts. Verifying the paragraph as one unit hides that. We split
into atomic claims first, then verify each separately.
"""

from __future__ import annotations

from typing import List, Optional
import re

from .schema import Claim
from .providers import LLMProvider, extract_json


_SYSTEM = (
    "You are a meticulous scientific fact-checking assistant. You break text "
    "into atomic, self-contained, verifiable claims. Each claim must stand "
    "alone (resolve pronouns), state exactly one assertion, and be checkable "
    "against scientific literature. Ignore opinions, questions, and filler."
)

_PROMPT = """Break the following text into atomic factual claims.

Return ONLY a JSON array of strings, one per claim. If there are no checkable
factual claims, return [].

TEXT:
\"\"\"{text}\"\"\""""


def extract_claims(
    text: str,
    llm: Optional[LLMProvider] = None,
    source: str = "user",
    max_claims: int = 12,
) -> List[Claim]:
    """Extract atomic claims from text.

    Uses the LLM when provided; otherwise falls back to sentence segmentation
    so the pipeline still works (degraded) with no model available.
    """
    text = (text or "").strip()
    if not text:
        return []

    if llm is not None:
        raw = llm.generate(_PROMPT.format(text=text), _SYSTEM)
        parsed = extract_json(raw)
        if isinstance(parsed, list):
            claims = [
                Claim(text=str(c).strip(), source=source)
                for c in parsed
                if str(c).strip()
            ]
            if claims:
                return claims[:max_claims]
        # If the LLM response wasn't usable, fall through to heuristic split.

    return _sentence_fallback(text, source)[:max_claims]


def _sentence_fallback(text: str, source: str) -> List[Claim]:
    """Heuristic split: sentences that look like factual assertions."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    claims = []
    for s in sentences:
        s = s.strip()
        if len(s.split()) < 4:
            continue
        if s.endswith("?"):
            continue
        claims.append(Claim(text=s, source=source))
    # If splitting produced nothing, treat the whole text as one claim.
    return claims or [Claim(text=text, source=source)]
