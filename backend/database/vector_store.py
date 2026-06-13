import faiss
import numpy as np
import pickle
from pathlib import Path


class FAISSVectorStore:
    def __init__(self, dimension: int = 384, cache_path: str = "cache/faiss_index"):
        """Initialize FAISS index with id-based deduplication.

        Previously every search() re-embedded its results and add()-ed them to
        the same index with no dedup, so the store accumulated duplicate vectors
        across sessions and semantic-search quality decayed over time. We now
        track seen paper ids and skip anything already indexed.
        """
        self.dimension = dimension
        self.cache_path = Path(cache_path)
        self.cache_path.mkdir(parents=True, exist_ok=True)

        # Create index
        self.index = faiss.IndexFlatL2(dimension)
        self.metadata = []
        # Set of paper ids already present in the index, for dedup on insert.
        self._seen_ids = set()

        self._load_cache()

    @staticmethod
    def _key(item: dict) -> str:
        """Stable dedup key for a paper. Falls back to title if no id."""
        return str(item.get('id') or item.get('paper_id') or item.get('title') or '')

    def add(self, embeddings: np.ndarray, metadata: list):
        """Add embeddings to the index, skipping papers already indexed.

        embeddings[i] must correspond to metadata[i]. Returns the number of
        new (non-duplicate) vectors actually added.
        """
        embeddings = np.asarray(embeddings, dtype='float32')
        if embeddings.ndim == 1:
            embeddings = embeddings.reshape(1, -1)

        new_vectors = []
        new_metadata = []
        for vec, item in zip(embeddings, metadata):
            key = self._key(item)
            if key and key in self._seen_ids:
                continue  # already indexed — skip duplicate
            if key:
                self._seen_ids.add(key)
            new_vectors.append(vec)
            new_metadata.append(item)

        if not new_vectors:
            return 0

        self.index.add(np.asarray(new_vectors, dtype='float32'))
        self.metadata.extend(new_metadata)
        self._save_cache()
        return len(new_vectors)

    def search(self, query_embedding: np.ndarray, k: int = 10):
        """Search for similar embeddings."""
        if self.index.ntotal == 0:
            return []
        query_embedding = np.asarray(query_embedding, dtype='float32').reshape(1, -1)
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_embedding, k)

        results = []
        for i, idx in enumerate(indices[0]):
            if 0 <= idx < len(self.metadata):
                results.append({
                    'metadata': self.metadata[idx],
                    'distance': float(distances[0][i]),
                    'similarity': 1 / (1 + float(distances[0][i]))
                })

        return results

    def _save_cache(self):
        """Save index and metadata."""
        faiss.write_index(self.index, str(self.cache_path / "index.faiss"))
        with open(self.cache_path / "metadata.pkl", 'wb') as f:
            pickle.dump(self.metadata, f)

    def _load_cache(self):
        """Load cached index and rebuild the dedup set."""
        index_path = self.cache_path / "index.faiss"
        metadata_path = self.cache_path / "metadata.pkl"

        if index_path.exists() and metadata_path.exists():
            self.index = faiss.read_index(str(index_path))
            with open(metadata_path, 'rb') as f:
                self.metadata = pickle.load(f)
            self._seen_ids = {self._key(m) for m in self.metadata if self._key(m)}
