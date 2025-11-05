import arxiv
import requests
from typing import List, Dict
import time

class ArxivClient:
    def __init__(self):
        self.client = arxiv.Client()
    
    def search(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search arXiv papers"""
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )
        
        papers = []
        for result in self.client.results(search):
            papers.append({
                'id': result.entry_id,
                'title': result.title,
                'authors': ', '.join([a.name for a in result.authors]),
                'abstract': result.summary,
                'year': result.published.year,
                'venue': 'arXiv',
                'citations': 0,  # arXiv doesn't provide citation count
                'url': result.entry_id,
                'pdf_url': result.pdf_url
            })
        
        return papers


class SemanticScholarClient:
    def __init__(self, api_key: str = None):
        """Initialize Semantic Scholar API client"""
        self.base_url = "https://api.semanticscholar.org/graph/v1"
        self.headers = {}
        if api_key:
            self.headers['x-api-key'] = api_key
    
    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """Search Semantic Scholar papers"""
        url = f"{self.base_url}/paper/search"
        params = {
            'query': query,
            'limit': limit,
            'fields': 'title,authors,abstract,year,venue,citationCount,url,openAccessPdf'
        }
        
        response = requests.get(url, params=params, headers=self.headers)
        
        if response.status_code == 429:
            time.sleep(60)  # Rate limit hit
            return self.search(query, limit)
        
        if response.status_code != 200:
            return []
        
        data = response.json()
        
        papers = []
        for paper in data.get('data', []):
            authors = ', '.join([a['name'] for a in paper.get('authors', [])])
            pdf_url = paper.get('openAccessPdf', {}).get('url') if paper.get('openAccessPdf') else None
            
            papers.append({
                'id': paper.get('paperId'),
                'title': paper.get('title'),
                'authors': authors,
                'abstract': paper.get('abstract', ''),
                'year': paper.get('year'),
                'venue': paper.get('venue', 'Semantic Scholar'),
                'citations': paper.get('citationCount', 0),
                'url': paper.get('url'),
                'pdf_url': pdf_url
            })
        
        return papers