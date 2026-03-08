from typing import List
import os
import numpy as np
from sentence_transformers import SentenceTransformer
from app.config import settings


class EmbeddingService:
    """Service for generating text embeddings"""

    _model_cache = {}

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = self._get_model(model_name)

    @classmethod
    def _resolve_model_path(cls, model_name: str) -> str:
        """Resolve model name to local path if available"""
        if model_name in settings.local_model_paths:
            local_path = settings.local_model_paths[model_name]
            if os.path.exists(local_path):
                print(f"Using local model from: {local_path}")
                return local_path
            else:
                print(f"Local path not found: {local_path}, falling back to download")
        return model_name

    @classmethod
    def _get_model(cls, model_name: str) -> SentenceTransformer:
        """Get or load a model from cache"""
        if model_name not in cls._model_cache:
            model_path = cls._resolve_model_path(model_name)
            print(f"Loading embedding model: {model_name}")
            cls._model_cache[model_name] = SentenceTransformer(model_path)
        return cls._model_cache[model_name]

    def embed_query(self, query: str) -> List[float]:
        """Generate embedding for a query"""
        # Add instruction prefix for specific models
        if "bge" in self.model_name.lower():
            query = f"Represent this sentence for searching relevant passages: {query}"
        elif "e5" in self.model_name.lower():
            query = f"query: {query}"

        embedding = self.model.encode(query, convert_to_numpy=True)
        return embedding.tolist()

    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of documents"""
        # Add instruction prefix for E5 models
        if "e5" in self.model_name.lower():
            documents = [f"passage: {doc}" for doc in documents]

        embeddings = self.model.encode(documents, convert_to_numpy=True, show_progress_bar=True)
        return embeddings.tolist()

    def compute_similarity(self, query_embedding: List[float], doc_embeddings: List[List[float]]) -> List[float]:
        """Compute cosine similarity between query and documents"""
        query_np = np.array(query_embedding)
        docs_np = np.array(doc_embeddings)

        # Normalize
        query_norm = query_np / np.linalg.norm(query_np)
        docs_norm = docs_np / np.linalg.norm(docs_np, axis=1, keepdims=True)

        # Cosine similarity
        similarities = np.dot(docs_norm, query_norm)
        return similarities.tolist()
