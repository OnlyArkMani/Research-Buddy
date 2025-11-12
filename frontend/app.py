import chainlit as cl
import sys
from pathlib import Path
import os

sys.path.append(str(Path(__file__).parent.parent / "backend"))

from models.llm import MistralLLM
from models.gemini_client import GeminiClient
from agents.search_agent import SearchAgent
from utils.filter_manager import FilterManager
from utils.summarizer import PaperSummarizer
from utils.citation_generator import CitationGenerator
from config import GEMINI_API_KEY, DEFAULT_USERNAME

# Initialize components
llm = None
gemini = None
search_agent = None
filter_manager = None
summarizer = None
user_name = DEFAULT_USERNAME

@cl.on_chat_start
async def start():
    """Welcome message with user name"""
    global llm, gemini, search_agent, filter_manager, summarizer, user_name
    
    # Ask for user name
    res = await cl.AskUserMessage(
        content="Welcome to **Research Buddy**! 🔬\n\nWhat should I call you?",
        timeout=30
    ).send()
    
    if res:
        user_name = res['output'].strip() or DEFAULT_USERNAME
        cl.user_session.set("user_name", user_name)
    
    try:
        # Initialize components
        llm = MistralLLM()
        if GEMINI_API_KEY:
            gemini = GeminiClient(GEMINI_API_KEY)
        search_agent = SearchAgent()
        filter_manager = FilterManager()
        summarizer = PaperSummarizer(gemini, llm)
        
        # Store in session
        cl.user_session.set("filter_manager", filter_manager)
        cl.user_session.set("summarizer", summarizer)
        cl.user_session.set("search_agent", search_agent)
        
        welcome_msg = f"""# Hello, {user_name}! 👋

Welcome to **Research Buddy** - Your AI-Powered Research Assistant! 🚀

## 🎯 What I Can Do:

### 📚 **Smart Paper Discovery**
- Find 50+ papers from arXiv, Semantic Scholar, PubMed
- Intelligent ranking by relevance, citations & recency

### 🔍 **Advanced Filtering**
- Filter by year: "papers after 2020"
- Filter by citations: "highly cited papers on..."
- Filter by domain: "ML papers in medicine"

### 📝 **AI Summarization**
- Get concise 3-sentence summaries
- Request detailed explanations
- Compare multiple papers

### 💾 **Bookmark & Organize**
- Save papers: "bookmark paper 1"
- Create collections: "create collection ML Papers"
- View saved: "show my bookmarks"

### 📚 **Citation Generator**
- Generate citations: "cite paper 1"
- Multiple formats: APA, IEEE, MLA, BibTeX

## 💡 **Try These Commands:**

**Search:**
- "Find papers on biometric detection using ML and DL models"
- "Recent papers on transformers after 2022"
- "Highly cited research on quantum computing"

**Summarize:**
- "Summarize paper 1" (after search results)
- "Give me key points from paper 3"
- "Detailed summary of paper 2"

**Organize:**
- "Bookmark paper 1"
- "Create collection Deep Learning"
- "Show my bookmarks"
- "Add paper 2 to Deep Learning collection"

**Filter:**
- "Show only papers after 2020"
- "Papers with more than 100 citations"
- "Clear filters"

**Citation:**
- "Cite paper 1"
- "Generate IEEE citation for paper 2"

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
    global user_name
    
    user_name = cl.user_session.get("user_name")
    filter_manager = cl.user_session.get("filter_manager")
    summarizer = cl.user_session.get("summarizer")
    search_agent = cl.user_session.get("search_agent")
    
    try:
        user_query = message.content.lower()
        
        # Route to appropriate handler
        if any(word in user_query for word in ['cite', 'citation', 'reference']):
            await handle_citation_request(message.content)
        
        elif any(word in user_query for word in ['bookmark', 'save', 'collection', 'show my']):
            await handle_bookmark_commands(message.content, user_name, search_agent)
        
        elif any(word in user_query for word in ['summarize', 'summary', 'explain', 'key points']):
            await handle_summarization(message.content, summarizer)
        
        elif any(word in user_query for word in ['filter', 'show only', 'after', 'before', 'clear filter']):
            await handle_filter_commands(message.content, filter_manager)
        
        else:
            # Standard research paper search
            await handle_paper_search(message.content, user_name, search_agent, filter_manager, summarizer)
        
    except Exception as e:
        error_msg = f"❌ **Error**: {str(e)}\n\nPlease try again or rephrase your query."
        await cl.Message(content=error_msg).send()


async def handle_paper_search(query: str, user_name: str, search_agent, filter_manager, summarizer):
    """Handle paper search with filters"""
    msg = cl.Message(content="")
    await msg.send()
    
    # Parse filter from query
    auto_filters = filter_manager.parse_filter_from_query(query)
    if auto_filters:
        for key, value in auto_filters.items():
            filter_manager.set_filter(key, value)
        await msg.stream_token(f"🔍 **Auto-detected filters**: {filter_manager.get_active_filters_summary()}\n\n")
    
    await msg.stream_token(f"🔍 **Searching for: {query}**\n\n")
    
    # Search
    try:
        papers = search_agent.search(query, max_results=50)
        
        # Apply filters
        if any(filter_manager.active_filters.values()):
            filtered_papers = filter_manager.apply_filters(papers)
            await msg.stream_token(f"✅ Found {len(papers)} papers, {len(filtered_papers)} after filtering\n\n")
            papers = filtered_papers
        else:
            await msg.stream_token(f"✅ Found {len(papers)} papers\n\n")
        
        if not papers:
            await msg.stream_token("😕 **No papers found**. Try adjusting filters or rephrasing.\n\n")
            await msg.update()
            return
        
        # Rank
        await msg.stream_token("🎯 **Ranking by relevance...**\n\n")
        ranked_papers = search_agent.semantic_search(query, k=min(50, len(papers)))
        
        # Store in session for later commands
        cl.user_session.set("last_search_results", ranked_papers)
        
        # Format results
        response = f"# 🎓 Top {min(20, len(ranked_papers))} Research Papers\n\n"
        
        if any(filter_manager.active_filters.values()):
            response += f"**Active Filters:**\n{filter_manager.get_active_filters_summary()}\n\n"
        
        response += "---\n\n"
        
        for i, result in enumerate(ranked_papers[:20], 1):
            paper = result['metadata']
            score = result.get('final_score', result.get('similarity', 0)) * 100
            
            response += f"### {i}. {paper.get('title', 'Untitled')}\n\n"
            response += f"**Authors**: {paper.get('authors', 'Unknown')}\n\n"
            response += f"**Year**: {paper.get('year', 'N/A')} | "
            response += f"**Citations**: {paper.get('citations', 0)} | "
            response += f"**Source**: {paper.get('source', 'N/A')}\n\n"
            response += f"**Relevance**: {score:.1f}%\n\n"
            
            # Quick actions
            response += f"💡 *Say \"summarize paper {i}\" or \"bookmark paper {i}\"*\n\n"
            
            if paper.get('url'):
                response += f"[📄 View]({paper['url']})"
            if paper.get('pdf_url'):
                response += f" | [📥 PDF]({paper['pdf_url']})"
            
            response += "\n\n---\n\n"
        
        await msg.stream_token(response)
        await msg.update()
        
    except Exception as e:
        await msg.stream_token(f"❌ Search error: {str(e)}\n\n")
        await msg.update()


async def handle_summarization(query: str, summarizer):
    """Handle summarization requests"""
    msg = cl.Message(content="")
    await msg.send()
    
    # Extract paper number
    import re
    match = re.search(r'paper (\d+)', query.lower())
    
    if not match:
        await msg.stream_token("❌ Please specify paper number (e.g., 'summarize paper 1')\n\n")
        await msg.update()
        return
    
    paper_num = int(match.group(1))
    results = cl.user_session.get("last_search_results", [])
    
    if not results or paper_num > len(results):
        await msg.stream_token("❌ Paper not found. Please search first.\n\n")
        await msg.update()
        return
    
    paper = results[paper_num - 1]['metadata']
    
    # Determine summary style
    if 'detailed' in query:
        style = 'detailed'
    elif 'key points' in query or 'bullet' in query:
        style = 'key-points'
    else:
        style = 'concise'
    
    await msg.stream_token(f"📝 **Generating {style} summary for Paper {paper_num}...**\n\n")
    await msg.stream_token(f"**Title**: {paper.get('title')}\n\n")
    
    summary = summarizer.summarize_paper(paper, style)
    
    await msg.stream_token(f"**Summary**:\n{summary}\n\n")
    await msg.stream_token(f"---\n\n💡 *Try: \"bookmark paper {paper_num}\" to save this paper*")
    
    await msg.update()


async def handle_bookmark_commands(query: str, user_name: str, search_agent):
    """Handle bookmark operations"""
    msg = cl.Message(content="")
    await msg.send()
    
    db = search_agent.db
    
    # Show bookmarks
    if 'show' in query or 'view' in query or 'my bookmarks' in query:
        bookmarks = db.get_bookmarks(user_name)
        
        if not bookmarks:
            await msg.stream_token("📚 **No bookmarks yet!**\n\nBookmark papers using: \"bookmark paper 1\"\n\n")
        else:
            response = f"# 📚 {user_name}'s Bookmarked Papers\n\n"
            response += f"*{len(bookmarks)} papers saved*\n\n---\n\n"
            
            for i, paper in enumerate(bookmarks, 1):
                response += f"### {i}. {paper.get('title')}\n\n"
                response += f"**Collection**: {paper.get('collection_name', 'default')}\n\n"
                if paper.get('notes'):
                    response += f"**Notes**: {paper['notes']}\n\n"
                response += f"**Saved**: {paper.get('bookmarked_at')}\n\n"
                response += "---\n\n"
            
            await msg.stream_token(response)
        
        await msg.update()
        return
    
    # Create collection
    if 'create collection' in query:
        import re
        match = re.search(r'create collection (.+)', query.lower())
        if match:
            collection_name = match.group(1).strip()
            success = db.create_collection(user_name, collection_name)
            if success:
                await msg.stream_token(f"✅ **Collection '{collection_name}' created!**\n\n")
            else:
                await msg.stream_token(f"❌ Collection already exists or error occurred.\n\n")
        await msg.update()
        return
    
    # Bookmark paper
    import re
    match = re.search(r'paper (\d+)', query.lower())
    
    if not match:
        await msg.stream_token("❌ Please specify paper number (e.g., 'bookmark paper 1')\n\n")
        await msg.update()
        return
    
    paper_num = int(match.group(1))
    results = cl.user_session.get("last_search_results", [])
    
    if not results or paper_num > len(results):
        await msg.stream_token("❌ Paper not found. Please search first.\n\n")
        await msg.update()
        return
    
    paper = results[paper_num - 1]['metadata']
    
    # Extract collection name if specified
    collection = "default"
    collection_match = re.search(r'to (.+) collection', query.lower())
    if collection_match:
        collection = collection_match.group(1).strip()
    
    success = db.add_bookmark(user_name, paper.get('id'), collection)
    
    if success:
        await msg.stream_token(f"✅ **Paper bookmarked successfully!**\n\n")
        await msg.stream_token(f"📌 **Title**: {paper.get('title')}\n\n")
        await msg.stream_token(f"📁 **Collection**: {collection}\n\n")
        await msg.stream_token(f"💡 *View all bookmarks: \"show my bookmarks\"*\n\n")
    else:
        await msg.stream_token("❌ Error saving bookmark.\n\n")
    
    await msg.update()


async def handle_filter_commands(query: str, filter_manager):
    """Handle filter operations"""
    msg = cl.Message(content="")
    await msg.send()
    
    # Clear filters
    if 'clear filter' in query.lower():
        filter_manager.clear_filters()
        await msg.stream_token("✅ **All filters cleared!**\n\n")
        await msg.update()
        return
    
    # Show active filters
    if 'show filter' in query.lower():
        summary = filter_manager.get_active_filters_summary()
        await msg.stream_token(f"## 🔍 Active Filters\n\n{summary}\n\n")
        await msg.update()
        return
    
    # Parse and set filters
    import re
    
    # Year filters
    year_after = re.search(r'after (\d{4})', query.lower())
    year_before = re.search(r'before (\d{4})', query.lower())
    year_range = re.search(r'(\d{4})-(\d{4})', query.lower())
    
    if year_after:
        year = int(year_after.group(1))
        filter_manager.set_filter('min_year', year)
        await msg.stream_token(f"✅ Filter set: Papers from {year} onwards\n\n")
    
    if year_before:
        year = int(year_before.group(1))
        filter_manager.set_filter('max_year', year)
        await msg.stream_token(f"✅ Filter set: Papers before {year}\n\n")
    
    if year_range:
        min_year = int(year_range.group(1))
        max_year = int(year_range.group(2))
        filter_manager.set_filter('min_year', min_year)
        filter_manager.set_filter('max_year', max_year)
        await msg.stream_token(f"✅ Filter set: Papers from {min_year} to {max_year}\n\n")
    
    # Citation filters
    min_citations = re.search(r'more than (\d+) citations?', query.lower())
    highly_cited = 'highly cited' in query.lower()
    
    if min_citations:
        citations = int(min_citations.group(1))
        filter_manager.set_filter('min_citations', citations)
        await msg.stream_token(f"✅ Filter set: Minimum {citations} citations\n\n")
    elif highly_cited:
        filter_manager.set_filter('min_citations', 100)
        await msg.stream_token(f"✅ Filter set: Highly cited papers (100+ citations)\n\n")
    
    # Recent papers
    if 'recent' in query.lower() or 'latest' in query.lower():
        from datetime import datetime
        current_year = datetime.now().year
        filter_manager.set_filter('min_year', current_year - 3)
        await msg.stream_token(f"✅ Filter set: Papers from last 3 years\n\n")
    
    await msg.stream_token(f"**Current Filters:**\n{filter_manager.get_active_filters_summary()}\n\n")
    await msg.stream_token(f"💡 *Now search for papers to apply these filters!*\n\n")
    
    await msg.update()


async def handle_citation_request(query: str):
    """Handle citation generation requests"""
    msg = cl.Message(content="")
    await msg.send()
    
    # Extract paper number
    import re
    match = re.search(r'paper (\d+)', query.lower())
    
    if not match:
        await msg.stream_token("❌ Please specify paper number (e.g., 'cite paper 1 in APA')\n\n")
        await msg.update()
        return
    
    paper_num = int(match.group(1))
    results = cl.user_session.get("last_search_results", [])
    
    if not results or paper_num > len(results):
        await msg.stream_token("❌ Paper not found. Please search first.\n\n")
        await msg.update()
        return
    
    paper = results[paper_num - 1]['metadata']
    
    # Determine citation format
    if 'apa' in query.lower():
        citation = CitationGenerator.generate_apa(paper)
        format_name = "APA"
    elif 'ieee' in query.lower():
        citation = CitationGenerator.generate_ieee(paper)
        format_name = "IEEE"
    elif 'mla' in query.lower():
        citation = CitationGenerator.generate_mla(paper)
        format_name = "MLA"
    elif 'bibtex' in query.lower():
        citation = CitationGenerator.generate_bibtex(paper)
        format_name = "BibTeX"
    else:
        # Show all formats
        citations = CitationGenerator.generate_all_formats(paper)
        response = f"## 📚 Citations for Paper {paper_num}\n\n"
        response += f"**Title**: {paper.get('title')}\n\n---\n\n"
        
        for format_name, citation in citations.items():
            response += f"### {format_name}\n```\n{citation}\n```\n\n"
        
        await msg.stream_token(response)
        await msg.update()
        return
    
    response = f"## 📚 {format_name} Citation for Paper {paper_num}\n\n"
    response += f"**Title**: {paper.get('title')}\n\n"
    response += f"```\n{citation}\n```\n\n"
    response += f"💡 *Try: \"cite paper {paper_num} in [APA/IEEE/MLA/BibTeX]\"*"
    
    await msg.stream_token(response)
    await msg.update()


if __name__ == "__main__":
    from chainlit.cli import run_chainlit
    run_chainlit(__file__)