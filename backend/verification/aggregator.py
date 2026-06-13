"""Aggregate per-passage stance judgments into a claim-level verdict.

This is the decision core, and deliberately pure (no LLM, no I/O) so it can be
tested exhaustively. It encodes the three behaviours that distinguish this
engine from a plain LLM answer:

  1. Abstention. If too little credible, confident evidence actually addresses
     the claim, we return INSUFFICIENT instead of guessing.
  2. Contradiction surfacing. When support and refutation are both substantial,
     we return CONTESTED rather than picking a side and hiding the conflict.
  3. Credibility weighting. Retracted sources contribute zero weight; lower-
     credibility sources contribute proportionally less.
"""

from __future__ import annotations

from typing import List

from .schema import (
    Claim,
    ClaimReport,
    StanceJudgment,
    StanceLabel,
    Verdict,
)


# Tunables (would be calibrated against a labelled claim set in evaluation).
MIN_RELEVANT_EVIDENCE_WEIGHT = 0.8   # total support+refute weight below this -> abstain
DECISIVE_NET_THRESHOLD = 0.5         # |net| at/above this -> a directional verdict
CONFIDENCE_CONF_FLOOR = 0.4          # judgments below this confidence are "weak"


def aggregate(claim: Claim, judgments: List[StanceJudgment]) -> ClaimReport:
    support = [j for j in judgments if j.label == StanceLabel.SUPPORTS]
    refute = [j for j in judgments if j.label == StanceLabel.REFUTES]
    neutral = [j for j in judgments if j.label == StanceLabel.NEUTRAL]

    support_w = sum(j.effective_weight for j in support)
    refute_w = sum(j.effective_weight for j in refute)
    directional_w = support_w + refute_w

    flags: List[str] = []
    if any(j.passage.retracted for j in judgments):
        flags.append("evidence set includes a RETRACTED source (excluded from verdict)")

    report = ClaimReport(
        claim=claim,
        verdict=Verdict.INSUFFICIENT,
        confidence=0.0,
        judgments=judgments,
        support_count=len(support),
        refute_count=len(refute),
        neutral_count=len(neutral),
        flags=flags,
    )

    # 1) Abstain when there isn't enough credible, confident directional evidence.
    if directional_w < MIN_RELEVANT_EVIDENCE_WEIGHT:
        report.verdict = Verdict.INSUFFICIENT
        # A little confidence scales with how close we were to the threshold.
        report.confidence = round(min(0.5, directional_w / (MIN_RELEVANT_EVIDENCE_WEIGHT * 2)), 3)
        return report

    # net in [-1, 1]: +1 fully supported, -1 fully refuted, 0 evenly split.
    net = (support_w - refute_w) / directional_w
    minority_w = min(support_w, refute_w)
    contested = minority_w >= 0.5 and abs(net) < DECISIVE_NET_THRESHOLD

    if contested:
        report.verdict = Verdict.CONTESTED
        # Confidence here = how confident we are that there IS a real dispute,
        # i.e. how balanced and well-supported both sides are.
        balance = 1.0 - abs(net)            # 1.0 when perfectly split
        report.confidence = round(_volume_factor(directional_w) * balance, 3)
        flags.append("literature is split — see supporting and refuting evidence")
        return report

    report.verdict = Verdict.SUPPORTED if net > 0 else Verdict.REFUTED
    report.confidence = round(_volume_factor(directional_w) * abs(net), 3)
    return report


def _volume_factor(weight: float) -> float:
    """Map total directional evidence weight to a 0..1 multiplier.

    More credible, confident evidence -> higher attainable confidence, with
    diminishing returns. Saturates near ~4 units of weight.
    """
    return min(1.0, weight / 4.0) ** 0.5
