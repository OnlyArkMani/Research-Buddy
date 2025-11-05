import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from agents.search_agent import SearchAgent
from models.llm import MistralLLM

def main():
    """Main application entry"""
    print("🚀 Initializing Research Paper Chatbot...")
    
    # Initialize components
    llm = MistralLLM()
    search_agent = SearchAgent()
    
    print("✅ Ready! Launch Chainlit UI with: chainlit run frontend/app.py")
    
    # Test query
    test_query = "transformer models for natural language processing"
    print(f"\n🔍 Testing with query: '{test_query}'")
    
    # Refine query
    refined = llm.refine_query(test_query)
    print(f"✨ Refined: {refined}")
    
    # Search papers
    papers = search_agent.search(test_query, max_results=5)
    print(f"📚 Found {len(papers)} papers")
    
    # Semantic search
    results = search_agent.semantic_search(test_query, k=5)
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['metadata']['title']}")
        print(f"   Relevance: {result['similarity']*100:.1f}%")

if __name__ == "__main__":
    main()