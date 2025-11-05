import sqlite3
from datetime import datetime
from typing import List, Dict, Optional

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

class PaperDatabase:
    def __init__(self, db_path: str = "cache/papers.db"):
        """Initialize SQLite database"""
        # Create cache directory if it doesn't exist
        cache_dir = Path(db_path).parent
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._create_tables()
    
    def _create_tables(self):
        """Create database schema"""
        cursor = self.conn.cursor()
        
        # Papers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS papers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paper_id TEXT UNIQUE,
                title TEXT NOT NULL,
                authors TEXT,
                abstract TEXT,
                year INTEGER,
                venue TEXT,
                citations INTEGER DEFAULT 0,
                url TEXT,
                pdf_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Query history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS query_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                refined_query TEXT,
                results_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
    
    def add_paper(self, paper: Dict) -> int:
        """Add or update paper"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO papers 
            (paper_id, title, authors, abstract, year, venue, citations, url, pdf_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            paper.get('id'),
            paper['title'],
            paper.get('authors'),
            paper.get('abstract'),
            paper.get('year'),
            paper.get('venue'),
            paper.get('citations', 0),
            paper.get('url'),
            paper.get('pdf_url')
        ))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def search_papers(self, query: str, limit: int = 20) -> List[Dict]:
        """Search papers by title/abstract"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT * FROM papers 
            WHERE title LIKE ? OR abstract LIKE ?
            ORDER BY citations DESC
            LIMIT ?
        ''', (f'%{query}%', f'%{query}%', limit))
        
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def log_query(self, query: str, refined_query: str, results_count: int):
        """Log user query"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO query_history (query, refined_query, results_count)
            VALUES (?, ?, ?)
        ''', (query, refined_query, results_count))
        self.conn.commit()