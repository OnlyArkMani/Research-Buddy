from typing import Dict, List, Optional
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from models.gemini_client import GeminiClient
from agents.search_agent import SearchAgent
from utils.summarizer import PaperSummarizer
from utils.citation_generator import CitationGenerator

class AutonomousResearchAgent:
    """Multi-step autonomous research agent"""
    
    def __init__(self, gemini_client: GeminiClient, search_agent: SearchAgent):
        self.gemini = gemini_client
        self.search_agent = search_agent
        self.summarizer = PaperSummarizer(gemini_client)
        
    async def execute_research_task(self, task: str, user_context: Dict = None) -> Dict:
        """
        Execute autonomous research task with multiple steps
        
        Args:
            task: User's research request
            user_context: User profile and preferences
            
        Returns:
            Complete research report
        """
        report = {
            'task': task,
            'steps': [],
            'papers': [],
            'summary': '',
            'citations': []
        }
        
        # Step 1: Parse intent
        step1 = await self._parse_research_intent(task)
        report['steps'].append(step1)
        
        # Step 2: Search papers
        step2 = await self._search_papers(step1['refined_query'])
        report['steps'].append(step2)
        report['papers'] = step2['papers']
        
        # Step 3: Rank and filter
        step3 = await self._rank_papers(step1['refined_query'], step2['papers'])
        report['steps'].append(step3)
        
        # Step 4: Summarize findings
        step4 = await self._generate_summary(task, step3['top_papers'])
        report['steps'].append(step4)
        report['summary'] = step4['summary']
        
        # Step 5: Generate citations
        step5 = await self._generate_citations(step3['top_papers'][:5])
        report['steps'].append(step5)
        report['citations'] = step5['citations']
        
        return report
    
    async def _parse_research_intent(self, task: str) -> Dict:
        """Step 1: Understand research intent"""
        refined = self.gemini.refine_query(task)
        
        return {
            'step': 'Intent Parsing',
            'status': 'completed',
            'refined_query': refined.get('main_topic', task),
            'parameters': refined
        }
    
    async def _search_papers(self, query: str) -> Dict:
        """Step 2: Search research papers"""
        papers = self.search_agent.search(query, max_results=50)
        
        return {
            'step': 'Paper Search',
            'status': 'completed',
            'papers': papers,
            'count': len(papers)
        }
    
    async def _rank_papers(self, query: str, papers: List[Dict]) -> Dict:
        """Step 3: Rank papers by relevance"""
        ranked = self.search_agent.semantic_search(query, k=min(20, len(papers)))
        
        top_papers = [result['metadata'] for result in ranked[:10]]
        
        return {
            'step': 'Paper Ranking',
            'status': 'completed',
            'top_papers': top_papers,
            'ranking_method': 'semantic similarity + citations + recency'
        }
    
    async def _generate_summary(self, topic: str, papers: List[Dict]) -> Dict:
        """Step 4: Generate research summary"""
        summary = self.gemini.generate_research_report(papers, topic)
        
        return {
            'step': 'Summary Generation',
            'status': 'completed',
            'summary': summary
        }
    
    async def _generate_citations(self, papers: List[Dict]) -> Dict:
        """Step 5: Generate citations"""
        citations = []
        
        for paper in papers:
            citations.append({
                'paper': paper.get('title'),
                'apa': CitationGenerator.generate_apa(paper),
                'ieee': CitationGenerator.generate_ieee(paper),
                'bibtex': CitationGenerator.generate_bibtex(paper)
            })
        
        return {
            'step': 'Citation Generation',
            'status': 'completed',
            'citations': citations
        }
    
    def format_report(self, report: Dict) -> str:
        """Format autonomous research report"""
        formatted = f"""# 🤖 Autonomous Research Report

## 📋 Task
{report['task']}

## 🔄 Execution Steps

"""
        
        for i, step in enumerate(report['steps'], 1):
            formatted += f"### Step {i}: {step['step']}\n"
            formatted += f"✅ Status: {step['status']}\n\n"
        
        formatted += f"""## 📚 Key Findings

{report['summary']}

## 📄 Top Papers ({len(report['papers'][:10])})

"""
        
        for i, paper in enumerate(report['papers'][:10], 1):
            formatted += f"**{i}. {paper.get('title')}**\n"
            formatted += f"- Authors: {paper.get('authors', 'Unknown')}\n"
            formatted += f"- Year: {paper.get('year', 'N/A')} | Citations: {paper.get('citations', 0)}\n"
            formatted += f"- [Link]({paper.get('url', '#')})\n\n"
        
        formatted += "## 📖 Citations\n\n"
        
        for citation in report['citations']:
            formatted += f"### {citation['paper']}\n\n"
            formatted += f"**APA**: {citation['apa']}\n\n"
            formatted += f"**IEEE**: {citation['ieee']}\n\n"
        
        return formatted