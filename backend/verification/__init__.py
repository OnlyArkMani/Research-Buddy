"""Claim Verification & Contradiction Engine.

The differentiator feature: take a research claim (or a sentence from any LLM's
answer) and return a verdict grounded in real papers — SUPPORTED / REFUTED /
CONTESTED / INSUFFICIENT — where every judgment quotes the exact source span.

This targets a structural weakness of frontier models: they hallucinate
citations, smooth disagreement into false consensus, and never abstain. This
engine asserts nothing it cannot quote, surfaces contradictions explicitly,
and returns calibrated "insufficient evidence" when the literature is thin.
"""

from .schema import (
    StanceLabel,
    Verdict,
    Claim,
    EvidencePassage,
    StanceJudgment,
    ClaimReport,
    VerificationReport,
)
from .engine import ClaimVerificationEngine

__all__ = [
    "StanceLabel",
    "Verdict",
    "Claim",
    "EvidencePassage",
    "StanceJudgment",
    "ClaimReport",
    "VerificationReport",
    "ClaimVerificationEngine",
]
