"""Standalone demo of the Claim Verification & Contradiction Engine.

Runs with NO API keys and NO model downloads: it uses a tiny deterministic
embedder and a scripted "LLM" so you can see the end-to-end output shape. In
production you'd swap in EmbeddingModel + GeminiProvider/MistralProvider.

    python verify_demo.py

The scenario is the headline use case: take a confident answer an LLM might
produce, decompose it into atomic claims, and verify each against a corpus of
(here, toy) papers — surfacing support, contradiction, and abstention.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

import numpy as np  # noqa: E402

from utils.pdf_rag import PaperRAGIndex  # noqa: E402
from verification.engine import (  # noqa: E402
    ClaimVerificationEngine,
    RAGEvidenceRetriever,
    format_report_markdown,
)
from verification.providers import MockLLMProvider  # noqa: E402


class ToyEmbedder:
    """Bag-of-words embedder over a fixed vocab — deterministic, no downloads."""
    VOCAB = ["dropout", "overfitting", "reduces", "increases", "batchnorm",
             "accuracy", "regularization", "training", "speed", "generalization"]

    def encode(self, texts):
        return np.array([self._v(t) for t in texts], dtype="float32")

    def encode_single(self, text):
        return self._v(text)

    def _v(self, text):
        t = text.lower()
        return np.array([float(t.count(w)) for w in self.VOCAB], dtype="float32")


# ---- A tiny corpus: two papers support, one refutes the dropout claim. -------
PAPERS = [
    ("p1", "Dropout: A Simple Way to Prevent Overfitting",
     "We show that dropout reduces overfitting and improves generalization "
     "and accuracy on held-out data across many tasks. Dropout regularization "
     "reduces overfitting substantially."),
    ("p2", "Empirical Study of Regularization",
     "Our experiments confirm dropout reduces overfitting and improves "
     "generalization. Regularization with dropout reduces overfitting."),
    ("p3", "When Dropout Hurts",
     "In contrast, we find dropout increases training error and reduces "
     "accuracy in low-data regimes; dropout increases overfitting here."),
]


def scripted_llm(prompt, system=None):
    """Stand-in for a real LLM. Claim extraction returns a JSON array; stance
    classification keys off words present in the evidence."""
    import json
    if "atomic factual claims" in (system or "") or "atomic factual claims" in prompt:
        # Claim-decomposition call.
        return json.dumps([
            "Dropout reduces overfitting.",
            "Dropout improves training speed.",
        ])
    # Stance-classification call. The prompt embeds both the CLAIM and the
    # EVIDENCE. No paper actually discusses training speed, so for that claim we
    # answer neutral regardless of evidence -> the engine should ABSTAIN.
    if "speed" in prompt:
        return json.dumps({"label": "neutral", "confidence": 0.3, "quote": "",
                           "rationale": "evidence does not address training speed"})
    if "increases" in prompt and "overfitting" in prompt:
        return json.dumps({"label": "refutes", "confidence": 0.85,
                           "quote": "dropout increases overfitting", "rationale": "contradicts"})
    if "reduces overfitting" in prompt:
        return json.dumps({"label": "supports", "confidence": 0.9,
                           "quote": "dropout reduces overfitting", "rationale": "direct support"})
    return json.dumps({"label": "neutral", "confidence": 0.4, "quote": "", "rationale": "off-topic"})


def main():
    index = PaperRAGIndex(ToyEmbedder(), chunk_size=200, overlap=40)
    for pid, title, text in PAPERS:
        index.add_paper(pid, text, title=title)

    retriever = RAGEvidenceRetriever(index)
    engine = ClaimVerificationEngine(retriever, MockLLMProvider(scripted_llm), evidence_per_claim=5)

    # The "confident LLM answer" we want to fact-check.
    llm_answer = (
        "Dropout reduces overfitting, and it also improves training speed."
    )
    print("INPUT (an answer to fact-check):\n  " + llm_answer + "\n")

    report = engine.verify_text(llm_answer, source="demo-llm-answer")
    print(format_report_markdown(report))


if __name__ == "__main__":
    main()
