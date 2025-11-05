import arxiv
import requests
from typing import List, Dict
import time
from Bio import Entrez
import aiohttp
import asyncio

class ArxivClient:
    def __init__(self):
        self.client = arxiv.Client()
    
    def search(self, query: str, max_results: int = 20) -> List[Dict]:
        """Search arXiv papers"""
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )
        
        papers = []
        try:
            for result in self.client.results(search):
                papers.append({
                    'id': result.entry_id,
                    'title': result.title,
                    'authors': ', '.join([a.name for a in result.authors]),
                    'abstract': result.summary,
                    'year': result.published.year,
                    'venue': 'arXiv',
                    'citations': 0,
                    'url': result.entry_id,
                    'pdf_url': result.pdf_url,
                    'source': 'arXiv'
                })
        except Exception as e:
            print(f"arXiv error: {e}")
        
        return papers


class SemanticScholarClient:
    def __init__(self, api_key: str = None):
        self.base_url = "https://api.semanticscholar.org/graph/v1"
        self.headers = {'x-api-key': api_key} if api_key else {}
    
    def search(self, query: str, limit: int = 20) -> List[Dict]:
        """Search Semantic Scholar"""
        url = f"{self.base_url}/paper/search"
        params = {
            'query': query,
            'limit': limit,
            'fields': 'title,authors,abstract,year,venue,citationCount,url,openAccessPdf,fieldsOfStudy'
        }
        
        try:
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            
            if response.status_code == 429:
                time.sleep(2)
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
                    'pdf_url': pdf_url,
                    'source': 'Semantic Scholar',
                    'fields': paper.get('fieldsOfStudy', [])
                })
            
            return papers
        except Exception as e:
            print(f"Semantic Scholar error: {e}")
            return []


class PubMedClient:
    def __init__(self, email: str = "researcher@example.com"):
        Entrez.email = email
    
    def search(self, query: str, max_results: int = 20) -> List[Dict]:
        """Search PubMed papers"""
        papers = []
        
        try:
            # Search for IDs
            handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results, sort="relevance")
            record = Entrez.read(handle)
            handle.close()
            
            id_list = record.get("IdList", [])
            
            if not id_list:
                return papers
            
            # Fetch details
            handle = Entrez.efetch(db="pubmed", id=id_list, rettype="xml", retmode="xml")
            records = Entrez.read(handle)
            handle.close()
            
            for article in records.get('PubmedArticle', []):
                medline = article.get('MedlineCitation', {})
                article_data = medline.get('Article', {})
                
                title = article_data.get('ArticleTitle', 'No title')
                abstract_list = article_data.get('Abstract', {}).get('AbstractText', [])
                abstract = ' '.join(abstract_list) if abstract_list else ''
                
                authors_list = article_data.get('AuthorList', [])
                authors = ', '.join([
                    f"{a.get('LastName', '')} {a.get('ForeName', '')}" 
                    for a in authors_list[:3]
                ])
                
                pub_date = article_data.get('Journal', {}).get('JournalIssue', {}).get('PubDate', {})
                year = pub_date.get('Year', 'N/A')
                
                pmid = medline.get('PMID', '')
                
                papers.append({
                    'id': f"PMID:{pmid}",
                    'title': title,
                    'authors': authors,
                    'abstract': abstract,
                    'year': int(year) if year != 'N/A' and year.isdigit() else None,
                    'venue': 'PubMed',
                    'citations': 0,
                    'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    'pdf_url': None,
                    'source': 'PubMed'
                })
        
        except Exception as e:
            print(f"PubMed error: {e}")
        
        return papers


class COREClient:
    def __init__(self):
        self.base_url = "https://api.core.ac.uk/v3"
    
    def search(self, query: str, limit: int = 20) -> List[Dict]:
        """Search CORE papers (no API key needed for basic search)"""
        # CORE requires API key for most features, returning empty for now
        # You can register at https://core.ac.uk/services/api for free tier
        return []


class MultiSourceSearch:
    def __init__(self, semantic_scholar_key: str = None):
        self.arxiv = ArxivClient()
        self.semantic_scholar = SemanticScholarClient(semantic_scholar_key)
        self.pubmed = PubMedClient()
        self.core = COREClient()
    
    async def search_all_async(self, query: str, max_per_source: int = 20) -> List[Dict]:
        """Parallel search across all sources"""
        loop = asyncio.get_event_loop()
        
        tasks = [
            loop.run_in_executor(None, self.arxiv.search, query, max_per_source),
            loop.run_in_executor(None, self.semantic_scholar.search, query, max_per_source),
            loop.run_in_executor(None, self.pubmed.search, query, max_per_source),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_papers = []
        for result in results:
            if isinstance(result, list):
                all_papers.extend(result)
        
        return all_papers
    
    def search_all(self, query: str, max_per_source: int = 20) -> List[Dict]:
        """Synchronous wrapper"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.search_all_async(query, max_per_source))