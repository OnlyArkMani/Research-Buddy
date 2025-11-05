import faiss
import numpy as np
import pickle
from pathlib import Path

class FAISSVectorStore:
    def __init__(self, dimension: int = 384, cache_path: str = "cache/faiss_index"):
        """Initialize FAISS index"""
        self.dimension = dimension
        self.cache_path = Path(cache_path)
        self.cache_path.mkdir(parents=True, exist_ok=True)
        
        # Create index
        self.index = faiss.IndexFlatL2(dimension)
        self.metadata = []
        
        self._load_cache()
    
    def add(self, embeddings: np.ndarray, metadata: list):
        """Add embeddings to index"""
        self.index.add(embeddings.astype('float32'))
        self.metadata.extend(metadata)
        self._save_cache()
    
    def search(self, query_embedding: np.ndarray, k: int = 10):
        """Search for similar embeddings"""
        query_embedding = query_embedding.reshape(1, -1).astype('float32')
        distances, indices = self.index.search(query_embedding, k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.metadata):
                results.append({
                    'metadata': self.metadata[idx],
                    'distance': float(distances[0][i]),
                    'similarity': 1 / (1 + float(distances[0][i]))
                })
        
        return results
    
    def _save_cache(self):
        """Save index and metadata"""
        faiss.write_index(self.index, str(self.cache_path / "index.faiss"))
        with open(self.cache_path / "metadata.pkl", 'wb') as f:
            pickle.dump(self.metadata, f)
    
    def _load_cache(self):
        """Load cached index"""
        index_path = self.cache_path / "index.faiss"
        metadata_path = self.cache_path / "metadata.pkl"
        
        if index_path.exists() and metadata_path.exists():
            self.index = faiss.read_index(str(index_path))
            with open(metadata_path, 'rb') as f:
                self.metadata = pickle.load(f)