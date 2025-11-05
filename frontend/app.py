import chainlit as cl
import sys
from pathlib import Path
import os

sys.path.append(str(Path(__file__).parent.parent / "backend"))

from models.llm import MistralLLM
from models.gemini_client import GeminiClient
from agents.search_agent import SearchAgent
from config import GEMINI_API_KEY, DEFAULT_USERNAME

# Initialize components
llm = None
gemini = None
search_agent = None
user_name = DEFAULT_USERNAME

@cl.on_chat_start
async def start():
    """Welcome message with user name"""
    global llm, gemini, search_agent, user_name
    
    # Ask for user name
    res = await cl.AskUserMessage(
        content="Welcome to **Research Buddy**! 🔬\n\nWhat should I call you?",
        timeout=30
    ).send()
    
    if res:
        user_name = res['output'].strip() or DEFAULT_USERNAME
    
    try:
        # Initialize components
        llm = MistralLLM()
        if GEMINI_API_KEY:
            gemini = GeminiClient(GEMINI_API_KEY)
        search_agent = SearchAgent()
        
        welcome_msg = f"""# Hello, {user_name}! 👋

Welcome to **Research Buddy** - Your AI-Powered Research Assistant! 🚀

I can help you:
- 🔍 **Find research papers** across arXiv, Semantic Scholar, PubMed & more
- 📊 **Discover 50+ relevant papers** for any research topic
- 💡 **Answer questions** about research concepts
- 🎯 **Get personalized recommendations** based on your interests

**Try asking:**
- "Find papers on biometric detection using ML and DL models"
- "Latest research on transformer architectures"
- "What is federated learning?"

*Let's discover groundbreaking research together!* ✨
"""
        
        await cl.Message(content=welcome_msg).send()
        
    except Exception as e:
        await cl.Message(
            content=f"⚠️ **Initialization Error**: {str(e)}\n\nPlease ensure:\n- Ollama is running (`ollama serve`)\n- Gemini API key is set (optional)"
        ).send()

@cl.on_message
async def main(message: cl.Message):
    """Handle user messages with intelligent routing"""
    global user_name, gemini, search_agent
    
    try:
        user_query = message.content
        
        # Determine if it's a research query or general chat
        is_research = gemini.is_research_query(user_query) if gemini else True
        
        if not is_research and gemini:
            # Handle general chat with Gemini
            response = gemini.chat(user_query)
            await cl.Message(content=response).send()
            return
        
        # Research paper search
        msg = cl.Message(content="")
        await msg.send()
        
        # Step 1: Query refinement
        await msg.stream_token(f"🔍 **Understanding your research interest, {user_name}...**\n\n")
        
        try:
            if gemini:
                refined = gemini.refine_query(user_query)
                await msg.stream_token(f"✨ **Query Enhanced**: Found {len(refined.get('keywords', []))} key terms\n\n")
            else:
                refined = {"main_topic": user_query}
        except Exception as e:
            await msg.stream_token(f"⚠️ Using original query\n\n")
            refined = {"main_topic": user_query}
        
        # Step 2: Multi-source search
        await msg.stream_token("📚 **Searching across arXiv, Semantic Scholar, PubMed...**\n\n")
        
        try:
            papers = search_agent.search(user_query, max_results=50)
            await msg.stream_token(f"✅ **Retrieved {len(papers)} papers** from multiple sources\n\n")
        except Exception as e:
            await msg.stream_token(f"❌ **Search error**: {str(e)}\n\n")
            await msg.update()
            return
        
        if not papers:
            await msg.stream_token("😕 **No papers found**. Try rephrasing your query.\n\n")
            await msg.update()
            return
        
        # Step 3: Semantic ranking
        await msg.stream_token("🎯 **Ranking by relevance, citations & recency...**\n\n")
        
        try:
            ranked_papers = search_agent.semantic_search(user_query, k=min(50, len(papers)))
        except Exception as e:
            await msg.stream_token(f"⚠️ Showing unranked results\n\n")
            ranked_papers = [{'metadata': p, 'similarity': 0.5, 'final_score': 0.5} for p in papers[:20]]
        
        # Format results
        response = f"# 🎓 Top {min(20, len(ranked_papers))} Research Papers for {user_name}\n\n"
        response += f"*Showing results from {len(set([p['metadata'].get('source') for p in ranked_papers]))} sources*\n\n"
        response += "---\n\n"
        
        for i, result in enumerate(ranked_papers[:20], 1):
            paper = result['metadata']
            score = result.get('final_score', result.get('similarity', 0)) * 100
            
            response += f"### {i}. {paper.get('title', 'Untitled')}\n\n"
            response += f"**Authors**: {paper.get('authors', 'Unknown')}\n\n"
            response += f"**Year**: {paper.get('year', 'N/A')} | "
            response += f"**Citations**: {paper.get('citations', 0)} | "
            response += f"**Source**: {paper.get('source', 'N/A')}\n\n"
            response += f"**Relevance Score**: {score:.1f}%\n\n"
            
            if paper.get('abstract'):
                abstract = paper['abstract'][:200] + "..." if len(paper.get('abstract', '')) > 200 else paper.get('abstract', '')
                response += f"*{abstract}*\n\n"
            
            links = []
            if paper.get('url'):
                links.append(f"[📄 View Paper]({paper['url']})")
            if paper.get('pdf_url'):
                links.append(f"[📥 PDF]({paper['pdf_url']})")
            
            if links:
                response += " | ".join(links) + "\n\n"
            
            response += "---\n\n"
        
        response += f"\n\n💡 **Tip**: Want to explore more? Ask about specific papers or refine your search!"
        
        await msg.stream_token(response)
        await msg.update()
        
    except Exception as e:
        error_msg = f"❌ **Error**: {str(e)}\n\nPlease try again or rephrase your query."
        await cl.Message(content=error_msg).send()

if __name__ == "__main__":
    from chainlit.cli import run_chainlit
    run_chainlit(__file__)