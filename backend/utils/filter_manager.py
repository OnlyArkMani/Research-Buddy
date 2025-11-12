from typing import List, Dict, Optional
from datetime import datetime

class FilterManager:
    """Manages smart filtering for research papers"""
    
    def __init__(self):
        self.active_filters = {
            'min_year': None,
            'max_year': None,
            'min_citations': None,
            'max_citations': None,
            'domains': [],
            'keywords': []
        }
    
    def set_filter(self, filter_type: str, value):
        """Set a specific filter"""
        if filter_type in self.active_filters:
            self.active_filters[filter_type] = value
            return True
        return False
    
    def clear_filters(self):
        """Reset all filters"""
        self.active_filters = {
            'min_year': None,
            'max_year': None,
            'min_citations': None,
            'max_citations': None,
            'domains': [],
            'keywords': []
        }
    
    def apply_filters(self, papers: List[Dict]) -> List[Dict]:
        """Apply all active filters to paper list"""
        filtered = papers.copy()
        
        # Year filter
        if self.active_filters['min_year']:
            filtered = [p for p in filtered if p.get('year') and p['year'] >= self.active_filters['min_year']]
        
        if self.active_filters['max_year']:
            filtered = [p for p in filtered if p.get('year') and p['year'] <= self.active_filters['max_year']]
        
        # Citation filter
        if self.active_filters['min_citations']:
            filtered = [p for p in filtered if p.get('citations', 0) >= self.active_filters['min_citations']]
        
        if self.active_filters['max_citations']:
            filtered = [p for p in filtered if p.get('citations', 0) <= self.active_filters['max_citations']]
        
        # Domain filter
        if self.active_filters['domains']:
            filtered = [p for p in filtered if self._matches_domain(p, self.active_filters['domains'])]
        
        # Keyword filter
        if self.active_filters['keywords']:
            filtered = [p for p in filtered if self._matches_keywords(p, self.active_filters['keywords'])]
        
        return filtered
    
    def _matches_domain(self, paper: Dict, domains: List[str]) -> bool:
        """Check if paper matches domain filter"""
        paper_fields = paper.get('fields', [])
        if not paper_fields:
            return True  # Include if no domain info
        
        return any(domain.lower() in str(paper_fields).lower() for domain in domains)
    
    def _matches_keywords(self, paper: Dict, keywords: List[str]) -> bool:
        """Check if paper matches keyword filter"""
        searchable_text = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()
        return any(keyword.lower() in searchable_text for keyword in keywords)
    
    def get_active_filters_summary(self) -> str:
        """Get human-readable summary of active filters"""
        active = []
        
        if self.active_filters['min_year'] or self.active_filters['max_year']:
            year_range = f"{self.active_filters['min_year'] or 'any'}-{self.active_filters['max_year'] or 'present'}"
            active.append(f"📅 Years: {year_range}")
        
        if self.active_filters['min_citations']:
            active.append(f"📊 Min citations: {self.active_filters['min_citations']}")
        
        if self.active_filters['domains']:
            active.append(f"🏷️ Domains: {', '.join(self.active_filters['domains'])}")
        
        if self.active_filters['keywords']:
            active.append(f"🔑 Keywords: {', '.join(self.active_filters['keywords'])}")
        
        return "\n".join(active) if active else "No filters active"
    
    def parse_filter_from_query(self, query: str) -> Dict:
        """Extract filter parameters from natural language query"""
        filters = {}
        query_lower = query.lower()
        
        # Year extraction
        current_year = datetime.now().year
        
        if 'recent' in query_lower or 'latest' in query_lower:
            filters['min_year'] = current_year - 3
        elif 'last 5 years' in query_lower:
            filters['min_year'] = current_year - 5
        elif 'after' in query_lower:
            # Try to extract year after "after"
            import re
            match = re.search(r'after\s+(\d{4})', query_lower)
            if match:
                filters['min_year'] = int(match.group(1))
        
        # Citation extraction
        if 'highly cited' in query_lower:
            filters['min_citations'] = 100
        elif 'influential' in query_lower:
            filters['min_citations'] = 50
        
        return filters