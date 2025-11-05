import google.generativeai as genai
from typing import Dict, Any
import json

class GeminiClient:
    def __init__(self, api_key: str):
        """Initialize Gemini Pro"""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        
    def generate(self, prompt: str, system_prompt: str = None) -> str:
        """Generate response from Gemini"""
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        
        try:
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            print(f"Gemini error: {e}")
            return ""
    
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
            # Clean response
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
        """Determine if query is about research papers"""
        research_keywords = [
            'paper', 'research', 'study', 'article', 'publication',
            'find', 'search', 'looking for', 'about', 'on',
            'detection', 'model', 'algorithm', 'method', 'approach'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in research_keywords) or len(query.split()) > 3
    
    def chat(self, message: str) -> str:
        """Handle general conversation"""
        system_prompt = """You are Research Buddy, a helpful AI assistant specializing in academic research.
        You help researchers find papers, explain concepts, and answer questions about research topics.
        Be concise, friendly, and helpful."""
        
        return self.generate(message, system_prompt)