import google.generativeai as genai
from typing import Dict, Any, List
import json

class GeminiClient:
    def __init__(self, api_key: str):
        """Initialize Gemini Pro with conversation history"""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        self.conversation_history = []
        
    def generate(self, prompt: str, system_prompt: str = None, use_history: bool = False) -> str:
        """Generate response from Gemini"""
        if use_history and self.conversation_history:
            # Build conversation context
            full_prompt = self._build_conversation_prompt(prompt, system_prompt)
        else:
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        
        try:
            response = self.model.generate_content(full_prompt)
            
            # Add to history if using conversation mode
            if use_history:
                self.conversation_history.append({"role": "user", "content": prompt})
                self.conversation_history.append({"role": "assistant", "content": response.text})
            
            return response.text
        except Exception as e:
            print(f"Gemini error: {e}")
            return ""
    
    def _build_conversation_prompt(self, new_message: str, system_prompt: str = None) -> str:
        """Build prompt with conversation history"""
        prompt = ""
        
        if system_prompt:
            prompt += f"{system_prompt}\n\n"
        
        prompt += "Previous conversation:\n"
        for msg in self.conversation_history[-6:]:  # Last 3 exchanges
            role = "User" if msg["role"] == "user" else "Assistant"
            prompt += f"{role}: {msg['content']}\n\n"
        
        prompt += f"User: {new_message}\n\nAssistant:"
        
        return prompt
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
    
    def chat(self, message: str, context: Dict = None) -> str:
        """Handle general conversation with context"""
        system_prompt = """You are Research Buddy, a helpful AI assistant specializing in academic research.
        You help researchers find papers, explain concepts, answer questions, and have friendly conversations.
        Be conversational, knowledgeable, and supportive. Use the user's research context if provided."""
        
        # Add context if available
        if context:
            context_str = f"\nUser context: {json.dumps(context, indent=2)}"
            system_prompt += context_str
        
        return self.generate(message, system_prompt, use_history=True)
    
    def refine_query(self, user_query: str) -> Dict[str, Any]:
        """Extract detailed research parameters"""
        system_prompt = """You are an expert research assistant. Extract comprehensive research parameters from user queries.
        Return a JSON with:
        {
            "main_topic": "primary research area",
            "techniques": ["method1", "method2"],
            "domains": ["domain1", "domain2"],
            "keywords": ["key1", "key2", "key3"],
            "time_period": "if mentioned",
            "paper_type": "review/survey/experimental/theoretical"
        }"""
        
        response = self.generate(f"Extract parameters from: '{user_query}'", system_prompt)
        
        try:
            json_str = response.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
            
            return json.loads(json_str.strip())
        except:
            return {
                "main_topic": user_query,
                "keywords": user_query.split()
            }
    
    def is_research_query(self, query: str) -> bool:
        """Determine if query is about research papers or general chat"""
        research_keywords = [
            'paper', 'research', 'study', 'article', 'publication',
            'find', 'search', 'looking for', 'about', 'on',
            'detection', 'model', 'algorithm', 'method', 'approach',
            'summarize', 'bookmark', 'cite', 'filter'
        ]
        
        query_lower = query.lower()
        
        # Check for commands
        if any(cmd in query_lower for cmd in ['bookmark', 'summarize', 'cite', 'filter']):
            return True
        
        # Check for research keywords
        return any(keyword in query_lower for keyword in research_keywords) or len(query.split()) > 5
    
    def compare_papers(self, paper1: Dict, paper2: Dict) -> str:
        """Compare two research papers"""
        prompt = f"""Compare these two research papers in detail:

Paper 1:
Title: {paper1.get('title')}
Authors: {paper1.get('authors')}
Year: {paper1.get('year')}
Abstract: {paper1.get('abstract', '')[:500]}

Paper 2:
Title: {paper2.get('title')}
Authors: {paper2.get('authors')}
Year: {paper2.get('year')}
Abstract: {paper2.get('abstract', '')[:500]}

Provide:
1. Common research theme
2. Key methodological differences
3. Complementary insights
4. Which paper is more recent/cited
5. Recommendation for which to read first"""

        return self.generate(prompt)
    
    def generate_research_report(self, papers: List[Dict], topic: str) -> str:
        """Generate comprehensive research summary report"""
        papers_summary = "\n\n".join([
            f"Paper {i+1}: {p.get('title')} ({p.get('year')}) - {p.get('citations', 0)} citations"
            for i, p in enumerate(papers[:10])
        ])
        
        prompt = f"""Generate a comprehensive research summary report on: {topic}

Based on these papers:
{papers_summary}

Provide:
1. Executive Summary (3-4 sentences)
2. Key Findings & Trends
3. Major Methodologies Used
4. Research Gaps Identified
5. Future Directions
6. Top 3 Must-Read Papers

Format as a structured report."""

        return self.generate(prompt)