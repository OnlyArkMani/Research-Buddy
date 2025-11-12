from typing import Dict, Optional
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from models.gemini_client import GeminiClient
from models.llm import MistralLLM

class PaperSummarizer:
    """AI-powered paper summarization"""
    
    def __init__(self, gemini_client: Optional[GeminiClient] = None, mistral_client: Optional[MistralLLM] = None):
        self.gemini = gemini_client
        self.mistral = mistral_client
    
    def summarize_paper(self, paper: Dict, style: str = "concise") -> str:
        """
        Generate paper summary
        
        Args:
            paper: Paper metadata dict
            style: 'concise' (3 sentences), 'detailed' (1 paragraph), or 'key-points' (bullet list)
        """
        abstract = paper.get('abstract', '')
        title = paper.get('title', '')
        
        if not abstract:
            return "❌ No abstract available for summarization"
        
        # Build prompt based on style
        if style == "concise":
            prompt = f"""Summarize this research paper in exactly 3 clear sentences:

Title: {title}

Abstract: {abstract}

Provide: 1) Main topic, 2) Method/approach, 3) Key finding."""

        elif style == "detailed":
            prompt = f"""Provide a detailed but accessible summary (100-150 words) of this research paper:

Title: {title}

Abstract: {abstract}

Focus on: research question, methodology, main results, and significance."""

        elif style == "key-points":
            prompt = f"""Extract 5 key points from this research paper:

Title: {title}

Abstract: {abstract}

Format as bullet points covering: objective, method, results, conclusions, impact."""

        else:
            return "❌ Invalid summary style"
        
        # Try Gemini first (better quality), fall back to Mistral
        try:
            if self.gemini:
                return self.gemini.generate(prompt)
            elif self.mistral:
                return self.mistral.generate(prompt)
            else:
                return self._fallback_summary(abstract)
        except Exception as e:
            return f"❌ Summarization error: {str(e)}"
    
    def batch_summarize(self, papers: list[Dict], style: str = "concise", max_papers: int = 5) -> Dict[str, str]:
        """Summarize multiple papers (limited to avoid rate limits)"""
        summaries = {}
        
        for i, paper in enumerate(papers[:max_papers]):
            paper_id = paper.get('id', f"paper_{i}")
            summaries[paper_id] = self.summarize_paper(paper, style)
        
        return summaries
    
    def _fallback_summary(self, abstract: str) -> str:
        """Simple extractive summary if no LLM available"""
        sentences = abstract.split('. ')
        # Take first 3 sentences
        return '. '.join(sentences[:3]) + '.'
    
    def compare_papers(self, paper1: Dict, paper2: Dict) -> str:
        """Compare two papers and highlight differences"""
        prompt = f"""Compare these two research papers and highlight key differences:

Paper 1:
Title: {paper1.get('title')}
Abstract: {paper1.get('abstract', '')[:500]}

Paper 2:
Title: {paper2.get('title')}
Abstract: {paper2.get('abstract', '')[:500]}

Provide: 1) Common theme, 2) Key differences in approach, 3) Complementary insights."""

        try:
            if self.gemini:
                return self.gemini.generate(prompt)
            elif self.mistral:
                return self.mistral.generate(prompt)
        except:
            pass
        
        return "Comparison unavailable"