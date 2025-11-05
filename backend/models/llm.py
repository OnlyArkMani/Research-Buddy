import ollama
from typing import Dict, Any

class MistralLLM:
    def __init__(self, model_name: str = "mistral:7b"):
        self.model_name = model_name
        self.client = ollama.Client()
        
    def generate(self, prompt: str, system_prompt: str = None) -> str:
        """Generate response from Mistral 7B"""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat(
            model=self.model_name,
            messages=messages
        )
        
        return response['message']['content']
    
    def refine_query(self, user_query: str) -> Dict[str, Any]:
        """Extract key research topics and refine query"""
        system_prompt = """You are a research assistant that extracts key topics 
        from user queries about research papers. Extract:
        1. Main research area
        2. Specific techniques/methods
        3. Application domain
        4. Time period (if mentioned)
        Return as JSON."""
        
        prompt = f"Extract research parameters from: '{user_query}'"
        
        response = self.generate(prompt, system_prompt)
        
        # Parse response (add error handling in production)
        import json
        try:
            return json.loads(response)
        except:
            return {"main_topic": user_query, "keywords": []}