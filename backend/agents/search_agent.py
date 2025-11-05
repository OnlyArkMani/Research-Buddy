from typing import List, Dict
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.api_clients import ArxivClient, SemanticScholarClient
from database.sqlite_db import PaperDatabase
from database.vector_store import FAISSVectorStore
from models.embeddings import EmbeddingModel

class SearchAgent:
    def __init__(self):
        """Initialize search agent"""
        self.arxiv = ArxivClient()
        self.semantic_scholar = SemanticScholarClient()
        self.db = PaperDatabase()
        self.vector_store = FAISSVectorStore()
        self.embeddings = EmbeddingModel()
    
    def search(self, query: str, max_results: int = 10) -> List[Dict]:
        """Parallel search across sources"""
        # Search both APIs
        arxiv_papers = self.arxiv.search(query, max_results=max_results)
        ss_papers = self.semantic_scholar.search(query, limit=max_results)
        
        # Combine and deduplicate
        all_papers = arxiv_papers + ss_papers
        unique_papers = self._deduplicate(all_papers)
        
        # Store in database
        for paper in unique_papers:
            self.db.add_paper(paper)
        
        # Generate embeddings and store in FAISS
        abstracts = [p.get('abstract', '') for p in unique_papers]
        embeddings = self.embeddings.encode(abstracts)
        self.vector_store.add(embeddings, unique_papers)
        
        return unique_papers
    
    def semantic_search(self, query: str, k: int = 10) -> List[Dict]:
        """Search using vector similarity"""
        query_embedding = self.embeddings.encode_single(query)
        results = self.vector_store.search(query_embedding, k=k)
        
        return results
    
    def _deduplicate(self, papers: List[Dict]) -> List[Dict]:
        """Remove duplicate papers by title"""
        seen = set()
        unique = []
        
        for paper in papers:
            title_lower = paper['title'].lower()
            if title_lower not in seen:
                seen.add(title_lower)
                unique.append(paper)
        
        return unique