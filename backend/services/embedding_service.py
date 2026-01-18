from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List

class EmbeddingService:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._model = SentenceTransformer('all-MiniLM-L6-v2')
        return cls._instance

    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for multiple texts (batch)"""
        return self._model.encode(texts, convert_to_numpy=True)

    def generate_query_embedding(self, query: str) -> np.ndarray:
        """Generate embedding for single query"""
        return self._model.encode([query], convert_to_numpy=True)[0]
