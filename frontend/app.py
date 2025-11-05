import chainlit as cl
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from models.llm import MistralLLM
from agents.search_agent import SearchAgent

# Initialize components
llm = None
search_agent = None

@cl.on_chat_start
async def start():
    """Welcome message"""
    global llm, search_agent
    
    try:
        # Initialize components
        llm = MistralLLM()
        search_agent = SearchAgent()
        
        await cl.Message(
            content="👋 Hello! I'm your Research Paper Discovery Assistant. Tell me about your research topic, and I'll find the most relevant papers for you.",
            author="Assistant"
        ).send()
    except Exception as e:
        await cl.Message(
            content=f"⚠️ Error initializing: {str(e)}\n\nPlease make sure Ollama is running: `ollama serve`",
            author="System"
        ).send()

@cl.on_message
async def main(message: cl.Message):
    """Handle user messages"""
    try:
        user_query = message.content
        
        # Create response message
        msg = cl.Message(content="")
        await msg.send()
        
        # Step 1: Refine query with LLM
        await msg.stream_token("🔍 Understanding your query...\n\n")
        
        try:
            refined = llm.refine_query(user_query)
            await msg.stream_token(f"✨ Refined query parameters extracted\n\n")
        except Exception as e:
            await msg.stream_token(f"⚠️ Query refinement skipped: {str(e)}\n\n")
            refined = {"main_topic": user_query}
        
        # Step 2: Search papers
        await msg.stream_token("📚 Searching across arXiv and Semantic Scholar...\n\n")
        
        try:
            papers = search_agent.search(user_query, max_results=10)
            await msg.stream_token(f"Found {len(papers)} papers\n\n")
        except Exception as e:
            await msg.stream_token(f"⚠️ Search error: {str(e)}\n\n")
            await msg.update()
            return
        
        if not papers:
            await msg.stream_token("😕 No papers found. Try a different query.\n\n")
            await msg.update()
            return
        
        # Step 3: Semantic ranking
        await msg.stream_token("🎯 Ranking by relevance...\n\n")
        
        try:
            ranked_papers = search_agent.semantic_search(user_query, k=min(10, len(papers)))
        except Exception as e:
            await msg.stream_token(f"⚠️ Ranking error: {str(e)}\n\nShowing unranked results:\n\n")
            ranked_papers = [{'metadata': p, 'similarity': 0.5} for p in papers[:5]]
        
        # Format results
        response = f"**Found {len(ranked_papers)} highly relevant papers:**\n\n"
        
        for i, result in enumerate(ranked_papers[:5], 1):
            paper = result['metadata']
            similarity = result.get('similarity', 0) * 100
            
            response += f"**{i}. {paper.get('title', 'Untitled')}**\n"
            response += f"*{paper.get('authors', 'Unknown authors')} ({paper.get('year', 'N/A')})*\n"
            response += f"📊 {similarity:.0f}% match | 📖 {paper.get('citations', 0)} citations | 🏛️ {paper.get('venue', 'N/A')}\n"
            
            if paper.get('url'):
                response += f"🔗 [View Paper]({paper['url']})"
            if paper.get('pdf_url'):
                response += f" | [PDF]({paper['pdf_url']})"
            
            response += "\n\n"
        
        await msg.stream_token(response)
        await msg.update()
        
    except Exception as e:
        error_msg = f"❌ An error occurred: {str(e)}\n\nPlease try again or rephrase your query."
        await cl.Message(content=error_msg).send()

if __name__ == "__main__":
    from chainlit.cli import run_chainlit
    run_chainlit(__file__)