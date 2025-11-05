from typing import List, Dict
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from utils.api_clients import MultiSourceSearch
from database.sqlite_db import PaperDatabase
from database.vector_store import FAISSVectorStore
from models.embeddings import EmbeddingModel
from tqdm import tqdm

class SearchAgent:
    def __init__(self, semantic_scholar_key: str = None):
        """Initialize enhanced search agent"""
        self.multi_search = MultiSourceSearch(semantic_scholar_key)
        self.db = PaperDatabase()
        self.vector_store = FAISSVectorStore()
        self.embeddings = EmbeddingModel()
    
    def search(self, query: str, max_results: int = 50) -> List[Dict]:
        """Multi-source parallel search"""
        print(f"🔍 Searching across multiple sources for: '{query}'")
        
        # Parallel search across all sources
        all_papers = self.multi_search.search_all(query, max_per_source=20)
        
        print(f"📚 Found {len(all_papers)} papers from all sources")
        
        # Deduplicate
        unique_papers = self._deduplicate(all_papers)
        print(f"✨ {len(unique_papers)} unique papers after deduplication")
        
        # Store in database
        for paper in tqdm(unique_papers, desc="Storing papers"):
            try:
                self.db.add_paper(paper)
            except:
                pass
        
        # Generate embeddings in batches
        if unique_papers:
            abstracts = [p.get('abstract', p.get('title', '')) for p in unique_papers]
            print("🧠 Generating embeddings...")
            embeddings = self.embeddings.encode(abstracts)
            self.vector_store.add(embeddings, unique_papers)
        
        return unique_papers[:max_results]
    
    def semantic_search(self, query: str, k: int = 50) -> List[Dict]:
        """Enhanced semantic search with re-ranking"""
        query_embedding = self.embeddings.encode_single(query)
        results = self.vector_store.search(query_embedding, k=k)
        
        # Re-rank by multiple factors
        for result in results:
            paper = result['metadata']
            
            # Composite score
            relevance = result['similarity']
            citation_score = min(paper.get('citations', 0) / 1000, 1.0)  # Normalize citations
            recency_score = self._calculate_recency(paper.get('year'))
            
            # Weighted score
            result['final_score'] = (
                relevance * 0.6 +
                citation_score * 0.3 +
                recency_score * 0.1
            )
        
        # Sort by final score
        results.sort(key=lambda x: x['final_score'], reverse=True)
        
        return results
    
    def _deduplicate(self, papers: List[Dict]) -> List[Dict]:
        """Advanced deduplication by title similarity"""
        seen = {}
        unique = []
        
        for paper in papers:
            title = paper.get('title', '').lower().strip()
            # Remove common words and punctuation for better matching
            title_key = ''.join(c for c in title if c.isalnum() or c.isspace())
            title_key = ' '.join(title_key.split())  # Normalize whitespace
            
            if title_key and title_key not in seen:
                seen[title_key] = True
                unique.append(paper)
        
        return unique
    
    def _calculate_recency(self, year) -> float:
        """Calculate recency score (newer papers score higher)"""
        if not year:
            return 0.5
        
        from datetime import datetime
        current_year = datetime.now().year
        age = current_year - int(year)
        
        if age < 0:
            return 1.0
        elif age <= 2:
            return 1.0
        elif age <= 5:
            return 0.8
        elif age <= 10:
            return 0.6
        else:
            return 0.4