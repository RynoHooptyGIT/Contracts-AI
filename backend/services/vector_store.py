import faiss
import numpy as np
from pathlib import Path
from typing import List, Tuple
import os

class FAISSVectorStore:
    def __init__(self, dimension: int = 384, index_path: str = None):
        self.dimension = dimension
        if index_path is None:
            index_path = os.getenv("FAISS_INDEX_PATH", "/app/data/faiss_index")
        self.index_path = Path(index_path)
        self.index_path.mkdir(parents=True, exist_ok=True)

        index_file = self.index_path / "index.faiss"
        if index_file.exists():
            self.index = faiss.read_index(str(index_file))
        else:
            self.index = faiss.IndexFlatL2(dimension)

    def add_vectors(self, embeddings: np.ndarray) -> List[int]:
        """Add vectors to index, return IDs"""
        start_id = self.index.ntotal
        self.index.add(embeddings.astype('float32'))
        return list(range(start_id, self.index.ntotal))

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Tuple[int, float]]:
        """Search for top-K similar vectors"""
        query = query_embedding.reshape(1, -1).astype('float32')
        distances, indices = self.index.search(query, top_k)
        return [(int(idx), float(dist)) for idx, dist in zip(indices[0], distances[0])]

    def save(self):
        """Save index to disk"""
        faiss.write_index(self.index, str(self.index_path / "index.faiss"))

    def load(self):
        """Load index from disk"""
        index_file = self.index_path / "index.faiss"
        if index_file.exists():
            self.index = faiss.read_index(str(index_file))
