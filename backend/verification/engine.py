"""Orchestrator for the Claim Verification & Contradiction Engine.

Pipeline:  decompose -> retrieve evidence -> classify stance -> aggregate -> report

The engine is composed of injected parts (LLM provider, an evidence retriever,
and the pure aggregator) so it runs identically against real models or test
mocks. The retriever only needs a ``retrieve_evidence(claim_text, k)`` method
returning ``EvidencePassage`` objects; ``RAGEvidenceRetriever`` adapts the
full-text ``PaperRAGIndex`` to that interface.
"""

from __future__ import annotations

from typing import Callable, List, Optional, Protocol, Sequence

from .schema import (
    Claim,
    ClaimReport,
    EvidencePassage,
    Verdict,
    VerificationReport,
)
from .providers import LLMProvider
from .claim_extractor import extract_claims
from .stance_classifier import classify_stance
from .aggregator import aggregate


class EvidenceRetriever(Protocol):
    def retrieve_evidence(self, claim_text: str, k: int = 5) -> List[EvidencePassage]: ...


class RAGEvidenceRetriever:
    """Adapts a full-text ``PaperRAGIndex`` to the EvidenceRetriever interface.

    ``retraction_checker`` is an optional callable(paper_id) -> bool used to flag
    retracted sources; ``credibility_fn`` is an optional callable(paper_meta) ->
    float in 0..1. Both default to "trust everything", and can be wired to a
    retraction database / venue ranking later.
    """

    def __init__(
        self,
        rag_index,
        retraction_checker: Optional[Callable[[str], bool]] = None,
        credibility_fn: Optional[Callable[[object], float]] = None,
    ):
        self._index = rag_index
        self._retraction_checker = retraction_checker or (lambda _pid: False)
        self._credibility_fn = credibility_fn or (lambda _chunk: 1.0)

    def retrieve_evidence(self, claim_text: str, k: int = 5) -> List[EvidencePassage]:
        passages = []
        for rp in self._index.retrieve(claim_text, k=k):
            c = rp.chunk
            retracted = bool(self._retraction_checker(c.paper_id))
            passages.append(
                EvidencePassage(
                    paper_id=c.paper_id,
                    quote=c.text,
                    locator=c.locator(),
                    retrieval_score=rp.score,
                    paper_title=c.paper_title,
                    url=c.url,
                    credibility=float(self._credibility_fn(c)),
                    retracted=retracted,
                )
            )
        return passages


class ClaimVerificationEngine:
    def __init__(
        self,
        retriever: EvidenceRetriever,
        llm: LLMProvider,
        evidence_per_claim: int = 6,
    ):
        self.retriever = retriever
        self.llm = llm
        self.evidence_per_claim = evidence_per_claim

    def verify_claim(self, claim_text: str, source: str = "user") -> ClaimReport:
        claim = Claim(text=claim_text, source=source)
        passages = self.retriever.retrieve_evidence(claim_text, k=self.evidence_per_claim)
        judgments = [classify_stance(claim.text, p, self.llm) for p in passages]
        return aggregate(claim, judgments)

    def verify_text(self, text: str, source: str = "user") -> VerificationReport:
        """Decompose text into atomic claims and verify each one."""
        claims = extract_claims(text, llm=self.llm, source=source)
        reports = [self.verify_claim(c.text, source=c.source) for c in claims]
        return VerificationReport(input_text=text, claim_reports=reports)


# ---------------------------------------------------------------------------
# Presentation
# ---------------------------------------------------------------------------

_VERDICT_BADGE = {
    Verdict.SUPPORTED: "✅ SUPPORTED",
    Verdict.REFUTED: "❌ REFUTED",
    Verdict.CONTESTED: "⚖️ CONTESTED",
    Verdict.INSUFFICIENT: "🤷 INSUFFICIENT EVIDENCE",
}


def format_report_markdown(report: VerificationReport) -> str:
    """Render a verification report as an auditable markdown evidence table."""
    out = ["# 🔎 Claim Verification Report\n"]
    for i, cr in enumerate(report.claim_reports, 1):
        dist = cr.consensus_distribution()
        out.append(f"## Claim {i}\n")
        out.append(f"> {cr.claim.text}\n")
        out.append(
            f"**Verdict:** {_VERDICT_BADGE[cr.verdict]}  |  "
            f"**Confidence:** {cr.confidence:.0%}  |  "
            f"**Consensus:** {dist['supports']} support / {dist['refutes']} refute "
            f"/ {dist['neutral']} neutral\n"
        )
        for flag in cr.flags:
            out.append(f"> ⚠️ {flag}\n")

        directional = [j for j in cr.judgments if j.label.value != "neutral"]
        if directional:
            out.append("\n**Evidence:**\n")
            for j in directional:
                tag = "🟢 supports" if j.label.value == "supports" else "🔴 refutes"
                retracted = " 🛑 RETRACTED" if j.passage.retracted else ""
                out.append(
                    f"- {tag} ({j.confidence:.0%}){retracted} — "
                    f"\"{j.passage.quote.strip()[:300]}\" "
                    f"— *{j.passage.locator}*"
                )
        else:
            out.append("\n*No passage directly addressed this claim.*")
        out.append("\n")
    return "\n".join(out)
