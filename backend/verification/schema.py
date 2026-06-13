"""Typed data structures for the claim-verification pipeline.

Plain dataclasses + enums (stdlib only) so the whole schema is importable and
testable without pydantic or any heavy dependency.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Optional


class StanceLabel(str, Enum):
    """How a single evidence passage relates to a claim."""
    SUPPORTS = "supports"
    REFUTES = "refutes"
    NEUTRAL = "neutral"


class Verdict(str, Enum):
    """The aggregate verdict for a claim across all its evidence."""
    SUPPORTED = "supported"
    REFUTED = "refuted"
    CONTESTED = "contested"        # the literature disagrees
    INSUFFICIENT = "insufficient"  # not enough evidence to judge -> abstain


@dataclass
class Claim:
    """An atomic, independently checkable assertion."""
    text: str
    source: str = "user"  # "user", or e.g. "gpt-4o answer", for fact-checking LLM output


@dataclass
class EvidencePassage:
    """A retrieved passage with everything needed to verify it independently."""
    paper_id: str
    quote: str                 # the exact span used as evidence
    locator: str               # human-readable pointer (title + char span)
    retrieval_score: float     # similarity from retrieval
    paper_title: str = ""
    url: str = ""
    year: Optional[int] = None
    venue: str = ""
    credibility: float = 1.0   # 0..1; lowered for retracted / low-quality sources
    retracted: bool = False


@dataclass
class StanceJudgment:
    """A classifier's stance for one (claim, evidence) pair."""
    passage: EvidencePassage
    label: StanceLabel
    confidence: float          # 0..1, the classifier's confidence in the label
    rationale: str = ""

    @property
    def effective_weight(self) -> float:
        """Weight this judgment by classifier confidence and source credibility.

        Retracted sources contribute no weight to a verdict (but are still shown,
        flagged, in the report)."""
        if self.passage.retracted:
            return 0.0
        return max(0.0, min(1.0, self.confidence)) * max(0.0, min(1.0, self.passage.credibility))


@dataclass
class ClaimReport:
    """The full, auditable result for one claim."""
    claim: Claim
    verdict: Verdict
    confidence: float                       # 0..1 confidence in the verdict
    judgments: List[StanceJudgment] = field(default_factory=list)
    support_count: int = 0
    refute_count: int = 0
    neutral_count: int = 0
    flags: List[str] = field(default_factory=list)  # e.g. "cites retracted source"

    @property
    def supporting(self) -> List[StanceJudgment]:
        return [j for j in self.judgments if j.label == StanceLabel.SUPPORTS]

    @property
    def refuting(self) -> List[StanceJudgment]:
        return [j for j in self.judgments if j.label == StanceLabel.REFUTES]

    def consensus_distribution(self) -> dict:
        return {
            "supports": self.support_count,
            "refutes": self.refute_count,
            "neutral": self.neutral_count,
        }


@dataclass
class VerificationReport:
    """Top-level result for a piece of input text (one or more claims)."""
    input_text: str
    claim_reports: List[ClaimReport] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "input_text": self.input_text,
            "claims": [
                {
                    "claim": cr.claim.text,
                    "source": cr.claim.source,
                    "verdict": cr.verdict.value,
                    "confidence": round(cr.confidence, 3),
                    "consensus": cr.consensus_distribution(),
                    "flags": cr.flags,
                    "evidence": [
                        {
                            "label": j.label.value,
                            "confidence": round(j.confidence, 3),
                            "quote": j.passage.quote,
                            "locator": j.passage.locator,
                            "url": j.passage.url,
                            "retracted": j.passage.retracted,
                            "rationale": j.rationale,
                        }
                        for j in cr.judgments
                    ],
                }
                for cr in self.claim_reports
            ],
        }
