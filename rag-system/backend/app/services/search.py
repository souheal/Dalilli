import logging
from typing import List, Dict, Any, Optional
import numpy as np

from app.services.embeddings import EmbeddingService
from app.services.vector_store import vector_store
from app.services.bm25_cache import bm25_cache, tokenize

logger = logging.getLogger(__name__)

# Candidate set caps — limit how many results each retriever produces
# before fusion. Keeps fusion cost constant regardless of corpus size.
SEMANTIC_CANDIDATE_FACTOR = 10
SEMANTIC_CANDIDATE_MAX = 200
BM25_CANDIDATE_FACTOR = 20
BM25_CANDIDATE_MAX = 300


class HybridSearchService:
    """Hybrid search combining BM25 and semantic search"""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        bm25_weight: float = 0.3,
        semantic_weight: float = 0.7
    ):
        self.embedding_service = embedding_service
        self.bm25_weight = bm25_weight
        self.semantic_weight = semantic_weight

    def search(
        self,
        query: str,
        collection: str = "default",
        top_k: int = 5,
        boost_doc_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining BM25 and semantic search

        Args:
            query: Search query
            collection: Collection name
            top_k: Number of results to return
            boost_doc_ids: Optional list of doc_ids to boost (source anchoring for follow-ups)

        Returns:
            List of results with text, metadata, and scores
        """
        # Get cached BM25 index (built once, reused across queries)
        cache_entry = bm25_cache.get_index(collection, vector_store)

        if not cache_entry:
            return []

        # Cap candidate sets to avoid O(n) fusion on large corpora
        corpus_size = len(cache_entry.documents)
        semantic_k = min(top_k * SEMANTIC_CANDIDATE_FACTOR, SEMANTIC_CANDIDATE_MAX, corpus_size)
        bm25_k = min(top_k * BM25_CANDIDATE_FACTOR, BM25_CANDIDATE_MAX, corpus_size)
        logger.debug("Hybrid search candidates: semantic_k=%d, bm25_k=%d (corpus=%d, top_k=%d)",
                      semantic_k, bm25_k, corpus_size, top_k)

        # Semantic search
        query_embedding = self.embedding_service.embed_query(query)
        semantic_results = vector_store.search(collection, query_embedding, top_k=semantic_k)

        # BM25 search using cached index
        bm25_results = self._bm25_search(query, cache_entry, top_k=bm25_k)

        # Combine results using reciprocal rank fusion
        combined_results = self._combine_results(
            semantic_results,
            bm25_results,
            self.semantic_weight,
            self.bm25_weight
        )

        # Apply source anchoring boost for follow-up queries
        if boost_doc_ids:
            boost_set = set(boost_doc_ids)
            for result in combined_results:
                if result["metadata"].get("doc_id") in boost_set:
                    result["score"] *= 1.2

        # Sort by combined score and return top_k
        combined_results.sort(key=lambda x: x["score"], reverse=True)
        return combined_results[:top_k]

    def _bm25_search(
        self,
        query: str,
        cache_entry,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Perform BM25 keyword search using the cached index."""
        # Tokenize query with the same tokenizer used at index time
        tokenized_query = tokenize(query)

        # Score against the cached index (always scores full corpus — this is fast on the cached index)
        scores = cache_entry.bm25_index.get_scores(tokenized_query)

        # Normalize scores to 0-1 range
        if max(scores) > 0:
            scores = scores / max(scores)

        # Create results
        results = []
        for i, (doc, score) in enumerate(zip(cache_entry.documents, scores)):
            results.append({
                "text": doc["text"],
                "metadata": doc["metadata"],
                "score": float(score),
                "id": doc.get("id", str(i))
            })

        # Sort by score and return capped candidates
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def _combine_results(
        self,
        semantic_results: List[Dict[str, Any]],
        bm25_results: List[Dict[str, Any]],
        semantic_weight: float,
        bm25_weight: float
    ) -> List[Dict[str, Any]]:
        """
        Combine semantic and BM25 results using weighted reciprocal rank fusion
        """
        # Create score maps
        semantic_scores = {}
        bm25_scores = {}

        for i, result in enumerate(semantic_results):
            key = result["text"][:100]  # Use text prefix as key
            semantic_scores[key] = {
                "rank": i + 1,
                "score": result["score"],
                "data": result
            }

        for i, result in enumerate(bm25_results):
            key = result["text"][:100]
            bm25_scores[key] = {
                "rank": i + 1,
                "score": result["score"],
                "data": result
            }

        # Combine scores
        all_keys = set(semantic_scores.keys()) | set(bm25_scores.keys())
        combined = []

        k = 60  # RRF constant

        for key in all_keys:
            # Calculate RRF score
            semantic_rrf = 0
            bm25_rrf = 0

            if key in semantic_scores:
                semantic_rrf = 1 / (k + semantic_scores[key]["rank"])
                data = semantic_scores[key]["data"]
            if key in bm25_scores:
                bm25_rrf = 1 / (k + bm25_scores[key]["rank"])
                data = bm25_scores[key]["data"]

            # Weighted combination
            combined_score = (semantic_weight * semantic_rrf) + (bm25_weight * bm25_rrf)

            # Also consider the raw scores
            raw_semantic = semantic_scores[key]["score"] if key in semantic_scores else 0
            raw_bm25 = bm25_scores[key]["score"] if key in bm25_scores else 0
            raw_combined = (semantic_weight * raw_semantic) + (bm25_weight * raw_bm25)

            # Final score is average of RRF and raw combined
            final_score = (combined_score * 100 + raw_combined) / 2

            combined.append({
                "text": data["text"],
                "metadata": data["metadata"],
                "score": final_score
            })

        return combined
