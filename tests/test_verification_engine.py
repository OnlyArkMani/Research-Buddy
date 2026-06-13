"""End-to-end tests for the verification engine using mock LLM + retriever.

These exercise the full decompose -> retrieve -> classify -> aggregate path,
plus the two behaviours that make the feature special: the anti-hallucination
grounding guard, and abstention/contradiction in the final report.
"""

import json

from verification.engine import ClaimVerificationEngine, format_report_markdown
from verification.schema import EvidencePassage, Verdict, StanceLabel, VerificationReport
from verification.stance_classifier import classify_stance
from verification.providers import MockLLMProvider


class ListRetriever:
    """Returns a fixed set of evidence passages regardless of the query."""

    def __init__(self, passages):
        self._passages = passages

    def retrieve_evidence(self, claim_text, k=5):
        return list(self._passages[:k])


def _passage(quote, pid="p1", title="Paper", retracted=False):
    return EvidencePassage(
        paper_id=pid,
        quote=quote,
        locator=f"{title} [chars 0-{len(quote)}]",
        retrieval_score=0.9,
        paper_title=title,
        retracted=retracted,
    )


def _wrap(claim_report):
    """Wrap a single ClaimReport in a VerificationReport for formatting."""
    return VerificationReport(input_text="x", claim_reports=[claim_report])


def test_grounding_guard_downgrades_ungrounded_support():
    """A 'supports' verdict whose quote is NOT in the evidence is distrusted.

    This is the core anti-hallucination mechanism: the model cannot assert
    support by inventing a quote.
    """
    passage = _passage("The sky is blue and water is wet.")
    llm = MockLLMProvider(lambda p, s: json.dumps({
        "label": "supports",
        "confidence": 0.95,
        "quote": "transformers outperform every model ever made",
        "rationale": "fabricated",
    }))
    judgment = classify_stance("Transformers are the best", passage, llm)
    assert judgment.label == StanceLabel.NEUTRAL
    assert "downgraded" in judgment.rationale


def test_grounded_support_is_accepted():
    passage = _passage("Experiments show the transformer outperforms the RNN baseline.")
    llm = MockLLMProvider(lambda p, s: json.dumps({
        "label": "supports",
        "confidence": 0.9,
        "quote": "the transformer outperforms the RNN baseline",
        "rationale": "direct match",
    }))
    judgment = classify_stance("Transformers beat RNNs", passage, llm)
    assert judgment.label == StanceLabel.SUPPORTS
    assert judgment.confidence == 0.9


def test_end_to_end_contested_claim():
    """Two grounded supports + two grounded refutes -> CONTESTED."""
    passages = [
        _passage("Our results confirm the method improves accuracy.", "p1", "Pro A"),
        _passage("We also observe the method improves accuracy markedly.", "p2", "Pro B"),
        _passage("In contrast, the method reduces accuracy in our trials.", "p3", "Con A"),
        _passage("We find the method reduces accuracy on held-out data.", "p4", "Con B"),
    ]

    def responder(prompt, system):
        # The claim ("improves accuracy") appears in every prompt, so key off the
        # evidence-only signal: "reduces accuracy" only appears in refuting evidence.
        if "reduces accuracy" in prompt:
            quote, label = "reduces accuracy", "refutes"
        else:
            quote, label = "improves accuracy", "supports"
        return json.dumps({"label": label, "confidence": 0.9, "quote": quote, "rationale": "x"})

    engine = ClaimVerificationEngine(ListRetriever(passages), MockLLMProvider(responder))
    report = engine.verify_claim("The method improves accuracy")
    assert report.verdict == Verdict.CONTESTED
    assert report.support_count == 2
    assert report.refute_count == 2
    assert "CONTESTED" in format_report_markdown(_wrap(report))


def test_insufficient_when_no_evidence_retrieved():
    engine = ClaimVerificationEngine(ListRetriever([]), MockLLMProvider(lambda p, s: ""))
    report = engine.verify_claim("Nobody has studied this")
    assert report.verdict == Verdict.INSUFFICIENT
