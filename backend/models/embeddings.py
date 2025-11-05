from sentence_transformers import SentenceTransformer
import numpy as np

class EmbeddingModel:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """Initialize lightweight embedding model (~80MB)"""
        self.model = SentenceTransformer(model_name)
        
    def encode(self, texts: list[str]) -> np.ndarray:
        """Generate embeddings for texts"""
        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False
        )
        return embeddings
    
    def encode_single(self, text: str) -> np.ndarray:
        """Generate embedding for single text"""
        return self.encode([text])[0]