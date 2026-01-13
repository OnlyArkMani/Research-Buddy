 `# Research Buddy

An AI-powered research assistant that helps researchers discover, organize, and analyze academic papers across multiple sources using advanced natural language processing and semantic search capabilities.

## Overview

Research Buddy is a comprehensive research management platform that combines multi-source paper discovery, intelligent ranking, AI-powered summarization, and personal organization features. It leverages state-of-the-art language models and semantic search to help researchers efficiently navigate the vast landscape of academic literature.

## Key Features

### Multi-Source Paper Discovery
- Searches across arXiv, Semantic Scholar, and PubMed simultaneously
- Retrieves up to 50+ papers per query with intelligent deduplication
- Parallel processing for fast results across multiple academic databases

### Intelligent Ranking System
- Semantic search using sentence transformers for relevance scoring
- Citation-based ranking to prioritize influential papers
- Recency weighting to surface the latest research
- Combined scoring algorithm balancing multiple factors

### AI-Powered Analysis
- Integration with Google Gemini and local Mistral LLM models
- Three summarization styles: concise, detailed, and key-points
- Query refinement for improved search accuracy
- Natural language understanding for complex research queries

### Advanced Filtering
- Filter by publication year range
- Minimum citation thresholds
- Research domain categorization
- Auto-detection of filters from natural language queries

### Personal Organization
- Bookmark system for saving important papers
- Custom collections for organizing research by topic
- User-specific storage and retrieval
- Notes and annotations support

### Citation Management
- Multiple citation format support: APA, IEEE, MLA, BibTeX
- One-click citation generation
- Export capabilities for reference managers

### Interactive Web Interface
- Built with Chainlit for conversational AI interaction
- Real-time search and streaming responses
- Firebase authentication with Google Sign-In
- Session management with JWT tokens
- Mobile-responsive design

## Architecture

### Backend Components

**Agents**
- Search Agent: Coordinates multi-source searches and semantic ranking
- Query refinement and result processing

**Models**
- Mistral LLM: Local language model for query processing
- Gemini Client: Cloud-based AI for advanced summarization
- Embedding Model: Sentence transformers for semantic search

**Database**
- SQLite: Paper metadata and bookmark storage
- FAISS: Vector store for semantic similarity search
- Redis support: Optional distributed caching

**Utilities**
- Multi-source API clients for academic databases
- Filter manager for advanced query filtering
- Citation generator for multiple formats
- PDF processing and text extraction

### Frontend

- Chainlit-based conversational interface
- Flask landing page with authentication
- Static assets for responsive design
- Firebase integration for user management

## Technology Stack

**Core LLM & AI**
- Ollama (Mistral 7B)
- Google Generative AI (Gemini)
- Sentence Transformers
- LangChain & LangGraph

**Search & APIs**
- arXiv API
- Semantic Scholar API
- PubMed/NCBI Biopython
- REST API clients with aiohttp

**Vector Storage & Embeddings**
- FAISS for similarity search
- ChromaDB support
- all-MiniLM-L6-v2 embeddings

**PDF & Document Processing**
- PyMuPDF for PDF parsing
- PyPDF for text extraction
- python-docx for Word export
- nbformat for Jupyter notebooks

**Web Framework**
- Chainlit for chat interface
- Flask for landing page
- Firebase Authentication
- CORS support

**Data Processing**
- NumPy and Pandas
- NetworkX for graph visualization
- Plotly and Matplotlib for charts

## Installation

### Prerequisites

- Python 3.8 or higher
- Ollama installed and running
- Firebase project (for authentication)
- Google Gemini API key (optional, for enhanced features)

### Setup Steps

1. Clone the repository:
```bash
git clone <repository-url>
cd ResearchBuddy
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements_landing.txt
```

4. Configure environment variables:

Create a `.env` file in the project root:
```env
# LLM Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Semantic Scholar (Optional)
SEMANTIC_SCHOLAR_API_KEY=your_semantic_scholar_key

# Firebase Configuration
FIREBASE_API_KEY=your_firebase_api_key
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_STORAGE_BUCKET=your-project.appspot.com
FIREBASE_MESSAGING_SENDER_ID=your_sender_id
FIREBASE_APP_ID=your_app_id

# JWT Secret (auto-generated if not provided)
JWT_SECRET=your_jwt_secret_here

# User Settings
DEFAULT_USERNAME=Researcher
```

5. Start Ollama server:
```bash
ollama serve
ollama pull mistral:7b
```

6. Initialize the database:
```bash
python backend/main.py
```

## Usage

### Starting the Application

1. Start the landing page server:
```bash
python landing_server.py
```

2. In a separate terminal, start the Chainlit interface:
```bash
chainlit run frontend/app.py
```

3. Access the application:
- Landing page: http://localhost:5000
- Chat interface: http://localhost:8000

### Basic Commands

**Search for Papers**
```
Find papers on biometric detection using ML and DL models
Recent papers on transformers after 2022
Highly cited research on quantum computing
```

**Summarize Papers**
```
Summarize paper 1
Give me key points from paper 3
Detailed summary of paper 2
```

**Organize Papers**
```
Bookmark paper 1
Create collection Deep Learning
Show my bookmarks
Add paper 2 to Deep Learning collection
```

**Filter Results**
```
Show only papers after 2020
Papers with more than 100 citations
Clear filters
```

**Generate Citations**
```
Cite paper 1
Generate IEEE citation for paper 2
Cite paper 3 in BibTeX format
```

## Project Structure

```
ResearchBuddy/
├── backend/
│   ├── agents/           # Search and processing agents
│   ├── database/         # SQLite and vector storage
│   ├── models/           # LLM and embedding models
│   ├── utils/            # Helper utilities and API clients
│   ├── config.py         # Configuration management
│   └── main.py           # Backend entry point
├── frontend/
│   └── app.py            # Chainlit chat interface
├── templates/            # HTML templates for landing page
├── static/               # CSS and JavaScript assets
├── cache/                # Local cache for papers and PDFs
├── .env                  # Environment variables
├── requirements.txt      # Python dependencies
├── landing_server.py     # Flask authentication server
└── quick_setup.py        # Quick setup utility
```

## Configuration

### LLM Settings

Modify `backend/config.py` to adjust:
- Ollama model selection
- API endpoints and ports
- Embedding model configuration
- Search result limits

### Search Parameters

```python
MAX_RESULTS_PER_SOURCE = 20  # Papers per source
TOTAL_SOURCES = 5            # Number of sources to query
TARGET_PAPERS = 50           # Total papers to retrieve
```

### Performance Tuning

```python
ENABLE_PARALLEL_SEARCH = True   # Parallel API calls
ENABLE_SMART_CACHING = True     # Cache search results
CACHE_EXPIRY_DAYS = 7           # Cache duration
```

## API Integration

### Supported Sources

- **arXiv**: Open access preprints in physics, math, CS, and more
- **Semantic Scholar**: AI-powered academic search engine
- **PubMed**: Biomedical and life sciences literature

### Adding Custom Sources

Extend `backend/utils/api_clients.py` to add new academic databases:

```python
class CustomSourceClient:
    def search(self, query: str, max_results: int = 20):
        # Implement search logic
        pass
```

## Database Schema

### Papers Table
- id, title, authors, year, abstract
- url, pdf_url, source, citations
- created_at

### Bookmarks Table
- id, user_id, paper_id, collection_id
- notes, bookmarked_at

### Collections Table
- id, user_id, name, description
- created_at

## Authentication Flow

1. User visits landing page
2. Firebase authentication (Google or Email)
3. JWT token generation
4. Session creation with 7-day persistence
5. Secure redirect to Chainlit interface
6. User context maintained across sessions

## Performance Optimization

### Caching Strategy
- FAISS indexes for fast similarity search
- SQLite for persistent metadata storage
- Optional Redis for distributed caching

### Batch Processing
- Embeddings generated in batches
- Parallel API requests across sources
- Efficient deduplication algorithms

### Resource Management
- Lazy loading of models
- Connection pooling for databases
- Memory-efficient vector operations

## Troubleshooting

### Common Issues

**Ollama Connection Error**
- Ensure Ollama is running: `ollama serve`
- Check port 11434 is not blocked
- Verify model is pulled: `ollama pull mistral:7b`

**Firebase Authentication Fails**
- Verify `.env` configuration
- Check Firebase project settings
- Ensure authorized domains include localhost

**Search Returns No Results**
- Check API keys in `.env`
- Verify internet connectivity
- Try broader search terms

**Embedding Generation Slow**
- First run downloads model (one-time)
- Consider GPU acceleration
- Reduce batch size in config

## Contributing

Contributions are welcome. Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes with clear commit messages
4. Add tests for new functionality
5. Submit a pull request with description

## License

This project is provided as-is for research and educational purposes.

## Acknowledgments

- Chainlit for the conversational AI framework
- Anthropic Claude for development assistance
- Open-source academic APIs for data access
- Contributors to the various Python libraries used

## Support

For issues, questions, or feature requests, please open an issue on the project repository.

## Roadmap

### Planned Features
- Multi-language paper support
- Export to reference managers (Zotero, Mendeley)
- Collaborative collections and sharing
- Advanced analytics and visualization
- Mobile application
- Browser extension for quick lookups
- Integration with more academic databases
- Machine learning model fine-tuning

### Under Development
- Enhanced PDF processing with OCR
- Automated literature review generation
- Citation network visualization
- Research trend analysis
- Personalized recommendations


##Author 
Ark Mani 
arkmanimishra@gmail.com


