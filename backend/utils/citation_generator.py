from typing import Dict

class CitationGenerator:
    """Generate formatted citations for research papers"""
    
    @staticmethod
    def generate_apa(paper: Dict) -> str:
        """Generate APA format citation"""
        authors = paper.get('authors', 'Unknown')
        year = paper.get('year', 'n.d.')
        title = paper.get('title', 'Untitled')
        venue = paper.get('venue', '')
        url = paper.get('url', '')
        
        # Format authors (APA style: Last, F. M.)
        # Simplified version - assumes authors are already formatted
        author_list = authors.split(',')
        if len(author_list) > 7:
            apa_authors = ', '.join(author_list[:6]) + ', ... ' + author_list[-1]
        else:
            apa_authors = authors
        
        citation = f"{apa_authors} ({year}). {title}."
        
        if venue:
            citation += f" {venue}."
        
        if url:
            citation += f" {url}"
        
        return citation
    
    @staticmethod
    def generate_ieee(paper: Dict) -> str:
        """Generate IEEE format citation"""
        authors = paper.get('authors', 'Unknown')
        year = paper.get('year', 'n.d.')
        title = paper.get('title', 'Untitled')
        venue = paper.get('venue', '')
        
        # Format authors (IEEE style: F. M. Last)
        # Simplified version
        author_list = [a.strip() for a in authors.split(',')]
        if len(author_list) > 3:
            ieee_authors = ', '.join(author_list[:3]) + ', et al.'
        else:
            ieee_authors = ' and '.join(author_list) if len(author_list) > 1 else author_list[0]
        
        citation = f"{ieee_authors}, \"{title},\""
        
        if venue:
            citation += f" {venue},"
        
        citation += f" {year}."
        
        return citation
    
    @staticmethod
    def generate_mla(paper: Dict) -> str:
        """Generate MLA format citation"""
        authors = paper.get('authors', 'Unknown')
        title = paper.get('title', 'Untitled')
        venue = paper.get('venue', '')
        year = paper.get('year', 'n.d.')
        url = paper.get('url', '')
        
        # Format authors (MLA style: Last, First)
        # Simplified version
        author_list = authors.split(',')
        mla_authors = author_list[0].strip()
        if len(author_list) > 1:
            mla_authors += ', et al.'
        
        citation = f"{mla_authors}. \"{title}.\""
        
        if venue:
            citation += f" {venue},"
        
        citation += f" {year}."
        
        if url:
            citation += f" Web. {url}"
        
        return citation
    
    @staticmethod
    def generate_bibtex(paper: Dict) -> str:
        """Generate BibTeX format citation"""
        paper_id = paper.get('id', 'unknown').replace('/', '_').replace(':', '_')
        authors = paper.get('authors', 'Unknown')
        title = paper.get('title', 'Untitled')
        year = paper.get('year', '')
        venue = paper.get('venue', '')
        url = paper.get('url', '')
        
        bibtex = f"@article{{{paper_id},\n"
        bibtex += f"  author = {{{authors}}},\n"
        bibtex += f"  title = {{{title}}},\n"
        
        if venue:
            bibtex += f"  journal = {{{venue}}},\n"
        
        if year:
            bibtex += f"  year = {{{year}}},\n"
        
        if url:
            bibtex += f"  url = {{{url}}},\n"
        
        bibtex += "}"
        
        return bibtex
    
    @staticmethod
    def generate_all_formats(paper: Dict) -> Dict[str, str]:
        """Generate all citation formats"""
        return {
            'APA': CitationGenerator.generate_apa(paper),
            'IEEE': CitationGenerator.generate_ieee(paper),
            'MLA': CitationGenerator.generate_mla(paper),
            'BibTeX': CitationGenerator.generate_bibtex(paper)
        }