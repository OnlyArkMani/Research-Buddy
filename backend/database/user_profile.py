import sqlite3
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
import json

class UserProfileManager:
    """Manages user profiles, preferences, and conversation history"""
    
    def __init__(self, db_path: str = "cache/user_profiles.db"):
        cache_dir = Path(db_path).parent
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._create_tables()
    
    def _create_tables(self):
        cursor = self.conn.cursor()
        
        # User profiles
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT,
                research_domains TEXT,  -- JSON array
                favorite_authors TEXT,  -- JSON array
                preferred_sources TEXT, -- JSON array
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Conversation history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,  -- 'user' or 'assistant'
                content TEXT NOT NULL,
                metadata TEXT,  -- JSON
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user_profiles (user_id)
            )
        ''')
        
        # User preferences
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id TEXT PRIMARY KEY,
                summary_style TEXT DEFAULT 'concise',
                citation_format TEXT DEFAULT 'APA',
                results_per_page INTEGER DEFAULT 20,
                enable_notifications BOOLEAN DEFAULT 1,
                theme TEXT DEFAULT 'dark',
                FOREIGN KEY (user_id) REFERENCES user_profiles (user_id)
            )
        ''')
        
        # Search history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                query TEXT NOT NULL,
                results_count INTEGER,
                filters_applied TEXT,  -- JSON
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user_profiles (user_id)
            )
        ''')
        
        self.conn.commit()
    
    def create_or_update_profile(self, user_id: str, name: str, **kwargs) -> bool:
        """Create or update user profile"""
        try:
            cursor = self.conn.cursor()
            
            research_domains = json.dumps(kwargs.get('research_domains', []))
            favorite_authors = json.dumps(kwargs.get('favorite_authors', []))
            preferred_sources = json.dumps(kwargs.get('preferred_sources', []))
            
            cursor.execute('''
                INSERT OR REPLACE INTO user_profiles 
                (user_id, name, email, research_domains, favorite_authors, preferred_sources, last_active)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, name, kwargs.get('email'), research_domains, favorite_authors, preferred_sources))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Profile error: {e}")
            return False
    
    def get_profile(self, user_id: str) -> Optional[Dict]:
        """Get user profile"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM user_profiles WHERE user_id = ?', (user_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        columns = [desc[0] for desc in cursor.description]
        profile = dict(zip(columns, row))
        
        # Parse JSON fields
        profile['research_domains'] = json.loads(profile.get('research_domains', '[]'))
        profile['favorite_authors'] = json.loads(profile.get('favorite_authors', '[]'))
        profile['preferred_sources'] = json.loads(profile.get('preferred_sources', '[]'))
        
        return profile
    
    def add_conversation_message(self, user_id: str, session_id: str, role: str, content: str, metadata: Dict = None):
        """Add message to conversation history"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO conversation_history (user_id, session_id, role, content, metadata)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, session_id, role, content, json.dumps(metadata or {})))
        self.conn.commit()
    
    def get_conversation_history(self, user_id: str, session_id: str, limit: int = 10) -> List[Dict]:
        """Get recent conversation history"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT role, content, metadata, created_at
            FROM conversation_history
            WHERE user_id = ? AND session_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, session_id, limit))
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                'role': row[0],
                'content': row[1],
                'metadata': json.loads(row[2]),
                'timestamp': row[3]
            })
        
        return list(reversed(messages))
    
    def add_search_to_history(self, user_id: str, query: str, results_count: int, filters: Dict = None):
        """Log search query"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO search_history (user_id, query, results_count, filters_applied)
            VALUES (?, ?, ?, ?)
        ''', (user_id, query, results_count, json.dumps(filters or {})))
        self.conn.commit()
    
    def get_search_history(self, user_id: str, limit: int = 20) -> List[Dict]:
        """Get user's search history"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT query, results_count, filters_applied, created_at
            FROM search_history
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit))
        
        columns = ['query', 'results_count', 'filters_applied', 'created_at']
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_personalized_suggestions(self, user_id: str) -> Dict:
        """Get personalized research suggestions based on history"""
        profile = self.get_profile(user_id)
        search_history = self.get_search_history(user_id, limit=10)
        
        # Extract common topics from search history
        common_terms = {}
        for search in search_history:
            words = search['query'].lower().split()
            for word in words:
                if len(word) > 4:  # Skip short words
                    common_terms[word] = common_terms.get(word, 0) + 1
        
        # Sort by frequency
        trending_topics = sorted(common_terms.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'research_domains': profile.get('research_domains', []) if profile else [],
            'trending_topics': [topic[0] for topic in trending_topics],
            'favorite_authors': profile.get('favorite_authors', []) if profile else []
        }