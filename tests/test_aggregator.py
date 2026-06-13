"""Tests for the pure aggregation logic — the verdict decision core."""

from verification.aggregator import aggregate, MIN_RELEVANT_EVIDENCE_WEIGHT
from verification.schema import (
    Claim,
    EvidencePassage,
    StanceJudgment,
    StanceLabel,
    Verdict,
)


def _passage(pid="p1", retracted=False, credibility=1.0):
    return EvidencePassage(
        paper_id=pid,
        quote="some evidence",
        locator=f"{pid} [chars 0-10]",
        retrieval_score=0.9,
        credibility=credibility,
        retracted=retracted,
    )


def _judgment(label, confidence=0.9, pid="p1", retracted=False, credibility=1.0):
    return StanceJudgment(
        passage=_passage(pid, retracted, credibility),
        label=label,
        confidence=confidence,
    )


def test_supported_when_evidence_agrees():
    claim = Claim(text="X works")
    judgments = [
        _judgment(StanceLabel.SUPPORTS, 0.9, "p1"),
        _judgment(StanceLabel.SUPPORTS, 0.9, "p2"),
        _judgment(StanceLabel.SUPPORTS, 0.8, "p3"),
    ]
    report = aggregate(claim, judgments)
    assert report.verdict == Verdict.SUPPORTED
    assert report.confidence > 0
    assert report.support_count == 3


def test_refuted_when_evidence_disagrees():
    claim = Claim(text="X works")
    judgments = [
        _judgment(StanceLabel.REFUTES, 0.9, "p1"),
        _judgment(StanceLabel.REFUTES, 0.85, "p2"),
        _judgment(StanceLabel.REFUTES, 0.8, "p3"),
    ]
    report = aggregate(claim, judgments)
    assert report.verdict == Verdict.REFUTED


def test_contested_when_literature_is_split():
    """The headline differentiator: surface disagreement, don't hide it."""
    claim = Claim(text="X works")
    judgments = [
        _judgment(StanceLabel.SUPPORTS, 0.9, "p1"),
        _judgment(StanceLabel.SUPPORTS, 0.9, "p2"),
        _judgment(StanceLabel.REFUTES, 0.9, "p3"),
        _judgment(StanceLabel.REFUTES, 0.9, "p4"),
    ]
    report = aggregate(claim, judgments)
    assert report.verdict == Verdict.CONTESTED
    assert any("split" in f for f in report.flags)


def test_insufficient_when_evidence_is_thin():
    """Abstention: one weak passage is not enough to render a verdict."""
    claim = Claim(text="X works")
    judgments = [_judgment(StanceLabel.SUPPORTS, 0.3, "p1")]
    report = aggregate(claim, judgments)
    assert report.verdict == Verdict.INSUFFICIENT


def test_neutral_only_abstains():
    claim = Claim(text="X works")
    judgments = [
        _judgment(StanceLabel.NEUTRAL, 0.9, "p1"),
        _judgment(StanceLabel.NEUTRAL, 0.9, "p2"),
    ]
    report = aggregate(claim, judgments)
    assert report.verdict == Verdict.INSUFFICIENT


def test_retracted_source_contributes_no_weight():
    """A retracted paper must not be able to swing a verdict."""
    claim = Claim(text="X works")
    judgments = [
        _judgment(StanceLabel.SUPPORTS, 1.0, "p1", retracted=True),
        _judgment(StanceLabel.SUPPORTS, 1.0, "p2", retracted=True),
    ]
    report = aggregate(claim, judgments)
    assert report.verdict == Verdict.INSUFFICIENT
    assert any("RETRACTED" in f for f in report.flags)


def test_confidence_increases_with_more_agreeing_evidence():
    claim = Claim(text="X works")
    small = aggregate(claim, [
        _judgment(StanceLabel.SUPPORTS, 0.9, "p1"),
        _judgment(StanceLabel.SUPPORTS, 0.9, "p2"),
    ])
    large = aggregate(claim, [
        _judgment(StanceLabel.SUPPORTS, 0.9, f"p{i}") for i in range(6)
    ])
    assert large.confidence > small.confidence
