"""Classify the stance of an evidence passage toward a claim.

For each (claim, passage) pair we ask: does this passage SUPPORT, REFUTE, or
stay NEUTRAL on the claim? This is a natural-language-inference (entailment /
contradiction / neutral) task. We use an LLM-as-classifier here, constrained to
structured JSON, with a guard that anything labelled supports/refutes must cite
a quote drawn from the passage — that grounding requirement is what prevents the
"confident but fabricated" failure mode of plain generation.

The classifier is swappable: a fine-tuned cross-encoder NLI model could drop in
behind the same ``classify_stance`` signature later.
"""

from __future__ import annotations

from typing import Optional

from .schema import EvidencePassage, StanceJudgment, StanceLabel
from .providers import LLMProvider, extract_json


_SYSTEM = (
    "You are a scientific natural-language-inference classifier. Given a CLAIM "
    "and an EVIDENCE passage from a paper, decide whether the evidence SUPPORTS "
    "the claim, REFUTES it, or is NEUTRAL (irrelevant or insufficient). Judge "
    "ONLY from the evidence text — never from prior knowledge. If the evidence "
    "does not actually address the claim, you must answer neutral."
)

_PROMPT = """CLAIM:
{claim}

EVIDENCE (from "{title}"):
\"\"\"{evidence}\"\"\"

Respond with ONLY a JSON object:
{{
  "label": "supports" | "refutes" | "neutral",
  "confidence": <float 0..1>,
  "quote": "<verbatim span from the EVIDENCE that justifies the label, or empty if neutral>",
  "rationale": "<one sentence>"
}}"""


def classify_stance(
    claim_text: str,
    passage: EvidencePassage,
    llm: LLMProvider,
) -> StanceJudgment:
    """Return a StanceJudgment for one (claim, passage) pair."""
    raw = llm.generate(
        _PROMPT.format(
            claim=claim_text,
            title=passage.paper_title or passage.paper_id,
            evidence=passage.quote,
        ),
        _SYSTEM,
    )
    parsed = extract_json(raw) or {}

    label = _coerce_label(parsed.get("label"))
    confidence = _coerce_conf(parsed.get("confidence"))
    quote = str(parsed.get("quote", "")).strip()
    rationale = str(parsed.get("rationale", "")).strip()

    # Grounding guard: a supports/refutes verdict must be backed by a quote that
    # actually appears in the evidence. If not, we distrust it and downgrade to
    # neutral. This is the anti-hallucination check.
    if label in (StanceLabel.SUPPORTS, StanceLabel.REFUTES):
        if not quote or not _quote_grounded(quote, passage.quote):
            label = StanceLabel.NEUTRAL
            confidence = min(confidence, 0.3)
            rationale = (rationale + " [downgraded: quote not grounded in evidence]").strip()
        else:
            # Replace the passage's stored quote with the precise grounding span.
            passage.quote = _best_span(quote, passage.quote)

    return StanceJudgment(
        passage=passage,
        label=label,
        confidence=confidence,
        rationale=rationale,
    )


def _coerce_label(value) -> StanceLabel:
    v = str(value or "").strip().lower()
    if v.startswith("support"):
        return StanceLabel.SUPPORTS
    if v.startswith("refute") or v.startswith("contradict"):
        return StanceLabel.REFUTES
    return StanceLabel.NEUTRAL


def _coerce_conf(value) -> float:
    try:
        c = float(value)
    except (TypeError, ValueError):
        return 0.5
    return max(0.0, min(1.0, c))


def _normalize(s: str) -> str:
    import re
    return re.sub(r"\s+", " ", s or "").strip().lower()


def _quote_grounded(quote: str, evidence: str, min_overlap: float = 0.6) -> bool:
    """True if the quote is (mostly) present in the evidence text.

    Exact-substring is the happy path; otherwise we accept high token overlap to
    tolerate minor LLM paraphrase/whitespace differences.
    """
    nq, ne = _normalize(quote), _normalize(evidence)
    if not nq:
        return False
    if nq in ne:
        return True
    q_tokens = set(nq.split())
    if not q_tokens:
        return False
    e_tokens = set(ne.split())
    overlap = len(q_tokens & e_tokens) / len(q_tokens)
    return overlap >= min_overlap


def _best_span(quote: str, evidence: str) -> str:
    """Return the exact evidence substring if present, else the quote itself."""
    nq, ne = _normalize(quote), _normalize(evidence)
    if nq in ne:
        # Map back to original-cased evidence span.
        idx = ne.find(nq)
        return evidence[idx:idx + len(quote)] if idx != -1 else quote
    return quote
